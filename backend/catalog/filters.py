import django_filters
from django.db.models import Exists, OuterRef

from .models import Product
from inventory.models import WarehouseStock
from inventory.signals import MAIN_WAREHOUSE_NAME


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
        main_warehouse_stock = WarehouseStock.objects.filter(
            product_id=OuterRef("pk"),
            warehouse__name=MAIN_WAREHOUSE_NAME,
            quantity__gt=0,
        )
        return queryset.annotate(_has_main_warehouse_stock=Exists(main_warehouse_stock)).filter(
            _has_main_warehouse_stock=value
        )
