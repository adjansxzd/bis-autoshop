from rest_framework import serializers

from .models import Brand, CarModel, Category, Product


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

    category_id = serializers.PrimaryKeyRelatedField(source="category", queryset=Category.objects.all(), write_only=True)
    brand_id = serializers.PrimaryKeyRelatedField(source="brand", queryset=Brand.objects.all(), write_only=True)
    compatible_car_ids = serializers.PrimaryKeyRelatedField(
        source="compatible_cars", queryset=CarModel.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name_en", "name_ru", "description_en", "description_ru",
            "price", "stock", "in_stock", "image_url", "is_active",
            "category", "brand", "compatible_cars",
            "category_id", "brand_id", "compatible_car_ids",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
