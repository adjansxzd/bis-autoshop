"""API tests for the main user process. Run: python manage.py test"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APITestCase

from catalog.models import Product
from inventory.models import StockMovement, Warehouse, WarehouseStock
from inventory.constants import MAIN_WAREHOUSE_NAME
from orders.models import Cart, CartItem, Order, OrderItem

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
        self.assertEqual(res.data["count"], Product.objects.filter(is_active=True).count())
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
        res = self.client.post("/api/auth/register/", {"username": "aibek", "email": "aibek@test.kz", "password": "Strong!pass77", "password2": "Strong!pass77"})
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
        warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        warehouse_stock = WarehouseStock.objects.get(warehouse=warehouse, product=product)
        self.assertEqual(self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 2}).status_code, 201)
        self.assertEqual(float(self.client.get("/api/cart/").data["total"]), float(product.price * 2))

        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty, Tole bi 59", "phone": "+77001234567"})
        self.assertEqual(res.status_code, 201, res.data)
        product.refresh_from_db()
        warehouse_stock.refresh_from_db()
        self.assertEqual(product.stock, start_stock - 2)
        self.assertEqual(warehouse_stock.quantity, start_stock - 2)
        order_item = OrderItem.objects.get(order_id=res.data["id"], product=product)
        self.assertEqual(order_item.warehouse, warehouse)
        movement = StockMovement.objects.get(order_id=res.data["id"], movement_type=StockMovement.Type.SALE)
        self.assertEqual(movement.quantity, 2)
        self.assertEqual(len(self.client.get("/api/cart/").data["items"]), 0)

    def test_checkout_insufficient_warehouse_stock_rolls_back(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-001")
        warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        stock = WarehouseStock.objects.get(warehouse=warehouse, product=product)
        stock.quantity = 1
        stock.save(update_fields=["quantity"])
        cart, _ = Cart.objects.get_or_create(user=User.objects.get(username="customer"))
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        order_count = Order.objects.count()
        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})

        self.assertEqual(res.status_code, 400)
        self.assertIn("Not enough stock", str(res.data))
        self.assertEqual(Order.objects.count(), order_count)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, 1)
        self.assertFalse(StockMovement.objects.filter(movement_type=StockMovement.Type.SALE).exists())
        self.assertEqual(CartItem.objects.filter(cart=cart).count(), 1)

    def test_cancelling_order_returns_stock(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-001")
        warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        stock = WarehouseStock.objects.get(warehouse=warehouse, product=product)
        starting_quantity = stock.quantity
        self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 2})
        order_res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
        self.assertEqual(order_res.status_code, 201, order_res.data)

        self.client.credentials()
        self.login("manager")
        res = self.client.patch(f"/api/orders/{order_res.data['id']}/status/", {"status": "cancelled"})

        self.assertEqual(res.status_code, 200, res.data)
        stock.refresh_from_db()
        product.refresh_from_db()
        self.assertEqual(stock.quantity, starting_quantity)
        self.assertEqual(product.stock, starting_quantity)
        movement = StockMovement.objects.get(order_id=order_res.data["id"], movement_type=StockMovement.Type.RETURN)
        self.assertEqual(movement.quantity, 2)
        self.assertEqual(movement.warehouse, warehouse)

    def test_repeated_cancellation_does_not_return_stock_twice(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-001")
        warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        stock = WarehouseStock.objects.get(warehouse=warehouse, product=product)
        starting_quantity = stock.quantity
        self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 2})
        order_res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
        self.assertEqual(order_res.status_code, 201, order_res.data)

        self.client.credentials()
        self.login("manager")
        url = f"/api/orders/{order_res.data['id']}/status/"
        first_res = self.client.patch(url, {"status": "cancelled"})
        second_res = self.client.patch(url, {"status": "cancelled"})

        self.assertEqual(first_res.status_code, 200, first_res.data)
        self.assertEqual(second_res.status_code, 200, second_res.data)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, starting_quantity)
        self.assertEqual(
            StockMovement.objects.filter(order_id=order_res.data["id"], movement_type=StockMovement.Type.RETURN).count(),
            1,
        )

    def test_cannot_add_more_than_stock(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-002")
        res = self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": product.stock + 1})
        self.assertEqual(res.status_code, 400)

    def test_cart_availability_uses_warehouse_stock(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-001")
        warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        WarehouseStock.objects.filter(warehouse=warehouse, product=product).update(quantity=1)

        res = self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 2})

        self.assertEqual(res.status_code, 400)
        self.assertIn("Only 1 in stock", str(res.data))

    def test_in_stock_filter_uses_warehouse_stock(self):
        product = Product.objects.get(sku="BR-001")
        warehouse = Warehouse.objects.get(name=MAIN_WAREHOUSE_NAME)
        WarehouseStock.objects.filter(warehouse=warehouse, product=product).update(quantity=0)

        res = self.client.get("/api/products/?in_stock=false&search=Front%20brake%20pads")

        self.assertEqual(res.status_code, 200)
        self.assertIn(product.id, [item["id"] for item in res.data["results"]])

    def test_checkout_empty_cart_fails(self):
        self.login("customer")
        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
        self.assertEqual(res.status_code, 400)

    def test_user_can_place_several_orders(self):
        self.login("customer")
        for sku in ("BR-001", "OIL-001"):
            product = Product.objects.get(sku=sku)
            self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 1})
            res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
            self.assertEqual(res.status_code, 201)
        self.assertEqual(self.client.get("/api/orders/").data["count"], 2)

    def test_one_order_can_hold_several_products(self):
        self.login("customer")
        for sku in ("BR-001", "FL-001", "LT-001"):
            self.client.post("/api/cart/items/", {"product_id": Product.objects.get(sku=sku).id, "quantity": 2})
        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
        self.assertEqual(len(res.data["items"]), 3)

    def test_out_of_stock_product_cannot_be_added(self):
        self.login("customer")
        product = Product.objects.get(sku="FL-003")  # seeded with stock 0
        res = self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 1})
        self.assertEqual(res.status_code, 400)

    def test_changing_quantity_above_stock_is_rejected(self):
        self.login("customer")
        product = Product.objects.get(sku="BR-002")
        item = self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 1}).data
        res = self.client.patch(f"/api/cart/items/{item['id']}/", {"quantity": product.stock + 1})
        self.assertEqual(res.status_code, 400)
        res = self.client.patch(f"/api/cart/items/{item['id']}/", {"quantity": product.stock})
        self.assertEqual(res.status_code, 200)

    def test_cancelling_order_restores_product_total(self):
        # Was a second "test_cancelling_order_returns_stock" that silently replaced the first one.
        product = Product.objects.get(sku="BR-003")
        start = product.stock
        self.login("customer")
        self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": 3})
        order = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"}).data
        self.login("manager")
        self.client.patch(f"/api/orders/{order['id']}/status/", {"status": "cancelled"})
        product.refresh_from_db()
        self.assertEqual(product.stock, start)

    def test_customer_sees_only_own_orders(self):
        User.objects.create_user("other", "o@test.kz", "Strong!pass77")
        self.login("other", "Strong!pass77")
        self.client.post("/api/cart/items/", {"product_id": Product.objects.get(sku="BR-001").id, "quantity": 1})
        self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
        self.login("customer")
        self.assertEqual(self.client.get("/api/orders/").data["count"], 0)

    # --- stock rules -------------------------------------------------------

    def place_order(self, sku="BR-001", quantity=2):
        """Checkout as customer, then log in as manager. Returns the order id."""
        self.login("customer")
        product = Product.objects.get(sku=sku)
        self.assertEqual(self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": quantity}).status_code, 201)
        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})
        self.assertEqual(res.status_code, 201, res.data)
        self.client.credentials()
        self.login("manager")
        return res.data["id"]

    def set_status(self, order_id, status):
        return self.client.patch(f"/api/orders/{order_id}/status/", {"status": status})

    def main_stock(self, sku):
        return WarehouseStock.objects.get(warehouse__name=MAIN_WAREHOUSE_NAME, product__sku=sku).quantity

    def test_shortage_in_one_line_rolls_back_whole_checkout(self):
        self.login("customer")
        ok_product = Product.objects.get(sku="BR-001")
        short_product = Product.objects.get(sku="BR-002")
        WarehouseStock.objects.filter(product=short_product).update(quantity=1)
        cart, _ = Cart.objects.get_or_create(user=User.objects.get(username="customer"))
        CartItem.objects.create(cart=cart, product=ok_product, quantity=1)
        CartItem.objects.create(cart=cart, product=short_product, quantity=2)
        start = self.main_stock("BR-001")

        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})

        self.assertEqual(res.status_code, 400)
        self.assertIn("Available: 1", str(res.data))
        self.assertEqual(self.main_stock("BR-001"), start)  # first line was written off, then rolled back
        self.assertEqual(Order.objects.count(), 0)
        self.assertFalse(StockMovement.objects.filter(movement_type=StockMovement.Type.SALE).exists())

    def test_checkout_product_without_warehouse_row_fails(self):
        product = Product.objects.get(sku="BR-001")
        WarehouseStock.objects.filter(product=product).delete()
        self.login("customer")
        cart, _ = Cart.objects.get_or_create(user=User.objects.get(username="customer"))
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        res = self.client.post("/api/orders/checkout/", {"shipping_address": "Almaty", "phone": "+77001234567"})

        self.assertEqual(res.status_code, 400)
        self.assertIn("Available: 0", str(res.data))

    def test_cancel_paid_order_returns_stock(self):
        start = self.main_stock("BR-001")
        order_id = self.place_order()
        self.assertEqual(self.set_status(order_id, "paid").status_code, 200)
        self.assertEqual(self.set_status(order_id, "cancelled").status_code, 200)
        self.assertEqual(self.main_stock("BR-001"), start)

    def test_cancel_after_shipping_is_rejected(self):
        start = self.main_stock("BR-001")
        order_id = self.place_order()
        for status in ("shipped", "delivered"):
            self.assertEqual(self.set_status(order_id, status).status_code, 200)
            res = self.set_status(order_id, "cancelled")
            self.assertEqual(res.status_code, 400, res.data)
        self.assertEqual(self.main_stock("BR-001"), start - 2)  # nothing returned
        self.assertFalse(StockMovement.objects.filter(order_id=order_id, movement_type=StockMovement.Type.RETURN).exists())
        self.assertEqual(Order.objects.get(pk=order_id).status, Order.Status.DELIVERED)

    def test_status_cannot_go_back(self):
        order_id = self.place_order()
        self.assertEqual(self.set_status(order_id, "shipped").status_code, 200)
        self.assertEqual(self.set_status(order_id, "new").status_code, 400)
        self.assertEqual(Order.objects.get(pk=order_id).status, Order.Status.SHIPPED)

    def test_cancelled_order_cannot_be_reopened(self):
        start = self.main_stock("BR-001")
        order_id = self.place_order()
        self.set_status(order_id, "cancelled")
        res = self.set_status(order_id, "new")
        self.assertEqual(res.status_code, 400)
        self.assertIn("cannot be reopened", str(res.data))
        self.assertEqual(self.main_stock("BR-001"), start)

    def test_product_stock_is_read_only_in_api(self):
        self.login("manager")
        product = Product.objects.get(sku="BR-001")
        start = product.stock
        res = self.client.patch(f"/api/products/{product.id}/", {"stock": 999})
        self.assertEqual(res.status_code, 200, res.data)
        product.refresh_from_db()
        self.assertEqual(product.stock, start)
        self.assertEqual(self.main_stock("BR-001"), start)

    def test_new_product_gets_empty_main_warehouse_row(self):
        self.login("manager")
        p = Product.objects.first()
        res = self.client.post("/api/products/", {
            "sku": "NEW-2", "name_en": "Spark plug", "name_ru": "Свеча", "price": "2500",
            "stock": 10, "category_id": p.category_id, "brand_id": p.brand_id,
        })
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["stock"], 0)  # stock in the request is ignored
        self.assertEqual(self.main_stock("NEW-2"), 0)

    def admin_change_status(self, order_id, status):
        order = Order.objects.get(pk=order_id)
        item = order.items.get()
        self.client.force_login(User.objects.get(username="admin"))
        return self.client.post(f"/admin/orders/order/{order_id}/change/", {
            "status": status, "shipping_address": order.shipping_address, "phone": order.phone,
            "items-TOTAL_FORMS": "1", "items-INITIAL_FORMS": "1",
            "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
            "items-0-id": str(item.pk), "items-0-order": str(order_id),
        })

    def test_cancel_in_django_admin_returns_stock(self):
        start = self.main_stock("BR-001")
        order_id = self.place_order()

        res = self.admin_change_status(order_id, "cancelled")

        self.assertEqual(res.status_code, 302)  # saved, redirected to the list
        self.assertEqual(Order.objects.get(pk=order_id).status, Order.Status.CANCELLED)
        self.assertEqual(self.main_stock("BR-001"), start)
        self.assertEqual(StockMovement.objects.filter(order_id=order_id, movement_type=StockMovement.Type.RETURN).count(), 1)

    def test_django_admin_rejects_cancel_after_shipping(self):
        order_id = self.place_order()
        self.set_status(order_id, "shipped")

        res = self.admin_change_status(order_id, "cancelled")

        self.assertEqual(res.status_code, 200)  # form re-rendered with an error
        self.assertEqual(Order.objects.get(pk=order_id).status, Order.Status.SHIPPED)
        self.assertFalse(StockMovement.objects.filter(order_id=order_id, movement_type=StockMovement.Type.RETURN).exists())


class OrderProcessTests(APITestCase):
    """Checkout with delivery & payment, demo payment, cancellation by the customer, history, reorder."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)

    def login(self, username="customer", password="demo12345"):
        token = self.client.post("/api/auth/login/", {"username": username, "password": password}).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def checkout(self, sku="BR-003", qty=1, **body):
        product = Product.objects.get(sku=sku)
        self.client.post("/api/cart/items/", {"product_id": product.id, "quantity": qty})
        data = {"shipping_address": "Almaty, Tole bi 59", "phone": "+77001234567"}
        data.update(body)
        return self.client.post("/api/orders/checkout/", data, format="json")

    def test_courier_fee_and_free_delivery(self):
        self.login()
        cheap = self.checkout("BR-003", 1, delivery_method="courier").data          # 17 900 ₸
        self.assertEqual(float(cheap["delivery_cost"]), 1500)
        self.assertEqual(float(cheap["total"]), 17900 + 1500)
        big = self.checkout("TR-003", 1, delivery_method="courier").data            # 79 900 ₸ ≥ 50 000
        self.assertEqual(float(big["delivery_cost"]), 0)

    def test_pickup_needs_no_address_and_is_free(self):
        self.login()
        res = self.checkout("BR-003", 1, delivery_method="pickup", shipping_address="")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(float(res.data["delivery_cost"]), 0)
        self.assertIn("AutoShop", res.data["shipping_address"])

    def test_courier_requires_address(self):
        self.login()
        self.assertEqual(self.checkout("BR-003", 1, delivery_method="courier", shipping_address="").status_code, 400)

    def test_delivery_options_endpoint(self):
        data = self.client.get("/api/orders/delivery-options/").data
        self.assertEqual(float(data["courier_price"]), 1500)

    def test_card_payment_flow_with_history(self):
        self.login()
        order = self.checkout(payment_method="card").data
        self.assertTrue(order["can_pay"])
        paid = self.client.post(f"/api/orders/{order['id']}/pay/").data
        self.assertEqual(paid["status"], "paid")
        self.assertIsNotNone(paid["paid_at"])
        self.assertEqual([e["status"] for e in paid["events"]], ["new", "paid"])
        self.assertEqual(self.client.post(f"/api/orders/{order['id']}/pay/").status_code, 400)  # no double payment

    def test_cash_order_cannot_be_paid_online(self):
        self.login()
        order = self.checkout(payment_method="cash").data
        self.assertFalse(order["can_pay"])
        self.assertEqual(self.client.post(f"/api/orders/{order['id']}/pay/").status_code, 400)

    def test_customer_cancels_and_stock_returns(self):
        self.login()
        product = Product.objects.get(sku="BR-003")
        before = product.stock
        order = self.checkout("BR-003", 2, payment_method="card").data
        self.client.post(f"/api/orders/{order['id']}/pay/")
        res = self.client.post(f"/api/orders/{order['id']}/cancel/", {"reason": "Ordered by mistake"}, format="json")
        self.assertEqual(res.data["status"], "cancelled")
        self.assertIn("refund", res.data["events"][-1]["note"])
        self.assertEqual(Product.objects.get(pk=product.pk).stock, before)

    def test_cannot_cancel_after_shipping_or_someone_elses_order(self):
        self.login()
        order = self.checkout().data
        self.login("manager")
        self.client.patch(f"/api/orders/{order['id']}/status/", {"status": "shipped"})
        self.login()
        self.assertEqual(self.client.post(f"/api/orders/{order['id']}/cancel/").status_code, 400)
        detail = self.client.get(f"/api/orders/{order['id']}/").data
        self.assertFalse(detail["can_cancel"])
        self.assertEqual(detail["events"][-1]["by"], "shop")
        User.objects.create_user("other", "o@test.kz", "Strong!pass77")
        self.login("other", "Strong!pass77")
        self.assertEqual(self.client.post(f"/api/orders/{order['id']}/cancel/").status_code, 404)

    def test_reorder_puts_items_back_in_cart(self):
        self.login()
        order = self.checkout("BR-003", 2).data
        res = self.client.post(f"/api/orders/{order['id']}/reorder/").data
        self.assertEqual(len(res["added"]), 1)
        self.assertEqual(self.client.get("/api/cart/").data["items"][0]["quantity"], 2)
