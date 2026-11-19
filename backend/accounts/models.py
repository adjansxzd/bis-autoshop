from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models

MANAGERS_GROUP = "Managers"

# What a store manager may do in the admin panel: run the catalog and the orders, nothing else.
MANAGER_PERMISSIONS = {
    "catalog": ["product", "category", "brand", "carmodel"],          # full CRUD
    "orders": ["order"],                                              # view + change status
    "inventory": ["warehouse", "warehousestock", "stockreceipt", "stockreceiptitem", "stockmovement"],
}
MANAGER_ACTIONS = {
    "product": ["view", "add", "change", "delete"],
    "category": ["view", "add", "change", "delete"],
    "brand": ["view", "add", "change", "delete"],
    "carmodel": ["view", "add", "change", "delete"],
    "order": ["view", "change"],
    # warehouse (Daulet's inventory app): managers post stock receipts and read balances / the journal
    "warehouse": ["view"],
    "warehousestock": ["view"],
    "stockreceipt": ["view", "add", "change"],
    "stockreceiptitem": ["view", "add", "change", "delete"],
    "stockmovement": ["view"],
}


def managers_group() -> Group:
    """Create (or refresh) the 'Managers' group with exactly the permissions above."""
    group, _ = Group.objects.get_or_create(name=MANAGERS_GROUP)
    codenames = [f"{action}_{model}" for model, actions in MANAGER_ACTIONS.items() for action in actions]
    perms = Permission.objects.filter(
        content_type__app_label__in=MANAGER_PERMISSIONS.keys(), codename__in=codenames
    )
    group.permissions.set(perms)
    return group


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)  # `createsuperuser` → admin role
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user with a role. The role is the single source of truth for access:
      customer → no admin panel
      manager  → admin panel: catalog + orders (via the 'Managers' group)
      admin    → everything (superuser), including users and roles
    """

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        MANAGER = "manager", "Store manager"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    preferred_language = models.CharField(max_length=2, default="en", choices=[("en", "English"), ("ru", "Русский")])

    objects = UserManager()

    @property
    def is_staff_role(self):
        return self.role in (self.Role.MANAGER, self.Role.ADMIN)

    def save(self, *args, **kwargs):
        # keep Django's admin flags in line with the role
        self.is_staff = self.role in (self.Role.MANAGER, self.Role.ADMIN)
        self.is_superuser = self.role == self.Role.ADMIN
        super().save(*args, **kwargs)
        # group membership needs a saved user (many-to-many)
        group = managers_group()
        if self.role == self.Role.MANAGER:
            self.groups.add(group)
        else:
            self.groups.remove(group)

    def __str__(self):
        return f"{self.username} ({self.role})"
