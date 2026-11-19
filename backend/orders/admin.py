from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Cart, CartItem, Order, OrderItem
from .services import change_order_status, validate_status_transition


class OrderItemInline(admin.TabularInline):
    """Order lines are fixed after checkout: changing them would not move stock."""

    model = OrderItem
    extra = 0
    readonly_fields = ("product", "warehouse", "quantity", "unit_price")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def clean_status(self):
        new_status = self.cleaned_data["status"]
        if self.instance.pk:
            try:
                validate_status_transition(self.instance.status, new_status)
            except ValidationError as error:
                raise forms.ValidationError(error.messages)
        return new_status


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = ("id", "user", "status", "total", "created_at")
    list_filter = ("status",)
    readonly_fields = ("user", "total", "created_at")
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        # Orders are created by checkout only (it writes off stock).
        return False

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            new_status = obj.status
            obj.status = form.initial["status"]
            # Same rules as the API: validates the transition and returns stock on cancel.
            change_order_status(obj, new_status, request.user)
            obj.status = new_status
        super().save_model(request, obj, form, change)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]
