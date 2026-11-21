from django.conf import settings
from django.db import models

from catalog.models import Product


class Cart(models.Model):
    """One active cart per user."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart")
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.select_related("product"))

    def __str__(self):
        return f"Cart of {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    class Delivery(models.TextChoices):
        COURIER = "courier", "Courier delivery"
        PICKUP = "pickup", "Pickup from the shop"

    class Payment(models.TextChoices):
        CARD = "card", "Card online (demo)"
        CASH = "cash", "Cash or card on delivery"

    class Status(models.TextChoices):
        NEW = "new", "New"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    shipping_address = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    delivery_method = models.CharField(max_length=20, choices=Delivery.choices, default=Delivery.COURIER)
    payment_method = models.CharField(max_length=20, choices=Payment.choices, default=Payment.CASH)
    comment = models.CharField(max_length=500, blank=True, help_text="Customer's note for the courier / shop")
    items_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # items_total + delivery_cost
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"], name="order_user_created_idx"),
            models.Index(fields=["status", "created_at"], name="order_status_created_idx"),
        ]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
    """Snapshot of a product at order time (price is copied so later price changes don't affect old orders)."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(
        "inventory.Warehouse", null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class OrderEvent(models.Model):
    """Status history of an order (the timeline on the order page): who changed what and when."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]

    def __str__(self):
        return f"#{self.order_id} → {self.status}"
