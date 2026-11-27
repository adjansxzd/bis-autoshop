from django.db import models
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Brand, CarModel, Category, Product, Review


class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name_en", "name_ru", "slug", "parent", "icon", "product_count"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "country"]


class CarModelSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="__str__", read_only=True)

    class Meta:
        model = CarModel
        fields = ["id", "make", "model", "year_from", "year_to", "label"]


class ProductSerializer(serializers.ModelSerializer):
    """Read: nested category/brand/cars for display. Write: send ids (category_id, brand_id, compatible_car_ids)."""

    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    compatible_cars = CarModelSerializer(many=True, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)
    # filled by ProductViewSet's queryset annotations (average stars and number of reviews)
    rating_avg = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()

    category_id = serializers.PrimaryKeyRelatedField(source="category", queryset=Category.objects.all(), write_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(source="brand", queryset=Brand.objects.all(), write_only=True)
    compatible_car_ids = serializers.PrimaryKeyRelatedField(
        source="compatible_cars", queryset=CarModel.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name_en", "name_ru", "description_en", "description_ru",
            "price", "stock", "in_stock", "image", "image_url", "model_3d", "oem_numbers", "specs",
            "rating_avg", "rating_count", "is_active",
            "category", "brand", "compatible_cars",
            "category_id", "brand_id", "compatible_car_ids",
            "created_at", "updated_at",
        ]
        # stock is a cached warehouse total; change it with stock receipts (inventory app), not here.
        read_only_fields = ["stock", "created_at", "updated_at"]

    @extend_schema_field(serializers.FloatField(allow_null=True))
    def get_rating_avg(self, obj):
        value = getattr(obj, "rating_avg", None)
        if value is None and not hasattr(obj, "rating_avg"):
            value = obj.reviews.aggregate(a=models.Avg("rating"))["a"]
        return round(float(value), 1) if value is not None else None

    @extend_schema_field(serializers.IntegerField())
    def get_rating_count(self, obj):
        value = getattr(obj, "rating_count", None)
        return value if value is not None else obj.reviews.count()

    def validate_specs(self, value):
        if not isinstance(value, list) or not all(isinstance(r, dict) and "value" in r for r in value):
            raise serializers.ValidationError('Specs must be a list like [{"en": "Diameter", "ru": "Диаметр", "value": "296 mm"}].')
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(_("Price must be greater than 0."))
        return value


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "rating", "text", "author", "is_mine", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    @extend_schema_field(serializers.CharField())
    def get_author(self, obj):
        # first name + initial of the last name, never the email
        u = obj.user
        if u.first_name:
            return f"{u.first_name} {u.last_name[:1] + '.' if u.last_name else ''}".strip()
        return u.username

    @extend_schema_field(serializers.BooleanField())
    def get_is_mine(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.user_id == request.user.id)

    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError(_("Rating must be from 1 to 5."))
        return value
