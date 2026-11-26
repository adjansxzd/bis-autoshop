from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import StockMovement, StockReceipt, StockReceiptItem, Supplier, Warehouse, WarehouseStock
from .services import receive_stock


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "address")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ("warehouse", "product", "quantity", "updated_at")
    list_filter = ("warehouse",)
    search_fields = ("product__sku", "product__name_en", "product__name_ru")

    def get_readonly_fields(self, request, obj=None):
        # Balances change only through receipts, sales and returns (inventory.services).
        if obj:
            return ("warehouse", "product", "quantity", "updated_at")
        return ("quantity", "updated_at")


class StockReceiptItemInline(admin.TabularInline):
    model = StockReceiptItem
    extra = 0

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.posted_at:
            return ("product", "quantity")
        return super().get_readonly_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.posted_at:
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.posted_at:
            return False
        return super().has_delete_permission(request, obj)


@admin.action(description="Провести поступление")
def post_stock_receipts(modeladmin, request, queryset):
    posted = 0
    already_posted = 0
    failed = 0
    for receipt in queryset:
        try:
            if receive_stock(receipt, request.user):
                posted += 1
            else:
                already_posted += 1
        except ValidationError as error:
            failed += 1
            modeladmin.message_user(request, str(error), level=messages.ERROR)

    if posted:
        modeladmin.message_user(request, f"Проведено поступлений: {posted}.", level=messages.SUCCESS)
    if already_posted:
        modeladmin.message_user(request, f"Уже проведено: {already_posted}.", level=messages.WARNING)
    if failed:
        modeladmin.message_user(request, f"Не проведено: {failed}.", level=messages.ERROR)


@admin.register(StockReceipt)
class StockReceiptAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "supplier", "warehouse", "created_at", "posted_at")
    list_filter = ("warehouse", "supplier")
    search_fields = ("number", "supplier__name")
    readonly_fields = ("posted_at",)
    inlines = [StockReceiptItemInline]
    actions = [post_stock_receipts]

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.posted_at:
            fields += ["warehouse", "supplier", "number"]
        return fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # A new receipt can only come from an active supplier.
        if db_field.name == "supplier":
            kwargs["queryset"] = Supplier.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.posted_at:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(StockReceiptItem)
class StockReceiptItemAdmin(admin.ModelAdmin):
    list_display = ("receipt", "product", "quantity")
    list_filter = ("receipt__warehouse",)
    search_fields = ("product__sku", "product__name_en", "product__name_ru")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.receipt.posted_at:
            return tuple(field.name for field in self.model._meta.fields)
        return super().get_readonly_fields(request, obj)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "receipt":
            kwargs["queryset"] = StockReceipt.objects.filter(posted_at__isnull=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.receipt.posted_at:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "movement_type", "warehouse", "product", "quantity", "order", "receipt", "user")
    list_filter = ("movement_type", "warehouse", "created_at")
    search_fields = ("product__sku", "product__name_en", "product__name_ru")
    readonly_fields = ("created_at",)

    # The journal is written only by inventory.services; in the admin it is view-only.
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False