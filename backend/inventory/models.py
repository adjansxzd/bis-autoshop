from django.conf import settings
from django.db import models
from django.db.models import Q


class Warehouse(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WarehouseStock(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stocks")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="warehouse_stocks")
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["warehouse", "product"], name="uniq_warehouse_product"),
            models.CheckConstraint(condition=Q(quantity__gte=0), name="stock_qty_nonnegative"),
        ]

    def __str__(self):
        return f"{self.product} at {self.warehouse}: {self.quantity}"


class Supplier(models.Model):
    """A permanent supplier that stock receipts come from."""

    name = models.CharField(max_length=150, unique=True)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class StockReceipt(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="receipts")
    supplier = models.ForeignKey(
        Supplier, null=True, blank=True, on_delete=models.PROTECT, related_name="receipts"
    )
    number = models.CharField(max_length=40, blank=True, help_text="Supplier invoice / document number")
    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["number"], condition=~Q(number=""), name="uniq_receipt_number"),
        ]

    def __str__(self):
        return f"Receipt #{self.pk} at {self.warehouse}"


class StockReceiptItem(models.Model):
    receipt = models.ForeignKey(StockReceipt, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="receipt_items")
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="receipt_item_qty_positive"),
            models.UniqueConstraint(fields=["receipt", "product"], name="uniq_receipt_product"),
        ]

    def __str__(self):
        return f"{self.product}: {self.quantity}"


class StockMovement(models.Model):
    class Type(models.TextChoices):
        RECEIPT = "receipt", "Receipt"
        SALE = "sale", "Sale"
        RETURN = "return", "Return"
        ADJUSTMENT = "adjustment", "Adjustment"

    movement_type = models.CharField(max_length=20, choices=Type.choices)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="movements")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock_movements")
    quantity = models.PositiveIntegerField()
    order = models.ForeignKey(
        "orders.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="stock_movements"
    )
    receipt = models.ForeignKey(
        StockReceipt, null=True, blank=True, on_delete=models.SET_NULL, related_name="stock_movements"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="stock_movements"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="stock_move_qty_positive"),
            # At most one sale and one return per product per order: blocks double write-off / double return.
            models.UniqueConstraint(
                fields=["order", "product", "movement_type"],
                condition=Q(movement_type__in=["sale", "return"]),
                name="uniq_order_product_movement",
            ),
        ]
        indexes = [
            models.Index(fields=["product", "warehouse", "created_at"], name="move_prod_wh_created_idx"),
            models.Index(fields=["created_at"], name="move_created_idx"),
        ]

    def __str__(self):
        return f"{self.movement_type}: {self.product} x {self.quantity}"