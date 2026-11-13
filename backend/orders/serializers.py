from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductSerializer
from inventory.services import get_available_stock

from .models import Cart, CartItem, Order, OrderItem


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
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate(self, attrs):
        product = attrs.get("product") or getattr(self.instance, "product", None)
        if product is None:
            return attrs

        quantity = attrs.get("quantity", getattr(self.instance, "quantity", 1))
        current_quantity = 0
        request = self.context.get("request")
        if self.instance is None and request and request.user.is_authenticated:
            current_quantity = (
                CartItem.objects.filter(cart__user=request.user, product=product)
                .values_list("quantity", flat=True)
                .first()
                or 0
            )

        available = get_available_stock(product)
        if current_quantity + quantity > available:
            raise serializers.ValidationError({"quantity": f"Only {available} in stock."})
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


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "status", "shipping_address", "phone", "total", "items", "created_at"]
        read_only_fields = ["status", "total", "created_at"]


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]
