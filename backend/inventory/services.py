from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from catalog.models import Product

from .models import StockMovement, StockReceipt, StockReceiptItem, Warehouse, WarehouseStock
from .signals import MAIN_WAREHOUSE_NAME


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


@transaction.atomic
def receive_stock(receipt, user):
    receipt = StockReceipt.objects.select_for_update().get(pk=receipt.pk)
    if receipt.posted_at is not None:
        return False

    items = list(StockReceiptItem.objects.select_for_update().filter(receipt=receipt).order_by("pk"))
    if not items:
        raise ValidationError("Cannot post an empty stock receipt.")

    warehouse = Warehouse.objects.select_for_update().get(pk=receipt.warehouse_id)
    for item in items:
        stock, _ = WarehouseStock.objects.select_for_update().get_or_create(
            warehouse=warehouse,
            product_id=item.product_id,
            defaults={"quantity": 0},
        )
        stock.quantity += item.quantity
        stock.save(update_fields=["quantity", "updated_at"])
        StockMovement.objects.create(
            movement_type=StockMovement.Type.RECEIPT,
            warehouse=warehouse,
            product_id=item.product_id,
            quantity=item.quantity,
            receipt=receipt,
            user=user,
        )
        sync_product_stock(item.product_id)

    receipt.posted_at = timezone.now()
    receipt.save(update_fields=["posted_at"])
    return True