from django.db import models


class Category(models.Model):
    """Parts category, e.g. Brakes, Engine oil, Lighting. Supports one level of nesting."""

    name_en = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")
    icon = models.CharField(max_length=40, blank=True, help_text="Icon name used by the frontend")

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name_en"]

    def __str__(self):
        return self.name_en


class Brand(models.Model):
    """Manufacturer of the part (Bosch, Brembo, Castrol...)."""

    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=60, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CarModel(models.Model):
    """A vehicle a part can fit: make + model + year range. Powers the 'Fits my car' filter."""

    make = models.CharField(max_length=60)       # Toyota
    model = models.CharField(max_length=60)      # Camry
    year_from = models.PositiveSmallIntegerField()
    year_to = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["make", "model", "year_from"]
        unique_together = ("make", "model", "year_from", "year_to")

    def __str__(self):
        return f"{self.make} {self.model} ({self.year_from}-{self.year_to})"


class Product(models.Model):
    """A part or accessory sold in the shop."""

    sku = models.CharField(max_length=40, unique=True)
    name_en = models.CharField(max_length=200)
    name_ru = models.CharField(max_length=200)
    description_en = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    compatible_cars = models.ManyToManyField(CarModel, blank=True, related_name="products")
    price = models.DecimalField(max_digits=10, decimal_places=2)  # in KZT
    stock = models.PositiveIntegerField(default=0)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def in_stock(self):
        return self.stock > 0

    def __str__(self):
        return f"{self.sku} — {self.name_en}"
