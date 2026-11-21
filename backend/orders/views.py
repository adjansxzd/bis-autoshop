from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer

from accounts.permissions import IsStaffRole
from inventory.services import get_available_stock

from .models import Cart, CartItem, Order
from .serializers import (
    CancelSerializer, CartItemSerializer, CartSerializer, CheckoutSerializer, OrderSerializer, OrderStatusSerializer,
)
from .services import (
    COURIER_PRICE, FREE_DELIVERY_FROM, PICKUP_ADDRESS, cancel_by_customer, change_order_status, pay_order, place_order,
)


def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    """GET /api/cart/ — current user's cart.  DELETE /api/cart/ — empty the cart."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CartSerializer)
    def get(self, request):
        return Response(CartSerializer(get_cart(request.user)).data)

    @extend_schema(responses={204: None})
    def delete(self, request):
        get_cart(request.user).items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CartItemViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    POST   /api/cart/items/        {product_id, quantity}  — add (or increase) a product
    PATCH  /api/cart/items/{id}/   {quantity}              — change quantity
    DELETE /api/cart/items/{id}/                           — remove from cart
    """

    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # schema generation
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)
        item, created = CartItem.objects.get_or_create(cart=get_cart(request.user), product=product, defaults={"quantity": 0})
        item.quantity += quantity
        available = get_available_stock(product)
        if item.quantity > available:
            raise ValidationError({"quantity": f"Only {available} in stock."})
        item.save()
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET  /api/orders/?q=&status=     — my orders (staff see all), search by number / product / SKU, filter by status
    POST /api/orders/checkout/       {shipping_address, phone} — turn the cart into an order
    PATCH /api/orders/{id}/status/   {status} — staff only
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status"]

    def get_queryset(self):
        qs = Order.objects.prefetch_related("items__product", "events").select_related("user")
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        user = self.request.user
        if not (user.is_staff_role or user.is_superuser):
            qs = qs.filter(user=user)
        # ?q= search in "My orders": order number (12 or #12), product name, SKU or address
        q = self.request.query_params.get("q", "").strip()
        if q:
            match = (
                Q(items__product__name_en__icontains=q) | Q(items__product__name_ru__icontains=q)
                | Q(items__product__sku__icontains=q) | Q(shipping_address__icontains=q)
            )
            if q.lstrip("#").isdigit():
                match |= Q(pk=int(q.lstrip("#")))
            qs = qs.filter(match).distinct()
        return qs

    @extend_schema(request=CheckoutSerializer, responses=OrderSerializer)
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def checkout(self, request):
        """Cart → order. Body: {delivery_method: courier|pickup, payment_method: card|cash, shipping_address, phone, comment}"""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        cart = get_cart(request.user)
        items = list(cart.items.select_related("product").select_for_update().order_by("pk"))
        if not items:
            raise ValidationError({"cart": "Cart is empty."})

        try:
            order = place_order(
                request.user,
                [(item.product, item.quantity) for item in items],
                data.get("shipping_address", "").strip(),
                data["phone"],
                delivery_method=data["delivery_method"],
                payment_method=data["payment_method"],
                comment=data.get("comment", "").strip(),
            )
        except DjangoValidationError as error:
            raise ValidationError({"stock": error.messages})
        cart.items.all().delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=inline_serializer("DeliveryOptions", {
        "courier_price": serializers.DecimalField(10, 2), "free_from": serializers.DecimalField(12, 2),
        "pickup_address": serializers.CharField(),
    }))
    @action(detail=False, methods=["get"], url_path="delivery-options", permission_classes=[AllowAny])
    def delivery_options(self, request):
        """Prices shown at checkout (one source of truth with place_order)."""
        return Response({"courier_price": COURIER_PRICE, "free_from": FREE_DELIVERY_FROM, "pickup_address": PICKUP_ADDRESS})

    @extend_schema(request=None, responses=OrderSerializer)
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        """Demo online payment for a 'card' order: status new → paid. No card data is sent or stored."""
        try:
            order = pay_order(self.get_object(), request.user)
        except DjangoValidationError as error:
            raise ValidationError({"detail": error.messages})
        return Response(OrderSerializer(order).data)

    @extend_schema(request=CancelSerializer, responses=OrderSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Customer cancels their own order (only while new or paid). Items go back to the warehouse."""
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = cancel_by_customer(self.get_object(), request.user, serializer.validated_data.get("reason", ""))
        except DjangoValidationError as error:
            raise ValidationError({"detail": error.messages})
        return Response(OrderSerializer(order).data)

    @extend_schema(request=None, responses=inline_serializer("ReorderResult", {
        "added": serializers.ListField(child=serializers.CharField()),
        "skipped": serializers.ListField(child=serializers.CharField()),
    }))
    @action(detail=True, methods=["post"])
    def reorder(self, request, pk=None):
        """'Order again': puts the items of a past order back into the cart (as many as are in stock)."""
        order = self.get_object()
        if order.user_id != request.user.id:
            raise ValidationError({"detail": "You can reorder only your own order."})
        cart = get_cart(request.user)
        added, skipped = [], []
        for line in order.items.select_related("product"):
            product = line.product
            item, _ = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": 0})
            room = get_available_stock(product) - item.quantity
            qty = min(line.quantity, room)
            if not product.is_active or qty <= 0:
                skipped.append(product.name_en)
                if item.quantity == 0:
                    item.delete()
                continue
            item.quantity += qty
            item.save()
            added.append(product.name_en)
        return Response({"added": added, "skipped": skipped})

    @action(detail=True, methods=["patch"], permission_classes=[IsStaffRole])
    def status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusSerializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = change_order_status(order, serializer.validated_data["status"], request.user, note="Changed by the shop")
        except DjangoValidationError as error:
            raise ValidationError({"status": error.messages})
        return Response(OrderSerializer(order).data)
