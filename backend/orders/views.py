from django.db import transaction
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.permissions import IsStaffRole
from inventory.models import StockMovement, Warehouse, WarehouseStock
from inventory.services import get_available_stock, sync_product_stock
from inventory.signals import MAIN_WAREHOUSE_NAME

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
        available = get_available_stock(product)
        if item.quantity > available:
            raise ValidationError({"quantity": f"Only {available} in stock."})
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
        items = list(cart.items.select_related("product").select_for_update().order_by("pk"))
        if not items:
            raise ValidationError({"cart": "Cart is empty."})

        warehouse = Warehouse.objects.select_for_update().filter(name=MAIN_WAREHOUSE_NAME).first()
        if warehouse is None:
            raise ValidationError({"stock": "Main warehouse is not configured."})

        locked_stock = {}
        for item in items:
            stock = WarehouseStock.objects.select_for_update().filter(
                warehouse=warehouse, product_id=item.product_id
            ).first()
            available = stock.quantity if stock else 0
            if item.quantity > available:
                raise ValidationError({
                    "stock": f"Not enough stock for {item.product.name_en}. Available: {available}."
                })
            locked_stock[item.pk] = stock

        order = serializer.save(user=request.user)
        total = 0
        for item in items:
            stock = locked_stock[item.pk]
            stock.quantity -= item.quantity
            stock.save(update_fields=["quantity", "updated_at"])
            OrderItem.objects.create(
                order=order,
                product=item.product,
                warehouse=warehouse,
                quantity=item.quantity,
                unit_price=item.product.price,
            )
            StockMovement.objects.create(
                movement_type=StockMovement.Type.SALE,
                warehouse=warehouse,
                product=item.product,
                quantity=item.quantity,
                order=order,
                user=request.user,
            )
            sync_product_stock(item.product_id)
            total += item.product.price * item.quantity
        order.total = total
        order.save(update_fields=["total"])
        cart.items.all().delete()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], permission_classes=[IsStaffRole])
    @transaction.atomic
    def status(self, request, pk=None):
        order = self.get_object()
        order = self.get_queryset().select_for_update().get(pk=order.pk)
        serializer = OrderStatusSerializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)

        next_status = serializer.validated_data["status"]
        if order.status == Order.Status.CANCELLED and next_status != Order.Status.CANCELLED:
            raise ValidationError({"status": "A cancelled order cannot be reopened."})

        if next_status == Order.Status.CANCELLED and order.status != Order.Status.CANCELLED:
            items = order.items.select_for_update().order_by("pk")
            for item in items:
                if item.warehouse_id is None:
                    warehouse = Warehouse.objects.select_for_update().filter(name=MAIN_WAREHOUSE_NAME).first()
                    if warehouse is None:
                        raise ValidationError({"warehouse": "Main warehouse is not configured."})
                    item.warehouse = warehouse
                    item.save(update_fields=["warehouse"])
                else:
                    warehouse = Warehouse.objects.select_for_update().get(pk=item.warehouse_id)
                stock, _ = WarehouseStock.objects.select_for_update().get_or_create(
                    warehouse=warehouse,
                    product_id=item.product_id,
                    defaults={"quantity": 0},
                )
                stock.quantity += item.quantity
                stock.save(update_fields=["quantity", "updated_at"])
                StockMovement.objects.create(
                    movement_type=StockMovement.Type.RETURN,
                    warehouse=warehouse,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    order=order,
                    user=request.user,
                )
                sync_product_stock(item.product_id)

        serializer.save()
        return Response(OrderSerializer(order).data)
