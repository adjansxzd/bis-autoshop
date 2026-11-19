"""Order operations shared by the API, the admin and the seed commands."""
from django.core.exceptions import ValidationError
from django.db import transaction

from inventory.services import get_main_warehouse, issue_stock_for_order, return_stock_for_order

from .models import Order, OrderItem

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
def change_order_status(order, new_status, user):
    """Validate and apply a status change; returns stock to the warehouse on cancel."""
    order = Order.objects.select_for_update().get(pk=order.pk)
    validate_status_transition(order.status, new_status)
    if order.status == new_status:
        return order
    if new_status == Order.Status.CANCELLED:
        return_stock_for_order(order, user)
    order.status = new_status
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def place_order(user, lines, shipping_address, phone):
    """Create an order from [(product, quantity), ...] and write off stock from Main warehouse.

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

    order = Order.objects.create(user=user, shipping_address=shipping_address, phone=phone)
    total = 0
    for product, quantity in merged.values():
        OrderItem.objects.create(
            order=order, product=product, warehouse=warehouse, quantity=quantity, unit_price=product.price
        )
        total += product.price * quantity
    issue_stock_for_order(order, user)
    order.total = total
    order.save(update_fields=["total"])
    return order
