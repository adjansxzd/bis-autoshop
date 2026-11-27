"""Catalog: photos, specs, price range, rating sort, reviews, order search. Run: python manage.py test"""
import io

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from PIL import Image
from rest_framework.test import APITestCase

from catalog.models import Product, Review
from orders.models import Order
from orders.services import change_order_status, place_order

User = get_user_model()


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)
        cls.buyer = User.objects.create_user("buyer", "buyer@test.kz", "Strong!pass77", first_name="Aibek", last_name="Sadykov")
        cls.product = Product.objects.get(sku="BR-003")  # no demo reviews on it
        place_order(cls.buyer, [(cls.product, 1)], "Almaty", "+77001234567")

    def token(self, username, password="Strong!pass77"):
        res = self.client.post("/api/auth/login/", {"username": username, "password": password})
        return {"HTTP_AUTHORIZATION": f"Bearer {res.json()['access']}"}

    def post_review(self, headers, rating=5, text="Great", product=None):
        product = product or self.product
        return self.client.post(f"/api/products/{product.id}/reviews/", {"rating": rating, "text": text},
                                content_type="application/json", **headers)

    # --- product details ---
    def test_product_has_specs_oem_and_rating(self):
        p = Product.objects.get(sku="BR-002")
        data = self.client.get(f"/api/products/{p.id}/").json()
        self.assertTrue(data["specs"] and "value" in data["specs"][0])
        self.assertIn("43512", data["oem_numbers"])
        reviewed = self.client.get(f"/api/products/{Product.objects.get(sku='BR-001').id}/").json()
        self.assertEqual(reviewed["rating_count"], 3)
        self.assertAlmostEqual(reviewed["rating_avg"], 4.7, places=1)

    def test_search_by_oem_number(self):
        res = self.client.get("/api/products/?search=90915-YZZE1").json()
        self.assertEqual([p["sku"] for p in res["results"]], ["FL-004"])

    @override_settings(MEDIA_ROOT="/tmp/claude-test-media")
    def test_photo_url_is_absolute(self):
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), "red").save(buf, "PNG")
        p = Product.objects.get(sku="BR-002")
        p.image.save("BR-002.png", SimpleUploadedFile("BR-002.png", buf.getvalue()), save=True)
        url = self.client.get(f"/api/products/{p.id}/").json()["image"]
        self.assertTrue(url.startswith("http://testserver/media/products/"), url)

    # --- price range + sorting ---
    def test_price_range_and_filter(self):
        rng = self.client.get("/api/products/price-range/").json()
        prices = [float(p.price) for p in Product.objects.filter(is_active=True)]
        self.assertEqual((float(rng["min"]), float(rng["max"])), (min(prices), max(prices)))
        brakes = self.client.get("/api/products/price-range/?category=brakes").json()
        self.assertGreaterEqual(float(brakes["min"]), float(rng["min"]))
        res = self.client.get("/api/products/?min_price=10000&max_price=30000&page_size=100").json()
        self.assertTrue(all(10000 <= float(p["price"]) <= 30000 for p in res["results"]))

    def test_sort_by_rating(self):
        res = self.client.get("/api/products/?ordering=-rating_avg").json()["results"]
        rated = [p["rating_avg"] for p in res if p["rating_avg"] is not None]
        self.assertEqual(rated, sorted(rated, reverse=True))
        self.assertIsNotNone(res[0]["rating_avg"])

    # --- reviews ---
    def test_reviews_are_public_with_summary(self):
        p = Product.objects.get(sku="BR-001")
        data = self.client.get(f"/api/products/{p.id}/reviews/").json()
        self.assertEqual(data["summary"]["count"], 3)
        self.assertEqual(sum(data["summary"]["distribution"].values()), 3)
        self.assertFalse(data["can_review"])  # anonymous
        self.assertNotIn("@", data["results"][0]["author"])  # no emails shown

    def test_only_buyers_can_review_once(self):
        call_command("seed", verbosity=0)
        stranger = self.token("customer", "demo12345")
        self.assertEqual(self.post_review(stranger).status_code, 403)          # never bought it
        self.assertEqual(self.post_review({}).status_code, 401)                # not signed in
        buyer = self.token("buyer")
        self.assertTrue(self.client.get(f"/api/products/{self.product.id}/reviews/", **buyer).json()["can_review"])
        self.assertEqual(self.post_review(buyer, rating=6).status_code, 400)   # 1..5 only
        res = self.post_review(buyer, rating=4, text="Fits my Rio")
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.json()["author"], "Aibek S.")
        self.assertEqual(self.post_review(buyer).status_code, 400)             # only one review
        data = self.client.get(f"/api/products/{self.product.id}/reviews/", **buyer).json()
        self.assertFalse(data["can_review"])
        self.assertEqual(data["my_review"]["rating"], 4)

    def test_cancelled_order_does_not_allow_review(self):
        user = User.objects.create_user("cancel", "c@test.kz", "Strong!pass77")
        product = Product.objects.get(sku="CO-002")
        order = place_order(user, [(product, 1)], "Almaty", "+77001234567")
        change_order_status(order, Order.Status.CANCELLED, user)
        self.assertEqual(self.post_review(self.token("cancel"), product=product).status_code, 403)

    def test_edit_own_review_but_not_others(self):
        buyer = self.token("buyer")
        review_id = self.post_review(buyer, rating=3).json()["id"]
        res = self.client.patch(f"/api/reviews/{review_id}/", {"rating": 5}, content_type="application/json", **buyer)
        self.assertEqual(res.json()["rating"], 5)
        other = self.token("customer", "demo12345")
        self.assertEqual(self.client.patch(f"/api/reviews/{review_id}/", {"rating": 1},
                                           content_type="application/json", **other).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/reviews/{review_id}/", **other).status_code, 404)

    def test_manager_can_delete_any_review(self):
        review = Review.objects.first()
        self.assertEqual(self.client.delete(f"/api/reviews/{review.id}/", **self.token("manager", "demo12345")).status_code, 204)
        self.client.force_login(User.objects.get(username="manager"))
        self.assertEqual(self.client.get("/admin/catalog/review/").status_code, 200)

    # --- order search ("My orders") ---
    def test_search_my_orders(self):
        buyer = self.token("buyer")
        second = place_order(self.buyer, [(Product.objects.get(sku="OIL-001"), 1)], "Astana", "+77001234567")
        by_product = self.client.get("/api/orders/?q=Castrol", **buyer).json()
        self.assertEqual([o["id"] for o in by_product["results"]], [second.id])
        by_number = self.client.get(f"/api/orders/?q=%23{second.id}", **buyer).json()
        self.assertEqual(by_number["count"], 1)
        by_status = self.client.get("/api/orders/?status=new", **buyer).json()
        self.assertEqual(by_status["count"], 2)
        # other customers' orders never appear
        self.assertEqual(self.client.get("/api/orders/?q=Castrol", **self.token("customer", "demo12345")).json()["count"], 0)


class Product3DModelTests(APITestCase):
    """Optional 3D model per product: seeded for a few parts, only real .glb files are accepted."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def test_seeded_parts_have_a_3d_model_in_the_api(self):
        product = Product.objects.get(sku="BR-002")
        data = self.client.get(f"/api/products/{product.id}/").data
        self.assertTrue(data["model_3d"].endswith(".glb"))
        plain = Product.objects.get(sku="BR-001")
        self.assertFalse(self.client.get(f"/api/products/{plain.id}/").data["model_3d"])

    def test_only_binary_gltf_is_accepted(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile
        from catalog.models import validate_glb
        validate_glb(SimpleUploadedFile("ok.glb", b"glTF" + b"\x00" * 20))
        with self.assertRaises(ValidationError):
            validate_glb(SimpleUploadedFile("fake.glb", b"<html>not a model</html>"))
