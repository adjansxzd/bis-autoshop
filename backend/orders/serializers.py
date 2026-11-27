from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductSerializer
from inventory.services import get_available_stock

from .models import Cart, CartItem, Order, OrderEvent, OrderItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        source="product", queryset=Product.objects.filter(is_active=True), write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError(_("Quantity must be at least 1."))
        return value

    def validate(self, attrs):
        """Stock limit: you can never have more of a product in the cart than the shop has."""
        product = attrs.get("product") or getattr(self.instance, "product", None)
        quantity = attrs.get("quantity")
        if product is not None:
            available = get_available_stock(product)
            if available == 0:
                raise serializers.ValidationError({"quantity": _("This product is out of stock.")})
            if self.instance is not None and quantity is not None and quantity > available:
                raise serializers.ValidationError({"quantity": _("Only {available} in stock.").format(available=available)})
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "items", "total", "updated_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name_en", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "subtotal"]


class OrderEventSerializer(serializers.ModelSerializer):
    by = serializers.SerializerMethodField()

    class Meta:
        model = OrderEvent
        fields = ["status", "note", "by", "created_at"]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_by(self, obj):
        # customers see "you" / "shop" — never the manager's username
        if obj.by is None:
            return None
        return "customer" if obj.by_id == obj.order.user_id else "shop"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    events = OrderEventSerializer(many=True, read_only=True)
    customer = serializers.CharField(source="user.username", read_only=True)
    can_pay = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id", "customer", "status", "delivery_method", "payment_method", "shipping_address", "phone", "comment",
            "items_total", "delivery_cost", "total", "paid_at", "items", "events", "can_pay", "can_cancel", "created_at",
        ]
        read_only_fields = ["status", "items_total", "delivery_cost", "total", "paid_at", "created_at"]

    @extend_schema_field(serializers.BooleanField())
    def get_can_pay(self, obj):
        return obj.status == Order.Status.NEW and obj.payment_method in Order.ONLINE_PAYMENTS

    @extend_schema_field(serializers.BooleanField())
    def get_can_cancel(self, obj):
        return obj.status in (Order.Status.NEW, Order.Status.PAID)


class CheckoutSerializer(serializers.Serializer):
    """POST /api/orders/checkout/ — address is required only for courier delivery."""

    delivery_method = serializers.ChoiceField(choices=Order.Delivery.choices, default=Order.Delivery.COURIER)
    payment_method = serializers.ChoiceField(choices=Order.Payment.choices, default=Order.Payment.CASH)
    shipping_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["delivery_method"] == Order.Delivery.COURIER and not attrs.get("shipping_address", "").strip():
            raise serializers.ValidationError({"shipping_address": _("Enter the delivery address.")})
        return attrs


class CancelSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=200, required=False, allow_blank=True)


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]
