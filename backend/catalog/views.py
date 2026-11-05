from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.permissions import IsStaffRoleOrReadOnly

from .filters import ProductFilter
from .models import Brand, CarModel, Category, Product
from .serializers import BrandSerializer, CarModelSerializer, CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsStaffRoleOrReadOnly]
    pagination_class = None
    lookup_field = "slug"
    search_fields = ["name_en", "name_ru"]

    def get_queryset(self):
        return Category.objects.annotate(product_count=Count("products", filter=Q(products__is_active=True)))


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsStaffRoleOrReadOnly]
    pagination_class = None
    search_fields = ["name"]


class CarModelViewSet(viewsets.ModelViewSet):
    queryset = CarModel.objects.all()
    serializer_class = CarModelSerializer
    permission_classes = [IsStaffRoleOrReadOnly]
    pagination_class = None
    filterset_fields = ["make"]
    search_fields = ["make", "model"]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsStaffRoleOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ["name_en", "name_ru", "sku", "brand__name", "description_en", "description_ru"]
    ordering_fields = ["price", "created_at", "name_en"]

    def get_queryset(self):
        qs = Product.objects.select_related("category", "brand").prefetch_related("compatible_cars").distinct()
        user = self.request.user
        # Customers only see active products; staff see everything (for the admin panel)
        if not (user.is_authenticated and (user.is_staff_role or user.is_superuser)):
            qs = qs.filter(is_active=True)
        return qs


@extend_schema(
    parameters=[OpenApiParameter("q", str, description="Search text, min 2 characters")],
    responses=inline_serializer("SearchResult", {
        "query": serializers.CharField(),
        "products": ProductSerializer(many=True),
        "categories": CategorySerializer(many=True),
        "cars": CarModelSerializer(many=True),
    }),
)
@api_view(["GET"])
@permission_classes([AllowAny])
def global_search(request):
    """GET /api/search/?q=brake — searches 3 entity types at once: products, categories, car models."""
    q = request.query_params.get("q", "").strip()
    if len(q) < 2:
        return Response({"query": q, "products": [], "categories": [], "cars": []})

    products = Product.objects.filter(is_active=True).filter(
        Q(name_en__icontains=q) | Q(name_ru__icontains=q) | Q(sku__icontains=q) | Q(brand__name__icontains=q)
    ).select_related("category", "brand").prefetch_related("compatible_cars").distinct()[:10]
    categories = Category.objects.filter(Q(name_en__icontains=q) | Q(name_ru__icontains=q))[:5]
    cars = CarModel.objects.filter(Q(make__icontains=q) | Q(model__icontains=q))[:5]

    return Response({
        "query": q,
        "products": ProductSerializer(products, many=True).data,
        "categories": CategorySerializer(categories, many=True).data,
        "cars": CarModelSerializer(cars, many=True).data,
    })
