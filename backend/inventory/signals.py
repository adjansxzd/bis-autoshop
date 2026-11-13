from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Warehouse, WarehouseStock

MAIN_WAREHOUSE_NAME = "Main warehouse"


@receiver(post_save, sender="catalog.Product")
def create_default_warehouse_stock(sender, instance, created, raw=False, **kwargs):
    if not created or raw:
        return

    warehouse, _ = Warehouse.objects.get_or_create(name=MAIN_WAREHOUSE_NAME)
    WarehouseStock.objects.get_or_create(
        warehouse=warehouse,
        product_id=instance.pk,
        defaults={"quantity": instance.stock},
    )