"""
python manage.py seed_warehouse  -> demo warehouse data on top of `seed` (safe to run again)

Creates (each step is skipped if it was already done):
- the catalog and demo users from `seed`, and Main warehouse;
- 3 extra products: WH-001 (plenty of stock), WH-002 (low stock: 2), WH-003 (zero stock);
- 2 posted stock receipts WH-REC-001 and WH-REC-002 (via inventory.services.receive_stock);
- 3 orders of the demo customer through the real checkout logic (orders.services.place_order):
  one paid, one delivered and one cancelled (stock returned).
After it the journal holds all movement types: receipt, sale and return.
"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Brand, Category, Product
from inventory.constants import MAIN_WAREHOUSE_NAME
from inventory.models import StockMovement, StockReceipt, StockReceiptItem, Warehouse
from inventory.services import receive_stock
from orders.models import Order
from orders.services import change_order_status, place_order

# sku, name_en, name_ru, price KZT
PRODUCTS = [
    ("WH-001", "Iridium spark plug", "Иридиевая свеча зажигания", 6900),
    ("WH-002", "Timing belt kit", "Комплект ремня ГРМ", 45900),
    ("WH-003", "Electric fuel pump", "Электрический топливный насос", 39900),
]

# receipt number -> [(sku, quantity)]
RECEIPTS = {
    "WH-REC-001": [("WH-001", 40), ("WH-002", 2)],
    "WH-REC-002": [("BR-001", 10), ("OIL-001", 6)],
}

# shipping_address marks a seeded order, so it is not created twice
ORDER_MARK = "[seed_warehouse] Almaty, Abay 10"
ORDERS = [
    (f"{ORDER_MARK}, order 1", [("WH-001", 3), ("BR-001", 1)], Order.Status.PAID),
    (f"{ORDER_MARK}, order 2", [("OIL-001", 2)], Order.Status.DELIVERED),
    (f"{ORDER_MARK}, order 3", [("WH-001", 2)], Order.Status.CANCELLED),
]


class Command(BaseCommand):
    help = "Fill the database with demo warehouse data: receipts, sales and a cancelled order"

    @transaction.atomic
    def handle(self, *args, **opts):
        call_command("seed", stdout=self.stdout)
        User = get_user_model()
        manager = User.objects.get(username="manager")
        customer = User.objects.get(username="customer")
        warehouse, _ = Warehouse.objects.get_or_create(name=MAIN_WAREHOUSE_NAME)

        category = Category.objects.get(slug="accessories")
        brand = Brand.objects.get(name="Bosch")
        for sku, en, ru, price in PRODUCTS:
            Product.objects.get_or_create(sku=sku, defaults={
                "name_en": en, "name_ru": ru,
                "description_en": f"{en} by Bosch.", "description_ru": f"{ru} от Bosch.",
                "category": category, "brand": brand, "price": price,
            })

        for number, lines in RECEIPTS.items():
            receipt, created = StockReceipt.objects.get_or_create(number=number, defaults={"warehouse": warehouse})
            if created:
                StockReceiptItem.objects.bulk_create([
                    StockReceiptItem(receipt=receipt, product=Product.objects.get(sku=sku), quantity=qty)
                    for sku, qty in lines
                ])
            receive_stock(receipt, manager)  # returns False if already posted

        for address, lines, final_status in ORDERS:
            if Order.objects.filter(user=customer, shipping_address=address).exists():
                continue
            order = place_order(
                customer,
                [(Product.objects.get(sku=sku), qty) for sku, qty in lines],
                address,
                "+77001234567",
            )
            change_order_status(order, final_status, manager)

        counts = {t: StockMovement.objects.filter(movement_type=t).count() for t in StockMovement.Type.values}
        self.stdout.write(self.style.SUCCESS(
            f"Warehouse demo data ready. Receipts posted: "
            f"{StockReceipt.objects.filter(posted_at__isnull=False).count()}, "
            f"seeded orders: {Order.objects.filter(shipping_address__startswith=ORDER_MARK).count()}, "
            f"movements: {counts}"
        ))
