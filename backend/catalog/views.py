from django.db.models import Count, Max, Min, Q
from django.utils.translation import gettext as _
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from accounts.permissions import IsStaffRoleOrReadOnly

from .filters import ProductFilter
from .models import Brand, CarModel, Category, Product, Review
from .reviews import has_bought, summary, with_ratings
from .serializers import BrandSerializer, CarModelSerializer, CategorySerializer, ProductSerializer, ReviewSerializer


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
    """
    GET /api/products/?category=&brand=&car=&min_price=&max_price=&in_stock=&search=&ordering=
        ordering: price, -price, -created_at, -rating_avg (best rated), -rating_count (most reviewed)
    GET /api/products/price-range/          lowest and highest price (for the price slider)
    GET/POST /api/products/{id}/reviews/    reviews of a product / leave a review (buyers only)
    """

    serializer_class = ProductSerializer
    permission_classes = [IsStaffRoleOrReadOnly]
    filterset_class = ProductFilter
    search_fields = ["name_en", "name_ru", "sku", "oem_numbers", "brand__name", "description_en", "description_ru"]
    ordering_fields = ["price", "created_at", "name_en", "rating_avg", "rating_count"]

    def get_queryset(self):
        qs = Product.objects.select_related("category", "brand").prefetch_related("compatible_cars").distinct()
        user = self.request.user
        # Customers only see active products; staff see everything (for the admin panel)
        if not (user.is_authenticated and (user.is_staff_role or user.is_superuser)):
            qs = qs.filter(is_active=True)
        return with_ratings(qs)

    @extend_schema(
        parameters=[OpenApiParameter("category", str, description="Category slug (optional)")],
        responses=inline_serializer("PriceRange", {"min": serializers.DecimalField(12, 2), "max": serializers.DecimalField(12, 2)}),
    )
    @action(detail=False, methods=["get"], url_path="price-range", permission_classes=[AllowAny])
    def price_range(self, request):
        qs = Product.objects.filter(is_active=True)
        if request.query_params.get("category"):
            qs = qs.filter(category__slug=request.query_params["category"])
        return Response(qs.aggregate(min=Min("price"), max=Max("price")))

    @extend_schema(request=ReviewSerializer, responses=inline_serializer("ProductReviews", {
        "summary": inline_serializer("ReviewSummary", {
            "avg": serializers.FloatField(allow_null=True), "count": serializers.IntegerField(),
            "distribution": serializers.DictField(child=serializers.IntegerField()),
        }),
        "can_review": serializers.BooleanField(),
        "my_review": ReviewSerializer(allow_null=True),
        "results": ReviewSerializer(many=True),
    }))
    @action(detail=True, methods=["get", "post"], permission_classes=[IsAuthenticatedOrReadOnly])
    def reviews(self, request, pk=None):
        product = self.get_object()
        if request.method == "POST":
            if not has_bought(request.user, product):
                raise PermissionDenied("You can review a product only after buying it.")
            if Review.objects.filter(product=product, user=request.user).exists():
                raise ValidationError({"detail": _("You have already reviewed this product. Edit your review instead.")})
            serializer = ReviewSerializer(data=request.data, context={"request": request})
            serializer.is_valid(raise_exception=True)
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        reviews = product.reviews.select_related("user")
        mine = reviews.filter(user=request.user).first() if request.user.is_authenticated else None
        ctx = {"request": request}
        return Response({
            "summary": summary(product),
            "can_review": mine is None and has_bought(request.user, product),
            "my_review": ReviewSerializer(mine, context=ctx).data if mine else None,
            "results": ReviewSerializer(reviews[:50], many=True, context=ctx).data,
        })


class ReviewViewSet(mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """PATCH / DELETE /api/reviews/{id}/ — edit or delete your own review (staff may delete any)."""

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["patch", "delete"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Review.objects.none()
        user = self.request.user
        if self.request.method == "DELETE" and (user.is_staff_role or user.is_superuser):
            return Review.objects.all()
        return Review.objects.filter(user=user)


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
        Q(name_en__icontains=q) | Q(name_ru__icontains=q) | Q(sku__icontains=q) | Q(oem_numbers__icontains=q) | Q(brand__name__icontains=q)
    ).select_related("category", "brand").prefetch_related("compatible_cars").distinct()
    products = with_ratings(products)[:10]
    categories = Category.objects.filter(Q(name_en__icontains=q) | Q(name_ru__icontains=q))[:5]
    cars = CarModel.objects.filter(Q(make__icontains=q) | Q(model__icontains=q))[:5]

    return Response({
        "query": q,
        "products": ProductSerializer(products, many=True, context={"request": request}).data,
        "categories": CategorySerializer(categories, many=True).data,
        "cars": CarModelSerializer(cars, many=True).data,
    })
