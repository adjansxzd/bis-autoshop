from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from catalog.models import Product

from .models import StockMovement, StockReceipt, StockReceiptItem, Warehouse, WarehouseStock
from .services import receive_stock
from .signals import MAIN_WAREHOUSE_NAME


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