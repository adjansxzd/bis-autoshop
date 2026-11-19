"""All stock changes go through this module.

Rules:
- WarehouseStock.quantity is the source of truth; Product.stock is a cached
  sum over all warehouses, refreshed by sync_product_stock().
- Every change of a balance writes a StockMovement row.
- Balances are changed with a single UPDATE ... SET quantity = quantity +/- N,
  and a sale only succeeds if quantity >= N in the same statement. This works
  on SQLite, where select_for_update() does not lock anything.
"""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from catalog.models import Product

from .constants import MAIN_WAREHOUSE_NAME
from .models import StockMovement, StockReceipt, StockReceiptItem, Warehouse, WarehouseStock


class InsufficientStockError(ValidationError):
    def __init__(self, product, available):
        self.product = product
        self.available = available
        super().__init__(f"Not enough stock for {product.name_en}. Available: {available}.")


def get_main_warehouse():
    return Warehouse.objects.filter(name=MAIN_WAREHOUSE_NAME).first()


def get_available_stock(product, warehouse=None):
    warehouse = warehouse or get_main_warehouse()
    if warehouse is None:
        return 0
    return (
        WarehouseStock.objects.filter(warehouse=warehouse, product_id=product.pk)
        .values_list("quantity", flat=True)
        .first()
        or 0
    )


@transaction.atomic
def sync_product_stock(product_id):
    product = Product.objects.select_for_update().get(pk=product_id)
    product.stock = (
        WarehouseStock.objects.filter(product_id=product_id).aggregate(total=Sum("quantity"))["total"] or 0
    )
    product.save(update_fields=["stock"])


def _add_to_balance(warehouse, product_id, quantity):
    """Atomically increase a balance, creating the row if it is missing."""
    WarehouseStock.objects.get_or_create(warehouse=warehouse, product_id=product_id, defaults={"quantity": 0})
    WarehouseStock.objects.filter(warehouse=warehouse, product_id=product_id).update(
        quantity=F("quantity") + quantity, updated_at=timezone.now()
    )


def _take_from_balance(warehouse, product_id, quantity):
    """Atomically decrease a balance. Returns False if there is not enough stock (or no row)."""
    updated = WarehouseStock.objects.filter(
        warehouse=warehouse, product_id=product_id, quantity__gte=quantity
    ).update(quantity=F("quantity") - quantity, updated_at=timezone.now())
    return updated == 1


def _require_main_warehouse():
    warehouse = get_main_warehouse()
    if warehouse is None:
        raise ValidationError("Main warehouse is not configured.")
    return warehouse


@transaction.atomic
def receive_stock(receipt, user):
    """Post a stock receipt. Returns False if it was already posted."""
    receipt = StockReceipt.objects.select_for_update().get(pk=receipt.pk)
    if receipt.posted_at is not None:
        return False

    items = list(StockReceiptItem.objects.filter(receipt=receipt).order_by("pk"))
    if not items:
        raise ValidationError("Cannot post an empty stock receipt.")

    # Mark as posted first: a concurrent second call now updates 0 rows and stops.
    marked = StockReceipt.objects.filter(pk=receipt.pk, posted_at__isnull=True).update(posted_at=timezone.now())
    if not marked:
        return False

    warehouse = receipt.warehouse
    for item in items:
        _add_to_balance(warehouse, item.product_id, item.quantity)
        StockMovement.objects.create(
            movement_type=StockMovement.Type.RECEIPT,
            warehouse=warehouse,
            product_id=item.product_id,
            quantity=item.quantity,
            receipt=receipt,
            user=user,
        )
        sync_product_stock(item.product_id)
    return True


@transaction.atomic
def issue_stock_for_order(order, user):
    """Write off stock for every item of a new order (sale).

    Raises InsufficientStockError if any item is short; the whole transaction
    (including the order) is rolled back by the caller's atomic block.
    Returns False if the order already has sale movements.
    """
    if order.stock_movements.filter(movement_type=StockMovement.Type.SALE).exists():
        return False

    for item in order.items.select_related("product").order_by("pk"):
        if item.warehouse_id is None:
            item.warehouse = _require_main_warehouse()
            item.save(update_fields=["warehouse"])
        if not _take_from_balance(item.warehouse, item.product_id, item.quantity):
            raise InsufficientStockError(item.product, get_available_stock(item.product, item.warehouse))
        StockMovement.objects.create(
            movement_type=StockMovement.Type.SALE,
            warehouse=item.warehouse,
            product_id=item.product_id,
            quantity=item.quantity,
            order=order,
            user=user,
        )
        sync_product_stock(item.product_id)
    return True


@transaction.atomic
def return_stock_for_order(order, user):
    """Put the stock of a cancelled order back. Returns False if it was already returned."""
    if order.stock_movements.filter(movement_type=StockMovement.Type.RETURN).exists():
        return False

    for item in order.items.order_by("pk"):
        if item.warehouse_id is None:
            item.warehouse = _require_main_warehouse()
            item.save(update_fields=["warehouse"])
        _add_to_balance(item.warehouse, item.product_id, item.quantity)
        StockMovement.objects.create(
            movement_type=StockMovement.Type.RETURN,
            warehouse=item.warehouse,
            product_id=item.product_id,
            quantity=item.quantity,
            order=order,
            user=user,
        )
        sync_product_stock(item.product_id)
    return True
