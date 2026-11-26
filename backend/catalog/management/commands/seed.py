"""
python manage.py seed           -> fills the DB with demo data (safe to run again)
python manage.py seed --reset   -> deletes catalog, orders, carts and stock data first
Demo accounts are for LOCAL development only.

Opening stock is not written to Product.stock: it is posted as stock receipts
(inventory.services.receive_stock), one receipt per supplier (see CATEGORY_SUPPLIER
in seed_data.py), so every balance has a matching journal entry.
Suppliers are permanent reference data: --reset keeps them.
"""
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Brand, CarModel, Category, Product, Review
from inventory.constants import MAIN_WAREHOUSE_NAME
from inventory.models import StockMovement, StockReceipt, StockReceiptItem, Supplier, Warehouse, WarehouseStock
from inventory.services import receive_stock
from orders.models import CartItem, Order, OrderItem

from .seed_data import (
    BRANDS, CARS, CATEGORIES, CATEGORY_SUPPLIER, DEMO_REVIEWERS, DEMO_REVIEWS, DESCRIPTIONS, PRODUCTS, SUPPLIERS,
)

# Product photos: put files named by SKU into this folder (BR-001.jpg, OIL-001.png ...) and run `seed`.
# They are copied into media/ once. Photos uploaded in the admin panel are never overwritten.
SEED_IMAGES = Path(__file__).resolve().parents[2] / "seed_images"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")

DEMO_USERS = [
    ("admin", "admin@autoshop.local", "admin", True),
    ("manager", "manager@autoshop.local", "manager", False),
    ("customer", "customer@autoshop.local", "customer", False),
]
DEMO_PASSWORD = "demo12345"


class Command(BaseCommand):
    help = "Fill the database with demo catalog data and demo users"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete catalog data before seeding")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["reset"]:
            # Children first: stock rows, journal, receipts and order lines PROTECT products.
            # Suppliers are kept: their receipts are deleted here, so PROTECT does not block anything.
            StockMovement.objects.all().delete()
            StockReceiptItem.objects.all().delete()
            StockReceipt.objects.all().delete()
            WarehouseStock.objects.all().delete()
            CartItem.objects.all().delete()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            CarModel.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()

        cats = {}
        for slug, en, ru, icon in CATEGORIES:
            cats[slug], _ = Category.objects.update_or_create(slug=slug, defaults={"name_en": en, "name_ru": ru, "icon": icon})
        brands = {}
        for name, country in BRANDS:
            brands[name], _ = Brand.objects.update_or_create(name=name, defaults={"country": country})
        cars = {}
        for key, (make, model, y1, y2) in CARS.items():
            cars[key], _ = CarModel.objects.get_or_create(make=make, model=model, year_from=y1, year_to=y2)

        suppliers = {}
        for key, name, contact, email, _prefix in SUPPLIERS:
            suppliers[key], _ = Supplier.objects.get_or_create(
                name=name, defaults={"contact_person": contact, "email": email}
            )

        warehouse, _ = Warehouse.objects.get_or_create(name=MAIN_WAREHOUSE_NAME)
        opening = {key: [] for key in suppliers}  # supplier key -> [(product, qty)]
        images_added = 0
        for sku, en, ru, cat, brand, price, stock, fits, oem, specs in PRODUCTS:
            desc_en, desc_ru = DESCRIPTIONS[cat]
            # "stock" is NOT in defaults: re-running seed must not overwrite the cached total.
            p, _ = Product.objects.update_or_create(sku=sku, defaults={
                "name_en": en, "name_ru": ru,
                "description_en": desc_en.format(name=en, brand=brand),
                "description_ru": desc_ru.format(name=ru, brand=brand),
                "category": cats[cat], "brand": brands[brand], "price": price,
                "oem_numbers": oem, "specs": specs,
            })
            p.compatible_cars.set([cars[key] for key in fits])
            images_added += self.attach_image(p)
            # Opening stock only for products with no journal entries and no balance yet
            # (an old DB may already hold balances created before the journal existed).
            if (
                stock > 0
                and not StockMovement.objects.filter(product=p).exists()
                and not WarehouseStock.objects.filter(product=p, quantity__gt=0).exists()
            ):
                opening[CATEGORY_SUPPLIER[cat]].append((p, stock))

        User = get_user_model()
        for username, email, role, _superuser in DEMO_USERS:
            user, created = User.objects.get_or_create(username=username, defaults={"email": email, "role": role})
            if created:
                user.set_password(DEMO_PASSWORD)
            user.role = role
            user.save()  # User.save() syncs staff/superuser flags and the Managers group from the role

        manager = User.objects.get(username="manager")
        prefixes = {key: prefix for key, *_rest, prefix in SUPPLIERS}
        receipts_added = 0
        for key, lines in opening.items():
            if not lines:
                continue
            receipt = StockReceipt.objects.create(
                warehouse=warehouse, supplier=suppliers[key], number=self.next_receipt_number(prefixes[key])
            )
            StockReceiptItem.objects.bulk_create(
                [StockReceiptItem(receipt=receipt, product=p, quantity=qty) for p, qty in lines]
            )
            receive_stock(receipt, manager)
            receipts_added += 1

        reviews_added = self.seed_reviews(User)

        if opts.get("verbosity", 1) > 0:
            self.stdout.write(self.style.SUCCESS(
                f"Seeded {Category.objects.count()} categories, {Brand.objects.count()} brands, "
                f"{CarModel.objects.count()} car models, {Product.objects.count()} products "
                f"({images_added} new photos, {reviews_added} new reviews), "
                f"{Supplier.objects.count()} suppliers ({receipts_added} new opening receipts), "
                f"demo users: admin / manager / customer (password: {DEMO_PASSWORD})"
            ))

    @staticmethod
    def next_receipt_number(prefix):
        """DAT-0001, DAT-0002 ...: first number not used yet (receipt numbers are unique)."""
        n = 1
        while StockReceipt.objects.filter(number=f"{prefix}-{n:04d}").exists():
            n += 1
        return f"{prefix}-{n:04d}"

    def attach_image(self, product):
        """Copy seed_images/<SKU>.<ext> to the product if it has no photo yet. Returns 1 if added."""
        if product.image or not SEED_IMAGES.exists():
            return 0
        for ext in IMAGE_EXTS:
            path = SEED_IMAGES / f"{product.sku}{ext}"
            if path.exists():
                with path.open("rb") as fh:
                    product.image.save(path.name, File(fh), save=True)
                return 1
        return 0

    def seed_reviews(self, User):
        """Demo reviewers (customers) and a few reviews, so ratings show up on a fresh database."""
        people = {}
        for username, first, last in DEMO_REVIEWERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={"email": f"{username}@autoshop.local", "first_name": first, "last_name": last}
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            people[username] = user
        added = 0
        for sku, username, stars, text in DEMO_REVIEWS:
            product = Product.objects.filter(sku=sku).first()
            if product:
                _, created = Review.objects.get_or_create(
                    product=product, user=people[username], defaults={"rating": stars, "text": text}
                )
                added += created
        return added
