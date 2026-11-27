from django.core.management import call_command
from rest_framework.test import APITestCase

from catalog.models import Product


class AnalyticsTests(APITestCase):
    """Sales analytics: only staff can see it, numbers match the orders placed."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def login(self, username):
        token = self.client.post("/api/auth/login/", {"username": username, "password": "demo12345"}).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def buy(self, sku, qty):
        product = Product.objects.get(sku=sku)
        self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": qty})
        return self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567",
                                                          "delivery_method": "pickup"}, format="json").data

    def test_customer_cannot_see_analytics(self):
        self.assertEqual(self.client.get("/api/analytics/summary/").status_code, 401)
        self.login("customer")
        self.assertEqual(self.client.get("/api/analytics/summary/").status_code, 403)

    def test_numbers_follow_orders_and_cancelled_are_excluded(self):
        self.login("customer")
        first = self.buy("BR-003", 2)
        second = self.buy("TR-003", 1)
        self.client.post(f"/api/orders/{second['id']}/cancel/")
        self.login("manager")
        data = self.client.get("/api/analytics/summary/?days=7").data
        self.assertEqual(data["orders"], 1)
        self.assertEqual(float(data["revenue"]), float(first["total"]))
        self.assertEqual(data["cancelled"], 1)
        self.assertEqual(data["top_products"][0]["sku"], "BR-003")
        self.assertEqual(data["top_products"][0]["quantity"], 2)
        self.assertEqual(len(data["daily"]), 7)

    def test_admin_page_opens_for_staff_only(self):
        self.client.login(username="manager", password="demo12345")
        page = self.client.get("/admin/analytics/?days=30")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Revenue per day")
        self.client.logout()
        self.client.login(username="customer", password="demo12345")
        self.assertEqual(self.client.get("/admin/analytics/").status_code, 302)  # sent to the admin login
