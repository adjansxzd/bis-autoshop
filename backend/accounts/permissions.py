from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsStaffRoleOrReadOnly(BasePermission):
    """Anyone can read; only manager/admin roles can create, update or delete."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff_role or user.is_superuser))


class IsStaffRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff_role or user.is_superuser))
