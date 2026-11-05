import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """Query params: ?category=brakes&brand=3&min_price=1000&max_price=50000&car=5&in_stock=true"""

    category = django_filters.CharFilter(field_name="category__slug")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    car = django_filters.NumberFilter(field_name="compatible_cars__id")  # "Fits my car"
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    class Meta:
        model = Product
        fields = ["category", "brand", "car", "min_price", "max_price", "in_stock"]

    def filter_in_stock(self, queryset, name, value):
        return queryset.filter(stock__gt=0) if value else queryset.filter(stock=0)
