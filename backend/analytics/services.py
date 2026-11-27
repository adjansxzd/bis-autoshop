"""
Sales analytics (read-only, computed from orders — no tables of its own).

Revenue counts every order that is not cancelled. Money is the order total (parts + delivery);
"parts revenue" per product/category uses quantity × unit price of the order lines.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from catalog.models import Product
from orders.models import Order, OrderItem

LOW_STOCK = 5  # same limit as the "low stock" highlight in the products list
LINE_TOTAL = ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=14, decimal_places=2))


def report(days=30):
    """Everything the analytics page and API show, for the last `days` days (0 = all time)."""
    now = timezone.now()
    orders = Order.objects.all()
    if days:
        orders = orders.filter(created_at__gte=now - timedelta(days=days))
    sold = orders.exclude(status=Order.Status.CANCELLED)
    lines = OrderItem.objects.filter(order__in=sold)

    revenue = sold.aggregate(s=Sum("total"))["s"] or Decimal("0")
    count = sold.count()
    by_status = {s: 0 for s, _label in Order.Status.choices}
    for row in orders.values("status").annotate(n=Count("id")):
        by_status[row["status"]] = row["n"]

    # one point per day, also for days without orders, so the chart has no gaps
    span = days or max(1, (now.date() - (orders.order_by("created_at").first().created_at.date() if orders.exists() else now.date())).days + 1)
    start = now.date() - timedelta(days=span - 1)
    per_day = {r["day"]: r for r in sold.annotate(day=TruncDate("created_at")).values("day").annotate(n=Count("id"), s=Sum("total"))}
    daily = []
    for i in range(span):
        day = start + timedelta(days=i)
        row = per_day.get(day, {})
        daily.append({"date": day.isoformat(), "orders": row.get("n", 0), "revenue": row.get("s") or Decimal("0")})

    top = (lines.values("product_id", "product__sku", "product__name_en", "product__name_ru")
           .annotate(sold_qty=Sum("quantity"), line_revenue=Sum(LINE_TOTAL)).order_by("-sold_qty", "-line_revenue")[:5])
    categories = (lines.values("product__category__name_en", "product__category__name_ru")
                  .annotate(sold_qty=Sum("quantity"), line_revenue=Sum(LINE_TOTAL)).order_by("-line_revenue"))

    def split(field):
        return {r[field]: {"orders": r["n"], "revenue": r["s"] or Decimal("0")}
                for r in sold.values(field).annotate(n=Count("id"), s=Sum("total"))}

    customers = get_user_model().objects.filter(role="customer")
    new_customers = customers.filter(date_joined__gte=now - timedelta(days=days)).count() if days else customers.count()

    return {
        "days": days,
        "revenue": revenue,
        "orders": count,
        "average_order": (revenue / count).quantize(Decimal("1")) if count else Decimal("0"),
        "cancelled": by_status[Order.Status.CANCELLED],
        "items_sold": lines.aggregate(n=Sum("quantity"))["n"] or 0,
        "new_customers": new_customers,
        "by_status": by_status,
        "by_payment": split("payment_method"),
        "by_delivery": split("delivery_method"),
        "daily": daily,
        "top_products": [
            {"id": r["product_id"], "sku": r["product__sku"], "name_en": r["product__name_en"], "name_ru": r["product__name_ru"],
             "quantity": r["sold_qty"], "revenue": r["line_revenue"]} for r in top
        ],
        "by_category": [
            {"name_en": r["product__category__name_en"], "name_ru": r["product__category__name_ru"],
             "quantity": r["sold_qty"], "revenue": r["line_revenue"]} for r in categories
        ],
        "low_stock": list(Product.objects.filter(is_active=True, stock__lte=LOW_STOCK).order_by("stock", "sku")
                          .values("id", "sku", "name_en", "name_ru", "stock")),
    }
