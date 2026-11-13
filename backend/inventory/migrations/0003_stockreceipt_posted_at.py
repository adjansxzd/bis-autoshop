from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_seed_default_warehouse_stock"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockreceipt",
            name="posted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]