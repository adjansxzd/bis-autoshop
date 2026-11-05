from django.contrib import admin

from .models import Brand, CarModel, Category, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name_en", "brand", "category", "price", "stock", "is_active")
    list_filter = ("category", "brand", "is_active")
    search_fields = ("sku", "name_en", "name_ru")
    filter_horizontal = ("compatible_cars",)


admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(CarModel)
