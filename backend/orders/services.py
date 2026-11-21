"""Order operations shared by the API, the admin and the seed commands."""
from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.services import get_main_warehouse, issue_stock_for_order, return_stock_for_order

from decimal import Decimal

from django.utils import timezone

from .models import Order, OrderEvent, OrderItem

# --- delivery rules (shown to customers via GET /api/orders/delivery-options/) ---
COURIER_PRICE = Decimal("1500")
FREE_DELIVERY_FROM = Decimal("50000")   # courier is free for orders from 50 000 ₸
PICKUP_ADDRESS = "AutoShop, Almaty, Abylai Khan Ave 1 (Mon–Sat 9:00–20:00)"


def delivery_cost(method, items_total):
    if method == Order.Delivery.PICKUP:
        return Decimal("0")
    return Decimal("0") if items_total >= FREE_DELIVERY_FROM else COURIER_PRICE


def log_event(order, status, user=None, note=""):
    OrderEvent.objects.create(order=order, status=status, by=user if user and user.is_authenticated else None, note=note)

# Normal flow goes forward only: new -> paid -> shipped -> delivered (steps may be skipped).
STATUS_FLOW = [Order.Status.NEW, Order.Status.PAID, Order.Status.SHIPPED, Order.Status.DELIVERED]
# Stock is returned on cancel, so cancelling is only allowed before the goods leave the warehouse.
CANCELLABLE_STATUSES = {Order.Status.NEW, Order.Status.PAID}


def validate_status_transition(current, new):
    if current == new:
        return
    if current == Order.Status.CANCELLED:
        raise ValidationError("A cancelled order cannot be reopened.")
    if new == Order.Status.CANCELLED:
        if current not in CANCELLABLE_STATUSES:
            raise ValidationError(f"An order in status '{current}' cannot be cancelled.")
        return
    if STATUS_FLOW.index(new) < STATUS_FLOW.index(current):
        raise ValidationError(f"Order status cannot go back from '{current}' to '{new}'.")


@transaction.atomic
def change_order_status(order, new_status, user, note=""):
    """Validate and apply a status change; returns stock to the warehouse on cancel.
    Every change is written to the order's history (OrderEvent) for the timeline."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    validate_status_transition(order.status, new_status)
    if order.status == new_status:
        return order
    if new_status == Order.Status.CANCELLED:
        return_stock_for_order(order, user)
    order.status = new_status
    fields = ["status"]
    if new_status == Order.Status.PAID and order.paid_at is None:
        order.paid_at = timezone.now()
        fields.append("paid_at")
    order.save(update_fields=fields)
    log_event(order, new_status, user, note)
    return order


@transaction.atomic
def pay_order(order, user):
    """Demo online payment: no card data is collected, the order just becomes 'paid'."""
    if order.user_id != user.id:
        raise ValidationError("You can pay only for your own order.")
    if order.payment_method != Order.Payment.CARD:
        raise ValidationError("This order is paid on delivery.")
    if order.status != Order.Status.NEW:
        raise ValidationError("Only a new, unpaid order can be paid.")
    return change_order_status(order, Order.Status.PAID, user, note="Paid online (demo payment, no real money)")


@transaction.atomic
def cancel_by_customer(order, user, reason=""):
    """A customer cancels their own order while it is new or paid; items go back to the warehouse."""
    if order.user_id != user.id:
        raise ValidationError("You can cancel only your own order.")
    note = f"Cancelled by customer{': ' + reason.strip() if reason.strip() else ''}"
    if order.status == Order.Status.PAID and order.payment_method == Order.Payment.CARD:
        note += " · refund issued (demo)"
    return change_order_status(order, Order.Status.CANCELLED, user, note=note[:255])


@transaction.atomic
def place_order(user, lines, shipping_address, phone, delivery_method=Order.Delivery.COURIER,
                payment_method=Order.Payment.CASH, comment=""):
    """Create an order from [(product, quantity), ...] and write off stock from Main warehouse.
    Delivery: courier (1 500 ₸, free from 50 000 ₸) or pickup (free, shop address is used).

    Raises django ValidationError (InsufficientStockError for a shortage); nothing is saved then.
    """
    merged = {}
    for product, quantity in lines:
        if product.pk in merged:
            merged[product.pk] = (product, merged[product.pk][1] + quantity)
        else:
            merged[product.pk] = (product, quantity)
    if not merged:
        raise ValidationError("Cart is empty.")

    warehouse = get_main_warehouse()
    if warehouse is None:
        raise ValidationError("Main warehouse is not configured.")

    if delivery_method == Order.Delivery.PICKUP:
        shipping_address = PICKUP_ADDRESS
    order = Order.objects.create(
        user=user, shipping_address=shipping_address, phone=phone,
        delivery_method=delivery_method, payment_method=payment_method, comment=comment,
    )
    total = 0
    for product, quantity in merged.values():
        OrderItem.objects.create(
            order=order, product=product, warehouse=warehouse, quantity=quantity, unit_price=product.price
        )
        total += product.price * quantity
    issue_stock_for_order(order, user)
    order.items_total = total
    order.delivery_cost = delivery_cost(delivery_method, total)
    order.total = order.items_total + order.delivery_cost
    order.save(update_fields=["items_total", "delivery_cost", "total"])
    log_event(order, Order.Status.NEW, user, note="Order placed")
    return order
