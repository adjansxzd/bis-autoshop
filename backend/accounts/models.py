from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role. Roles drive access rules (customer vs manager vs admin)."""

    class Role(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        MANAGER = "manager", "Store manager"
        ADMIN = "admin", "Administrator"

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    preferred_language = models.CharField(max_length=2, default="en", choices=[("en", "English"), ("ru", "Русский")])

    @property
    def is_staff_role(self):
        return self.role in (self.Role.MANAGER, self.Role.ADMIN)

    def __str__(self):
        return f"{self.username} ({self.role})"
