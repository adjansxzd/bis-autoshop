"""
python manage.py seed           -> fills the DB with demo data (safe to run again)
python manage.py seed --reset   -> deletes catalog data first
Demo accounts are for LOCAL development only.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from catalog.models import Brand, CarModel, Category, Product

CATEGORIES = [
    ("brakes", "Brakes", "Тормозная система", "disc"),
    ("engine-oil", "Engine oil & fluids", "Масла и жидкости", "droplet"),
    ("filters", "Filters", "Фильтры", "filter"),
    ("lighting", "Lighting", "Освещение", "bulb"),
    ("suspension", "Suspension", "Подвеска", "spring"),
    ("accessories", "Accessories", "Аксессуары", "star"),
    ("tires", "Tires & wheels", "Шины и диски", "wheel"),
]

BRANDS = [
    ("Bosch", "Germany"), ("Brembo", "Italy"), ("Castrol", "United Kingdom"), ("Mann-Filter", "Germany"),
    ("Philips", "Netherlands"), ("KYB", "Japan"), ("Michelin", "France"), ("Toyota Genuine", "Japan"),
]

CARS = [
    ("Toyota", "Camry", 2018, 2024), ("Toyota", "Land Cruiser Prado", 2010, 2023), ("Hyundai", "Elantra", 2016, 2023),
    ("Hyundai", "Tucson", 2015, 2024), ("Kia", "Rio", 2017, 2023), ("Chevrolet", "Cobalt", 2013, 2023),
    ("Lada", "Granta", 2011, 2024), ("Volkswagen", "Polo", 2015, 2022),
]

# sku, name_en, name_ru, category, brand, price KZT, stock, compatible car indexes
PRODUCTS = [
    ("BR-001", "Front brake pads", "Передние тормозные колодки", "brakes", "Brembo", 24900, 15, [0, 2, 3]),
    ("BR-002", "Ventilated brake disc", "Вентилируемый тормозной диск", "brakes", "Brembo", 38500, 8, [0, 1]),
    ("BR-003", "Rear brake pads", "Задние тормозные колодки", "brakes", "Bosch", 17900, 20, [2, 4, 6]),
    ("BR-004", "Brake fluid DOT4 1L", "Тормозная жидкость DOT4 1л", "brakes", "Bosch", 4900, 40, [0, 1, 2, 3, 4, 5, 6, 7]),
    ("OIL-001", "Castrol EDGE 5W-30 4L", "Моторное масло Castrol EDGE 5W-30 4л", "engine-oil", "Castrol", 21500, 30, [0, 2, 3, 7]),
    ("OIL-002", "Castrol Magnatec 10W-40 4L", "Моторное масло Castrol Magnatec 10W-40 4л", "engine-oil", "Castrol", 14900, 25, [4, 5, 6]),
    ("OIL-003", "Antifreeze G12 5L", "Антифриз G12 5л", "engine-oil", "Castrol", 8900, 18, [0, 1, 2, 3, 4, 5, 6, 7]),
    ("FL-001", "Oil filter W 712/95", "Масляный фильтр W 712/95", "filters", "Mann-Filter", 3900, 50, [2, 3, 4]),
    ("FL-002", "Air filter C 26 017", "Воздушный фильтр C 26 017", "filters", "Mann-Filter", 6500, 35, [0, 1]),
    ("FL-003", "Cabin filter with carbon", "Салонный фильтр угольный", "filters", "Bosch", 5900, 0, [0, 2, 3, 4]),
    ("FL-004", "Toyota genuine oil filter", "Оригинальный масляный фильтр Toyota", "filters", "Toyota Genuine", 4500, 22, [0, 1]),
    ("LT-001", "H7 X-tremeVision bulbs (2 pcs)", "Лампы H7 X-tremeVision (2 шт)", "lighting", "Philips", 11900, 28, [2, 4, 5, 7]),
    ("LT-002", "LED H4 headlight kit", "Комплект LED ламп H4", "lighting", "Philips", 27900, 10, [5, 6]),
    ("SU-001", "Front shock absorber Excel-G", "Передний амортизатор Excel-G", "suspension", "KYB", 32900, 12, [0, 2, 3]),
    ("SU-002", "Rear shock absorber Excel-G", "Задний амортизатор Excel-G", "suspension", "KYB", 28900, 9, [4, 6, 7]),
    ("SU-003", "Stabilizer link", "Стойка стабилизатора", "suspension", "Toyota Genuine", 9900, 16, [0, 1]),
    ("AC-001", "Wiper blades Aerotwin 600/475", "Щётки стеклоочистителя Aerotwin 600/475", "accessories", "Bosch", 12900, 30, [0, 2, 3]),
    ("AC-002", "Car battery S4 60Ah", "Аккумулятор S4 60Ач", "accessories", "Bosch", 54900, 7, [0, 2, 3, 4, 5, 6, 7]),
    ("AC-003", "All-weather floor mats", "Всесезонные коврики", "accessories", "Toyota Genuine", 19900, 14, [0, 1]),
    ("TR-001", "Michelin X-Ice North 4 205/55 R16", "Шина Michelin X-Ice North 4 205/55 R16", "tires", "Michelin", 62900, 24, [2, 7]),
    ("TR-002", "Michelin Primacy 4 215/55 R17", "Шина Michelin Primacy 4 215/55 R17", "tires", "Michelin", 58900, 16, [0, 3]),
]

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

    def handle(self, *args, **opts):
        if opts["reset"]:
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
        cars = []
        for make, model, y1, y2 in CARS:
            car, _ = CarModel.objects.get_or_create(make=make, model=model, year_from=y1, year_to=y2)
            cars.append(car)

        for sku, en, ru, cat, brand, price, stock, fits in PRODUCTS:
            p, _ = Product.objects.update_or_create(sku=sku, defaults={
                "name_en": en, "name_ru": ru,
                "description_en": f"{en} by {brand}. Quality part with manufacturer warranty.",
                "description_ru": f"{ru} от {brand}. Качественная деталь с гарантией производителя.",
                "category": cats[cat], "brand": brands[brand], "price": price, "stock": stock,
            })
            p.compatible_cars.set([cars[i] for i in fits])

        User = get_user_model()
        for username, email, role, superuser in DEMO_USERS:
            user, created = User.objects.get_or_create(username=username, defaults={"email": email, "role": role})
            if created:
                user.set_password(DEMO_PASSWORD)
                user.is_staff = role in ("admin", "manager")  # can open /admin/
                user.is_superuser = superuser
                user.save()

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Category.objects.count()} categories, {Brand.objects.count()} brands, "
            f"{CarModel.objects.count()} car models, {Product.objects.count()} products, "
            f"demo users: admin / manager / customer (password: {DEMO_PASSWORD})"
        ))
