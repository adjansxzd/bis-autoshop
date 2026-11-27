"""Admin panel and role-based access tests. Run: python manage.py test"""
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APITestCase

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


class AccountTests(TestCase):
    """Registration, profile, password change, 'My cars' and staying signed in (token refresh)."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def register(self, **overrides):
        data = {"username": "aibek", "email": "aibek@test.kz", "password": "Strong!pass77",
                "password2": "Strong!pass77", "first_name": "Aibek", "phone": "+7 700 123 45 67"}
        data.update(overrides)
        return self.client.post("/api/auth/register/", data, content_type="application/json")

    def auth(self, access):
        return {"HTTP_AUTHORIZATION": f"Bearer {access}"}

    # --- registration ---
    def test_register_returns_tokens_and_customer_role(self):
        res = self.register()
        self.assertEqual(res.status_code, 201, res.content)
        self.assertIn("access", res.json())
        self.assertEqual(res.json()["user"]["role"], "customer")
        me = self.client.get("/api/auth/me/", **self.auth(res.json()["access"]))
        self.assertEqual(me.json()["username"], "aibek")

    def test_register_rejects_bad_input(self):
        self.assertEqual(self.register(password2="Other!pass77").status_code, 400)          # passwords differ
        self.assertEqual(self.register(password="12345678", password2="12345678").status_code, 400)  # weak
        self.assertEqual(self.register(email="customer@autoshop.local").status_code, 400)  # email taken
        self.assertEqual(self.register(username="customer").status_code, 400)             # username taken
        self.assertEqual(self.register(phone="abc").status_code, 400)                      # bad phone

    def test_cannot_register_as_manager(self):
        res = self.register(role="admin")
        self.assertEqual(res.json()["user"]["role"], "customer")

    # --- profile ---
    def test_update_profile_but_not_role(self):
        access = self.register().json()["access"]
        res = self.client.patch("/api/auth/me/", {"address": "Almaty, Tole bi 59", "role": "admin"},
                                content_type="application/json", **self.auth(access))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["address"], "Almaty, Tole bi 59")
        self.assertEqual(res.json()["role"], "customer")

    def test_change_password(self):
        access = self.register().json()["access"]
        bad = self.client.post("/api/auth/password/", {"old_password": "wrong", "new_password": "Newer!pass88"},
                               content_type="application/json", **self.auth(access))
        self.assertEqual(bad.status_code, 400)
        ok = self.client.post("/api/auth/password/", {"old_password": "Strong!pass77", "new_password": "Newer!pass88"},
                              content_type="application/json", **self.auth(access))
        self.assertEqual(ok.status_code, 204)
        self.assertEqual(self.client.post("/api/auth/login/", {"username": "aibek", "password": "Newer!pass88"}).status_code, 200)

    # --- my cars ---
    def test_garage_add_list_delete_only_own(self):
        from catalog.models import CarModel
        camry = CarModel.objects.get(model="Camry")
        access = self.register().json()["access"]
        res = self.client.post("/api/auth/garage/", {"car_id": camry.id, "year": 2020},
                               content_type="application/json", **self.auth(access))
        self.assertEqual(res.status_code, 201, res.content)
        car_id = res.json()["id"]
        # duplicate and impossible year are rejected
        self.assertEqual(self.client.post("/api/auth/garage/", {"car_id": camry.id, "year": 2020},
                                          content_type="application/json", **self.auth(access)).status_code, 400)
        self.assertEqual(self.client.post("/api/auth/garage/", {"car_id": camry.id, "year": 1999},
                                          content_type="application/json", **self.auth(access)).status_code, 400)
        self.assertEqual(len(self.client.get("/api/auth/garage/", **self.auth(access)).json()), 1)
        # another user can't see or delete it
        other = self.client.post("/api/auth/login/", {"username": "customer", "password": "demo12345"}).json()["access"]
        self.assertEqual(self.client.get("/api/auth/garage/", **self.auth(other)).json(), [])
        self.assertEqual(self.client.delete(f"/api/auth/garage/{car_id}/", **self.auth(other)).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/auth/garage/{car_id}/", **self.auth(access)).status_code, 204)

    # --- staying signed in ---
    def test_refresh_token_gives_new_access(self):
        refresh = self.register().json()["refresh"]
        res = self.client.post("/api/auth/refresh/", {"refresh": refresh}, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/", **self.auth(res.json()["access"])).status_code, 200)


class GoogleSignInTests(APITestCase):
    """Sign in with Google: the ID token is checked by google-auth (mocked here), then the user is found or created."""

    CLAIMS = {"email": "Aidana.B@gmail.com", "email_verified": True, "given_name": "Aidana", "family_name": "B"}

    def test_off_when_no_client_id(self):
        with self.settings(GOOGLE_CLIENT_ID=""):
            self.assertEqual(self.client.get("/api/auth/google/config/").data["client_id"], "")
            self.assertEqual(self.client.post("/api/auth/google/", {"credential": "x"}).status_code, 400)

    def test_new_google_user_becomes_customer_and_gets_tokens(self):
        with self.settings(GOOGLE_CLIENT_ID="test-client"), \
                mock.patch("accounts.google.id_token.verify_oauth2_token", return_value=self.CLAIMS) as verify:
            res = self.client.post("/api/auth/google/", {"credential": "token"})
        self.assertEqual(res.status_code, 200, res.data)
        self.assertTrue(res.data["created"])
        self.assertEqual(verify.call_args.args[2], "test-client")  # audience = our client ID
        user = User.objects.get(email="aidana.b@gmail.com")
        self.assertEqual(user.role, "customer")
        self.assertFalse(user.has_usable_password())
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").data["first_name"], "Aidana")

    def test_existing_email_signs_in_same_account(self):
        existing = User.objects.create_user("aidana", "aidana.b@gmail.com", "Strong!pass77")
        with self.settings(GOOGLE_CLIENT_ID="test-client"), \
                mock.patch("accounts.google.id_token.verify_oauth2_token", return_value=self.CLAIMS):
            res = self.client.post("/api/auth/google/", {"credential": "token"})
        self.assertFalse(res.data["created"])
        self.assertEqual(res.data["user"]["id"], existing.id)

    def test_invalid_token_is_rejected(self):
        with self.settings(GOOGLE_CLIENT_ID="test-client"), \
                mock.patch("accounts.google.id_token.verify_oauth2_token", side_effect=ValueError("bad")):
            self.assertEqual(self.client.post("/api/auth/google/", {"credential": "forged"}).status_code, 400)
        self.assertFalse(User.objects.filter(email__iexact="aidana.b@gmail.com").exists())


class SecurityTests(APITestCase):
    """Architecture & Security: brute-force limit, sign-out blacklists the token, refresh tokens rotate, security headers."""

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user("sec", "sec@test.kz", "Strong!pass77")

    def test_login_is_rate_limited(self):
        from django.core.cache import cache
        from rest_framework.throttling import ScopedRateThrottle
        cache.clear()
        with mock.patch.dict(ScopedRateThrottle.THROTTLE_RATES, {"auth": "3/min"}):
            codes = [self.client.post("/api/auth/login/", {"username": "sec", "password": "wrong"}).status_code for _ in range(4)]
        cache.clear()
        self.assertEqual(codes, [401, 401, 401, 429])

    def test_logout_blacklists_refresh_token(self):
        tokens = self.client.post("/api/auth/login/", {"username": "sec", "password": "Strong!pass77"}).data
        self.assertEqual(self.client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}).status_code, 205)
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}).status_code, 401)

    def test_refresh_token_rotates_and_old_one_dies(self):
        tokens = self.client.post("/api/auth/login/", {"username": "sec", "password": "Strong!pass77"}).data
        new = self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}).data
        self.assertIn("refresh", new)
        self.assertNotEqual(new["refresh"], tokens["refresh"])
        self.assertEqual(self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}).status_code, 401)

    def test_security_headers(self):
        res = self.client.get("/api/health/")
        self.assertEqual(res["X-Content-Type-Options"], "nosniff")
        self.assertEqual(res["X-Frame-Options"], "DENY")
        self.assertEqual(res["Referrer-Policy"], "same-origin")

    def test_blocked_user_cannot_sign_in(self):
        User.objects.filter(username="sec").update(is_active=False)
        self.assertEqual(self.client.post("/api/auth/login/", {"username": "sec", "password": "Strong!pass77"}).status_code, 401)

    def test_customer_cannot_change_own_role(self):
        tokens = self.client.post("/api/auth/login/", {"username": "sec", "password": "Strong!pass77"}).data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.client.patch("/api/auth/me/", {"role": "admin"}, format="json")
        self.assertEqual(User.objects.get(username="sec").role, "customer")
