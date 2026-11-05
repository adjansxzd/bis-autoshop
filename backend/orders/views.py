from django.db import transaction
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsStaffRole

from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartItemSerializer, CartSerializer, OrderSerializer, OrderStatusSerializer


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
        if item.quantity > product.stock:
            raise ValidationError({"quantity": f"Only {product.stock} in stock."})
        item.save()
        return Response(self.get_serializer(item).data, status=status.HTTP_201_CREATED)


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    GET  /api/orders/                — my orders (staff see all orders)
    POST /api/orders/checkout/       {shipping_address, phone} — turn the cart into an order
    PATCH /api/orders/{id}/status/   {status} — staff only
    """

    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status"]

    def get_queryset(self):
        qs = Order.objects.prefetch_related("items__product").select_related("user")
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        user = self.request.user
        if user.is_staff_role or user.is_superuser:
            return qs
        return qs.filter(user=user)

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def checkout(self, request):
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = get_cart(request.user)
        items = list(cart.items.select_related("product").select_for_update())
        if not items:
            raise ValidationError({"cart": "Cart is empty."})

        for item in items:
            if item.quantity > item.product.stock:
                raise ValidationError({"stock": f"Not enough stock for {item.product.name_en}."})

        order = serializer.save(user=request.user)
        total = 0
        for item in items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, unit_price=item.product.price)
            item.product.stock -= item.quantity
            item.product.save(update_fields=["stock"])
            total += item.product.price * item.quantity
        order.total = total
        order.save(update_fields=["total"])
        cart.items.all().delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], permission_classes=[IsStaffRole])
    def status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusSerializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)
