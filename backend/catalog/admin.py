from django.conf import settings
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Brand, CarModel, Category, Product, Review

LOW_STOCK = 5  # products with this many or fewer are highlighted

admin.site.site_header = "AutoShop administration"
admin.site.site_title = "AutoShop admin"
admin.site.index_title = "Catalog, orders and users"
admin.site.site_url = settings.SHOP_URL  # "View site" → the Angular shop


class StockFilter(admin.SimpleListFilter):
    """Right-hand filter: Out of stock / Low stock / In stock."""

    title = "stock"
    parameter_name = "stock"

    def lookups(self, request, model_admin):
        return [("out", "Out of stock"), ("low", f"Low (1–{LOW_STOCK})"), ("ok", "In stock")]

    def queryset(self, request, queryset):
        if self.value() == "out":
            return queryset.filter(stock=0)
        if self.value() == "low":
            return queryset.filter(stock__gt=0, stock__lte=LOW_STOCK)
        if self.value() == "ok":
            return queryset.filter(stock__gt=LOW_STOCK)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumb", "sku", "name_en", "brand", "category", "price", "stock", "stock_status", "rating", "is_active")
    list_display_links = ("thumb", "sku", "name_en")
    list_editable = ("price", "is_active")  # quick edits straight from the list
    # stock is a cached warehouse total; change it with a stock receipt in the Inventory section.
    readonly_fields = ("stock", "photo_preview")
    list_filter = (StockFilter, "category", "brand", "is_active")
    search_fields = ("sku", "name_en", "name_ru", "oem_numbers", "brand__name")
    list_select_related = ("brand", "category")
    list_per_page = 25
    filter_horizontal = ("compatible_cars",)
    actions = ["activate", "deactivate"]
    fieldsets = (
        ("Product", {"fields": ("sku", "category", "brand", "price", "is_active")}),
        ("Stock", {"fields": ("stock",), "description": "Total over all warehouses. To add stock, post a Stock receipt (Inventory)."}),
        ("English", {"fields": ("name_en", "description_en")}),
        ("Русский", {"fields": ("name_ru", "description_ru")}),
        ("Fitment", {"fields": ("compatible_cars",), "description": "Cars this part fits ('Fits my car' filter)."}),
        ("Photo", {"fields": ("image", "photo_preview")}),
        ("3D model", {"fields": ("model_3d",), "description": "Optional .glb file — customers can rotate it on the product page."}),
        ("Details", {"fields": ("oem_numbers", "specs"),
                     "description": 'Specs: [{"en": "Diameter", "ru": "Диаметр", "value": "296 mm"}, ...]'}),
    )

    def get_queryset(self, request):
        from .reviews import with_ratings
        return with_ratings(super().get_queryset(request))

    @admin.display(description="")
    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:6px">', obj.image.url)
        return format_html('<span style="display:inline-block;width:40px;height:40px;border-radius:6px;background:#f0f0ed"></span>')

    @admin.display(description="Preview")
    def photo_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width:240px;border-radius:8px">', obj.image.url)
        return "No photo yet — the shop shows the category icon."

    @admin.display(description="Rating", ordering="rating_avg")
    def rating(self, obj):
        if not obj.rating_count:
            return "—"
        return f"{obj.rating_avg:.1f}★ ({obj.rating_count})"

    @admin.display(description="Stock status", ordering="stock")
    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<b style="color:#c81e1e">Out of stock</b>')
        if obj.stock <= LOW_STOCK:
            return format_html('<b style="color:#b45309">Low: {}</b>', obj.stock)
        return format_html('<span style="color:#138a43">OK</span>')

    @admin.action(description="Show selected products in the shop")
    def activate(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_active=True)} product(s) are now visible.")

    @admin.action(description="Hide selected products from the shop")
    def deactivate(self, request, queryset):
        self.message_user(request, f"{queryset.update(is_active=False)} product(s) hidden.")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_ru", "slug", "products")
    search_fields = ("name_en", "name_ru")
    prepopulated_fields = {"slug": ("name_en",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(n=Count("products"))

    @admin.display(description="Products", ordering="n")
    def products(self, obj):
        return obj.n


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    search_fields = ("name",)


@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ("make", "model", "year_from", "year_to")
    list_filter = ("make",)
    search_fields = ("make", "model")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Moderation: managers can read and delete reviews (e.g. rude or spam), not write them."""

    list_display = ("product", "user", "stars", "short_text", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__sku", "product__name_en", "user__username", "text")
    list_select_related = ("product", "user")
    readonly_fields = ("product", "user", "rating", "text", "created_at", "updated_at")

    def has_add_permission(self, request):
        return False  # reviews are written by customers in the shop

    @admin.display(description="Rating", ordering="rating")
    def stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)

    @admin.display(description="Text")
    def short_text(self, obj):
        return (obj.text[:70] + "…") if len(obj.text) > 70 else obj.text
