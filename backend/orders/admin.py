from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.utils.html import format_html

from .models import Cart, CartItem, Order, OrderItem
from .services import change_order_status, validate_status_transition

STATUS_COLORS = {
    "new": "#d91f26", "paid": "#2563eb", "shipped": "#b45309", "delivered": "#138a43", "cancelled": "#6b7280",
}


class OrderItemInline(admin.TabularInline):
    """Order lines are fixed after checkout: changing them would not move stock."""

    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("product", "warehouse", "quantity", "unit_price", "line_total")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Subtotal")
    def line_total(self, obj):
        return obj.subtotal


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
    list_display = ("id", "user", "status_badge", "items_count", "total", "phone", "created_at")
    list_display_links = ("id", "user")
    list_filter = ("status", "created_at")
    search_fields = ("id", "user__username", "user__email", "phone", "shipping_address")
    date_hierarchy = "created_at"
    list_per_page = 25
    readonly_fields = ("user", "total", "created_at")
    fields = ("user", "status", "shipping_address", "phone", "total", "created_at")
    inlines = [OrderItemInline]
    actions = ["mark_paid", "mark_shipped", "mark_delivered", "mark_cancelled"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user").annotate(n_items=Count("items"))

    def has_add_permission(self, request):
        # Orders are created by checkout only (it writes off stock).
        return False

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        color = STATUS_COLORS.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-weight:600">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description="Items", ordering="n_items")
    def items_count(self, obj):
        return obj.n_items

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            new_status = obj.status
            obj.status = form.initial["status"]
            # Same rules as the API: validates the transition and returns stock on cancel.
            change_order_status(obj, new_status, request.user)
            obj.status = new_status
        super().save_model(request, obj, form, change)

    def _set(self, request, queryset, status, label):
        """Bulk action. Uses the same service as the API, so the status rules and stock returns apply.
        Orders that can't move to this status (e.g. cancelling a shipped order) are skipped with a message."""
        done, skipped = 0, []
        for order in queryset:
            try:
                change_order_status(order, status, request.user)
                done += 1
            except ValidationError as error:
                skipped.append(f"#{order.pk}: {' '.join(error.messages)}")
        if done:
            self.message_user(request, f"{done} order(s) marked as {label}.", messages.SUCCESS)
        if skipped:
            self.message_user(request, "Skipped — " + "; ".join(skipped), messages.WARNING)

    @admin.action(description="Mark as paid")
    def mark_paid(self, request, queryset):
        self._set(request, queryset, Order.Status.PAID, "paid")

    @admin.action(description="Mark as shipped (on the way to the customer)")
    def mark_shipped(self, request, queryset):
        self._set(request, queryset, Order.Status.SHIPPED, "shipped")

    @admin.action(description="Mark as delivered")
    def mark_delivered(self, request, queryset):
        self._set(request, queryset, Order.Status.DELIVERED, "delivered")

    @admin.action(description="Cancel (only new / paid orders; items go back to the warehouse)")
    def mark_cancelled(self, request, queryset):
        self._set(request, queryset, Order.Status.CANCELLED, "cancelled")


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Visible to admins only (managers have no cart permissions)."""

    list_display = ("user", "updated_at")
    inlines = [CartItemInline]
