from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError, Sum
from django.test import TestCase

from catalog.management.commands.seed_data import CATEGORIES, CATEGORY_SUPPLIER, PRODUCTS, SUPPLIERS
from catalog.models import Product
from orders.models import Order
from orders.services import change_order_status, place_order

from .constants import MAIN_WAREHOUSE_NAME
from .models import StockMovement, StockReceipt, StockReceiptItem, Supplier, Warehouse, WarehouseStock
from .services import receive_stock


User = get_user_model()


class StockReceiptTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def setUp(self):
        self.user = User.objects.get(username="manager")
        self.product = Product.objects.get(sku="BR-001")
        self.warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        self.stock = WarehouseStock.objects.get(warehouse=self.warehouse, product=self.product)

    def create_receipt(self, quantity=5):
        receipt = StockReceipt.objects.create(warehouse=self.warehouse)
        StockReceiptItem.objects.create(receipt=receipt, product=self.product, quantity=quantity)
        return receipt

    def test_receiving_stock_increases_balance_and_records_movement(self):
        starting_quantity = self.stock.quantity
        receipt = self.create_receipt()

        posted = receive_stock(receipt, self.user)

        self.assertTrue(posted)
        self.stock.refresh_from_db()
        self.product.refresh_from_db()
        receipt.refresh_from_db()
        self.assertEqual(self.stock.quantity, starting_quantity + 5)
        self.assertEqual(self.product.stock, starting_quantity + 5)
        self.assertIsNotNone(receipt.posted_at)
        movement = StockMovement.objects.get(receipt=receipt)
        self.assertEqual(movement.movement_type, StockMovement.Type.RECEIPT)
        self.assertEqual(movement.quantity, 5)
        self.assertEqual(movement.user, self.user)

    def test_reposting_receipt_does_not_duplicate_stock_or_movement(self):
        starting_quantity = self.stock.quantity
        receipt = self.create_receipt()

        self.assertTrue(receive_stock(receipt, self.user))
        self.assertFalse(receive_stock(receipt, self.user))

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, starting_quantity + 5)
        self.assertEqual(StockMovement.objects.filter(receipt=receipt).count(), 1)

    def test_empty_receipt_cannot_be_posted(self):
        receipt = StockReceipt.objects.create(warehouse=self.warehouse)

        with self.assertRaises(ValidationError):
            receive_stock(receipt, self.user)

        receipt.refresh_from_db()
        self.assertIsNone(receipt.posted_at)
        self.assertFalse(StockMovement.objects.filter(receipt=receipt).exists())

    def test_receipt_creates_missing_warehouse_row(self):
        WarehouseStock.objects.filter(product=self.product).delete()
        receipt = self.create_receipt(quantity=3)

        receive_stock(receipt, self.user)

        self.assertEqual(WarehouseStock.objects.get(warehouse=self.warehouse, product=self.product).quantity, 3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_same_product_twice_in_one_receipt_is_rejected_by_db(self):
        receipt = self.create_receipt()
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockReceiptItem.objects.create(receipt=receipt, product=self.product, quantity=1)

    def test_db_blocks_second_return_for_same_order_line(self):
        order = place_order(User.objects.get(username="customer"), [(self.product, 1)], "Almaty", "+77001234567")
        StockMovement.objects.create(
            movement_type=StockMovement.Type.RETURN, warehouse=self.warehouse, product=self.product, quantity=1, order=order
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            StockMovement.objects.create(
                movement_type=StockMovement.Type.RETURN, warehouse=self.warehouse, product=self.product, quantity=1, order=order
            )

    def test_db_blocks_negative_balance(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            WarehouseStock.objects.filter(pk=self.stock.pk).update(quantity=-1)

    def test_product_created_with_stock_gets_journal_entry(self):
        product = Product.objects.create(
            sku="SIG-1", name_en="X", name_ru="X", price=100, stock=5,
            category=self.product.category, brand=self.product.brand,
        )
        self.assertEqual(WarehouseStock.objects.get(warehouse=self.warehouse, product=product).quantity, 5)
        movement = StockMovement.objects.get(product=product)
        self.assertEqual((movement.movement_type, movement.quantity), (StockMovement.Type.ADJUSTMENT, 5))


def journal_balance(warehouse_id, product_id):
    """Balance as the journal sees it: receipts + returns + adjustments - sales."""
    moves = StockMovement.objects.filter(warehouse_id=warehouse_id, product_id=product_id)

    def total(*types):
        return moves.filter(movement_type__in=types).aggregate(s=Sum("quantity"))["s"] or 0

    T = StockMovement.Type
    return total(T.RECEIPT, T.RETURN, T.ADJUSTMENT) - total(T.SALE)


class JournalAssertions:
    def assert_balances_match_journal(self):
        rows = list(WarehouseStock.objects.all())
        self.assertGreater(len(rows), 0)
        for row in rows:
            self.assertEqual(row.quantity, journal_balance(row.warehouse_id, row.product_id), row)
        for product in Product.objects.all():
            total = WarehouseStock.objects.filter(product=product).aggregate(s=Sum("quantity"))["s"] or 0
            self.assertEqual(product.stock, total, product.sku)

    def snapshot(self):
        return (
            Product.objects.count(), WarehouseStock.objects.count(), StockReceipt.objects.count(),
            StockMovement.objects.count(), Order.objects.count(),
            tuple(WarehouseStock.objects.order_by("pk").values_list("quantity", flat=True)),
        )


class SeedTests(JournalAssertions, TestCase):

    def test_seed_balances_match_journal(self):
        call_command("seed", stdout=StringIO())
        self.assert_balances_match_journal()
        self.assertEqual(Product.objects.get(sku="BR-001").stock, 15)
        self.assertEqual(Product.objects.get(sku="FL-003").stock, 0)

    def test_seed_rerun_keeps_stock_after_sales(self):
        call_command("seed", stdout=StringIO())
        product = Product.objects.get(sku="BR-001")
        place_order(User.objects.get(username="customer"), [(product, 2)], "Almaty", "+77001234567")

        call_command("seed", stdout=StringIO())

        product.refresh_from_db()
        self.assertEqual(product.stock, 13)  # not reset to 15
        self.assertEqual(StockReceipt.objects.count(), len(SUPPLIERS))  # one opening receipt per supplier
        self.assert_balances_match_journal()

    def test_seed_reset_works_with_orders_and_stock(self):
        call_command("seed", stdout=StringIO())
        manager = User.objects.get(username="manager")
        product = Product.objects.get(sku="BR-001")
        order = place_order(User.objects.get(username="customer"), [(product, 1)], "Almaty", "+77001234567")
        change_order_status(order, Order.Status.CANCELLED, manager)
        receipt = StockReceipt.objects.create(
            warehouse=Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME), supplier=Supplier.objects.first()
        )
        StockReceiptItem.objects.create(receipt=receipt, product=product, quantity=4)
        receive_stock(receipt, manager)

        call_command("seed", "--reset", stdout=StringIO())

        self.assertEqual(Product.objects.count(), len(PRODUCTS))
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Supplier.objects.count(), len(SUPPLIERS))  # suppliers survive --reset
        self.assertEqual(StockReceipt.objects.count(), len(SUPPLIERS))
        self.assertEqual(Product.objects.get(sku="BR-001").stock, 15)
        self.assert_balances_match_journal()


class SupplierTests(JournalAssertions, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def setUp(self):
        self.manager = User.objects.get(username="manager")
        self.warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        self.product = Product.objects.get(sku="BR-001")
        self.supplier = Supplier.objects.get(name=SUPPLIERS[0][1])

    def post_receipt(self, supplier, quantity=5):
        receipt = StockReceipt.objects.create(warehouse=self.warehouse, supplier=supplier)
        StockReceiptItem.objects.create(receipt=receipt, product=self.product, quantity=quantity)
        self.assertTrue(receive_stock(receipt, self.manager))
        receipt.refresh_from_db()
        return receipt

    def test_seed_creates_suppliers_with_contacts(self):
        self.assertEqual(Supplier.objects.count(), 3)
        for _key, name, contact, email, _prefix in SUPPLIERS:
            supplier = Supplier.objects.get(name=name)
            self.assertEqual((supplier.contact_person, supplier.email), (contact, email))
            self.assertEqual(supplier.phone, "")  # seed stores no phone numbers
            self.assertTrue(supplier.is_active)

    def test_every_category_has_a_supplier(self):
        keys = {key for key, *_ in SUPPLIERS}
        self.assertEqual(set(CATEGORY_SUPPLIER), {slug for slug, *_ in CATEGORIES})
        self.assertTrue(set(CATEGORY_SUPPLIER.values()) <= keys)

    def test_opening_stock_comes_in_one_posted_receipt_per_supplier(self):
        receipts = StockReceipt.objects.all()
        self.assertEqual(receipts.count(), 3)
        self.assertFalse(receipts.filter(supplier__isnull=True).exists())
        self.assertFalse(receipts.filter(posted_at__isnull=True).exists())
        self.assertEqual(sorted(receipts.values_list("number", flat=True)), ["ASC-0001", "DAT-0001", "VL-0001"])
        key_by_name = {name: key for key, name, *_ in SUPPLIERS}
        for item in StockReceiptItem.objects.select_related("receipt__supplier", "product__category"):
            self.assertEqual(
                key_by_name[item.receipt.supplier.name], CATEGORY_SUPPLIER[item.product.category.slug], item.product.sku
            )

    def test_receipt_with_supplier_is_posted(self):
        before = self.product.stock
        receipt = self.post_receipt(self.supplier)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, before + 5)
        self.assertEqual(receipt.supplier, self.supplier)
        self.assertIn(receipt, self.supplier.receipts.all())
        movement = StockMovement.objects.get(receipt=receipt)
        self.assertEqual((movement.movement_type, movement.quantity), (StockMovement.Type.RECEIPT, 5))
        self.assert_balances_match_journal()

    def test_receipt_without_supplier_is_posted(self):
        before = self.product.stock
        receipt = self.post_receipt(None, quantity=2)

        self.product.refresh_from_db()
        self.assertIsNone(receipt.supplier)
        self.assertEqual(self.product.stock, before + 2)
        self.assertTrue(StockMovement.objects.filter(receipt=receipt).exists())
        self.assert_balances_match_journal()

    def test_supplier_with_receipts_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.supplier.delete()

    def test_seed_rerun_creates_no_duplicates(self):
        before = self.snapshot() + (Supplier.objects.count(),)
        call_command("seed", verbosity=0)
        self.assertEqual(self.snapshot() + (Supplier.objects.count(),), before)

    def test_seed_balances_match_journal(self):
        self.assert_balances_match_journal()
        for row in WarehouseStock.objects.select_related("product"):
            received = StockMovement.objects.filter(
                product=row.product, movement_type=StockMovement.Type.RECEIPT
            ).aggregate(s=Sum("quantity"))["s"] or 0
            self.assertEqual(row.quantity, received, row.product.sku)  # fresh seed: receipts only

    def test_inactive_supplier_is_not_offered_in_receipt_form(self):
        inactive = Supplier.objects.create(name="ТОО «Закрытый поставщик»", is_active=False)
        self.client.force_login(User.objects.get(username="admin"))

        page = self.client.get("/admin/inventory/stockreceipt/add/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, self.supplier.name)
        self.assertNotContains(page, inactive.name)

        res = self.client.post("/admin/inventory/stockreceipt/add/", {
            "warehouse": self.warehouse.pk, "supplier": inactive.pk, "number": "X-1",
            "items-TOTAL_FORMS": "0", "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
        })
        self.assertEqual(res.status_code, 200)  # form shown again with an error, nothing saved
        self.assertIn("supplier", res.context["adminform"].form.errors)
        self.assertFalse(StockReceipt.objects.filter(number="X-1").exists())
