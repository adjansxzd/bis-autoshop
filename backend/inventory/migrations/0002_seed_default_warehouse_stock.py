from django.db import migrations


def seed_default_warehouse_stock(apps, schema_editor):
    Warehouse = apps.get_model("inventory", "Warehouse")
    WarehouseStock = apps.get_model("inventory", "WarehouseStock")
    Product = apps.get_model("catalog", "Product")
    database = schema_editor.connection.alias

    warehouse, _ = Warehouse.objects.using(database).get_or_create(
        name="Main warehouse",
        defaults={"address": "", "is_active": True},
    )
    for product in Product.objects.using(database).all().iterator():
        WarehouseStock.objects.using(database).get_or_create(
            warehouse_id=warehouse.pk,
            product_id=product.pk,
            defaults={"quantity": product.stock},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_default_warehouse_stock, migrations.RunPython.noop),
    ]