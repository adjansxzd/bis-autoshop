"""API tests for the main user process. Run: python manage.py test"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APITestCase

from catalog.models import Product

User = get_user_model()


class ShopFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def login(self, username, password="demo12345"):
        res = self.client.post("/api/auth/login/", {"username": username, "password": password})
        self.assertEqual(res.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")

    def test_health(self):
        self.assertEqual(self.client.get("/api/health/").data["status"], "ok")

    def test_catalog_is_public_and_paginated(self):
        res = self.client.get("/api/products/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 21)
        self.assertEqual(len(res.data["results"]), 12)

    def test_filter_by_category_and_car(self):
        res = self.client.get("/api/products/?category=brakes")
        self.assertTrue(all(p["category"]["slug"] == "brakes" for p in res.data["results"]))
        car_id = res.data["results"][0]["compatible_cars"][0]["id"]
        res = self.client.get(f"/api/products/?car={car_id}")
        self.assertTrue(all(any(c["id"] == car_id for c in p["compatible_cars"]) for p in res.data["results"]))

    def test_global_search_returns_three_entity_types(self):
        res = self.client.get("/api/search/?q=toyota")
        self.assertGreater(len(res.data["products"]), 0)
        self.assertGreater(len(res.data["cars"]), 0)
        self.assertIn("categories", res.data)

    def test_register_new_user(self):
        res = self.client.post("/api/auth/register/", {"username": "aibek", "email": "aibek@test.kz", "password": "Strong!pass77"})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(User.objects.get(username="aibek").role, "customer")

    def test_customer_cannot_create_product(self):
        self.login("customer")
        res = self.client.post("/api/products/", {"sku": "X", "name_en": "X", "name_ru": "X", "price": 1, "category_id": 1, "brand_id": 1})
        self.assertEqual(res.status_code, 403)

    def test_manager_can_create_product(self):
        self.login("manager")
        p = Product.objects.first()
        res = self.client.post("/api/products/", {
            "sku": "NEW-1", "name_en": "Spark plug", "name_ru": "Свеча зажигания", "price": "2500",
            "stock": 10, "category_id": p.category_id, "brand_id": p.brand_id,
        })
        self.assertEqual(res.status_code, 201, res.data)

    def test_cart_to_order_flow_reduces_stock(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-001")
        start_stock = product.stock
        self.assertEqual(self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 2}).status_code, 201)
        self.assertEqual(float(self.client.get("/api/cart/").data["total"]), float(product.price * 2))

        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty, Tole bi 59", "phone": "+77001234567"})
        self.assertEqual(res.status_code, 201, res.data)
        product.refresh_from_db()
        self.assertEqual(product.stock, start_stock - 2)
        self.assertEqual(len(self.client.get("/api/cart/").data["items"]), 0)

    def test_cannot_add_more_than_stock(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-002")
        res = self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": product.stock + 1})
        self.assertEqual(res.status_code, 400)

    def test_checkout_empty_cart_fails(self):
        self.login("customer")
        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
        self.assertEqual(res.status_code, 400)
