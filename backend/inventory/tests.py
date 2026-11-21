from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.test import TestCase

from catalog.models import Product
from orders.models import Order
from orders.services import place_order

from .constants import MAIN_WAREHOUSE_NAME
from .models import StockMovement, StockReceipt, StockReceiptItem, Warehouse, WarehouseStock
from .services import InsufficientStockError, receive_stock


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
        self.assertEqual(StockReceipt.objects.count(), 1)
        self.assert_balances_match_journal()

    def test_seed_reset_works_with_orders_and_stock(self):
        call_command("seed_warehouse", stdout=StringIO())

        call_command("seed", "--reset", stdout=StringIO())

        from catalog.management.commands.seed_data import PRODUCTS
        self.assertEqual(Product.objects.count(), len(PRODUCTS))
        self.assertEqual(Order.objects.count(), 0)
        self.assert_balances_match_journal()


class SeedWarehouseTests(JournalAssertions, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_warehouse", stdout=StringIO())

    def stock(self, sku):
        return WarehouseStock.objects.get(warehouse__name=MAIN_WAREHOUSE_NAME, product__sku=sku).quantity

    def test_balances_match_journal(self):
        self.assert_balances_match_journal()

    def test_journal_has_receipt_sale_and_return(self):
        types = set(StockMovement.objects.values_list("movement_type", flat=True))
        self.assertTrue({"receipt", "sale", "return"} <= types, types)

    def test_expected_balances(self):
        self.assertEqual(self.stock("WH-001"), 37)  # 40 received - 3 sold - 2 sold + 2 returned
        self.assertEqual(self.stock("WH-002"), 2)   # low stock
        self.assertEqual(self.stock("WH-003"), 0)   # zero stock
        self.assertEqual(self.stock("BR-001"), 24)  # 15 opening + 10 received - 1 sold
        self.assertEqual(self.stock("OIL-001"), 34)  # 30 opening + 6 received - 2 sold
        self.assertEqual(
            sorted(Order.objects.values_list("status", flat=True)),
            ["cancelled", "delivered", "paid"],
        )
        self.assertEqual(StockReceipt.objects.filter(posted_at__isnull=False).count(), 3)

    def test_rerun_creates_no_duplicates(self):
        before = self.snapshot()
        call_command("seed_warehouse", stdout=StringIO())
        self.assertEqual(self.snapshot(), before)

    def test_low_stock_product_cannot_be_oversold(self):
        customer = User.objects.get(username="customer")
        with self.assertRaises(InsufficientStockError):
            with transaction.atomic():
                place_order(customer, [(Product.objects.get(sku="WH-002"), 3)], "Almaty", "+77001234567")
        self.assertEqual(self.stock("WH-002"), 2)

    def test_zero_stock_product_cannot_be_sold(self):
        customer = User.objects.get(username="customer")
        with self.assertRaises(InsufficientStockError):
            with transaction.atomic():
                place_order(customer, [(Product.objects.get(sku="WH-003"), 1)], "Almaty", "+77001234567")
