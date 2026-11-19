"""Admin panel and role-based access tests. Run: python manage.py test"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from catalog.models import Product
from orders.models import Order
from orders.services import place_order

User = get_user_model()


class AdminPanelRoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def as_user(self, username):
        self.client.force_login(User.objects.get(username=username))

    def make_order(self, sku="BR-001", qty=2):
        """A real order through the same service as checkout (writes off stock from the warehouse)."""
        product = Product.objects.get(sku=sku)
        order = place_order(User.objects.get(username="customer"), [(product, qty)], "Almaty", "+77001234567")
        return order, product

    # --- who can open what ---
    def test_customer_cannot_open_admin(self):
        self.as_user("customer")
        res = self.client.get("/admin/")
        self.assertEqual(res.status_code, 302)  # sent to the admin login page
        self.assertIn("/admin/login/", res["Location"])

    def test_manager_can_manage_products_and_orders(self):
        self.as_user("manager")
        self.assertEqual(self.client.get("/admin/catalog/product/").status_code, 200)
        self.assertEqual(self.client.get("/admin/orders/order/").status_code, 200)

    def test_manager_cannot_see_users(self):
        self.as_user("manager")
        self.assertEqual(self.client.get("/admin/accounts/user/").status_code, 403)

    def test_admin_can_see_users(self):
        self.as_user("admin")
        self.assertEqual(self.client.get("/admin/accounts/user/").status_code, 200)

    # --- role changes keep access in sync ---
    def test_changing_role_updates_access(self):
        user = User.objects.get(username="customer")
        user.role = User.Role.MANAGER
        user.save()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.has_perm("catalog.add_product"))
        self.assertFalse(user.has_perm("accounts.view_user"))
        user.role = User.Role.CUSTOMER
        user.save()
        user = User.objects.get(pk=user.pk)  # reload to clear the permission cache
        self.assertFalse(user.is_staff)
        self.assertFalse(user.has_perm("catalog.add_product"))

    # --- CRUD through the admin panel ---
    def test_manager_adds_product_and_it_appears_in_shop(self):
        self.as_user("manager")
        p = Product.objects.first()
        res = self.client.post("/admin/catalog/product/add/", {
            "sku": "SP-001", "category": p.category_id, "brand": p.brand_id, "price": "2500",
            "is_active": "on", "name_en": "Spark plug", "name_ru": "Свеча зажигания",
            "description_en": "", "description_ru": "", "image_url": "",
        })
        self.assertEqual(res.status_code, 302, getattr(res, "context", None) and res.context["adminform"].errors)
        self.client.logout()
        self.assertEqual(self.client.get("/api/products/?search=SP-001").json()["count"], 1)

    def test_low_stock_filter(self):
        self.as_user("manager")
        res = self.client.get("/admin/catalog/product/?stock=out")
        self.assertContains(res, "FL-003")   # seeded with stock 0
        self.assertNotContains(res, "BR-004")  # stock 40

    def test_manager_can_post_stock_receipts(self):
        self.as_user("manager")
        self.assertEqual(self.client.get("/admin/inventory/stockreceipt/").status_code, 200)
        self.assertEqual(self.client.get("/admin/inventory/stockreceipt/add/").status_code, 200)
        self.assertEqual(self.client.get("/admin/inventory/stockmovement/").status_code, 200)

    # --- order actions ---
    def test_mark_as_shipped_action(self):
        order, _ = self.make_order()
        self.as_user("manager")
        self.client.post("/admin/orders/order/", {"action": "mark_shipped", "_selected_action": [order.pk]})
        order.refresh_from_db()
        self.assertEqual(order.status, "shipped")

    def test_cancel_action_returns_stock(self):
        order, product = self.make_order(qty=3)
        before = Product.objects.get(pk=product.pk).stock
        self.as_user("manager")
        self.client.post("/admin/orders/order/", {"action": "mark_cancelled", "_selected_action": [order.pk]})
        self.assertEqual(Product.objects.get(pk=product.pk).stock, before + 3)
        # cancelling twice must not add stock twice
        self.client.post("/admin/orders/order/", {"action": "mark_cancelled", "_selected_action": [order.pk]})
        self.assertEqual(Product.objects.get(pk=product.pk).stock, before + 3)

    def test_shipped_order_cannot_be_cancelled(self):
        order, product = self.make_order()
        self.as_user("manager")
        self.client.post("/admin/orders/order/", {"action": "mark_shipped", "_selected_action": [order.pk]})
        stock = Product.objects.get(pk=product.pk).stock
        self.client.post("/admin/orders/order/", {"action": "mark_cancelled", "_selected_action": [order.pk]})
        order.refresh_from_db()
        self.assertEqual(order.status, "shipped")  # refused: goods already left the warehouse
        self.assertEqual(Product.objects.get(pk=product.pk).stock, stock)

    def test_customer_sees_status_set_by_manager(self):
        order, _ = self.make_order()
        self.as_user("manager")
        self.client.post("/admin/orders/order/", {"action": "mark_shipped", "_selected_action": [order.pk]})
        self.client.logout()
        token = self.client.post("/api/auth/login/", {"username": "customer", "password": "demo12345"}).json()["access"]
        orders = self.client.get("/api/orders/", HTTP_AUTHORIZATION=f"Bearer {token}").json()["results"]
        self.assertEqual(orders[0]["status"], "shipped")
