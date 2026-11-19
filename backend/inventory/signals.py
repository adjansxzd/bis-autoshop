from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import MAIN_WAREHOUSE_NAME  # noqa: F401  (kept for old imports)
from .models import StockMovement, Warehouse, WarehouseStock


@receiver(post_save, sender="catalog.Product")
def create_default_warehouse_stock(sender, instance, created, raw=False, **kwargs):
    """Every new product gets a row in Main warehouse.

    If the product was created with a non-zero stock, that opening balance is
    written to the journal as an adjustment, so balance == sum of movements.
    """
    if not created or raw:
        return

    warehouse, _ = Warehouse.objects.get_or_create(name=MAIN_WAREHOUSE_NAME)
    stock, stock_created = WarehouseStock.objects.get_or_create(
        warehouse=warehouse,
        product_id=instance.pk,
        defaults={"quantity": instance.stock},
    )
    if stock_created and stock.quantity > 0:
        StockMovement.objects.create(
            movement_type=StockMovement.Type.ADJUSTMENT,
            warehouse=warehouse,
            product_id=instance.pk,
            quantity=stock.quantity,
        )
