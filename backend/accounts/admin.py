from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Only admins see this section: managers have no permissions on users."""

    list_display = ("username", "email", "role", "is_active", "date_joined")
    list_filter = ("role", "is_active")
    search_fields = ("username", "email", "phone")
    ordering = ("-date_joined",)
    # role decides staff/superuser automatically (see User.save), so those flags are hidden
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email", "phone", "preferred_language")}),
        ("Access", {"fields": ("role", "is_active")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("username", "email", "role", "password1", "password2")}),
    )
    actions = ["block_users", "unblock_users"]

    @admin.action(description="Block selected users")
    def block_users(self, request, queryset):
        updated = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"{updated} user(s) blocked.")

    @admin.action(description="Unblock selected users")
    def unblock_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) unblocked.")
