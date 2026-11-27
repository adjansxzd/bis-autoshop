from django.contrib import admin
from django.shortcuts import render
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from orders.models import Order

from .services import LOW_STOCK, report

PERIODS = [(7, "7 days"), (30, "30 days"), (90, "90 days"), (0, "All time")]


def _days(request):
    try:
        days = int(request.GET.get("days", 30))
    except ValueError:
        days = 30
    return days if days in dict(PERIODS) else 30


@extend_schema(parameters=[OpenApiParameter("days", int, description="7, 30, 90 or 0 (all time)")])
@api_view(["GET"])
@permission_classes([IsAdminUser])  # managers and admins only
def summary(request):
    """GET /api/analytics/summary/?days=30 — revenue, orders, top parts, categories, low stock (staff only)."""
    return Response(report(_days(request)))


def admin_page(request):
    """Admin panel → "Sales analytics": the same report as a page with simple bar charts."""
    days = _days(request)
    data = report(days)
    peak = max([d["revenue"] for d in data["daily"]] + [1])
    for d in data["daily"]:
        d["pct"] = round(float(d["revenue"]) / float(peak) * 100, 1)
    cat_peak = max([c["revenue"] for c in data["by_category"]] + [1])
    for c in data["by_category"]:
        c["pct"] = round(float(c["revenue"]) / float(cat_peak) * 100, 1)
    labels = dict(Order.Status.choices)
    statuses = [{"key": k, "label": labels[k], "n": n} for k, n in data["by_status"].items()]
    pay_labels, del_labels = dict(Order.Payment.choices), dict(Order.Delivery.choices)
    context = {
        **admin.site.each_context(request),
        "title": "Sales analytics",
        "r": data,
        "days": days,
        "periods": PERIODS,
        "statuses": statuses,
        "payments": [{"label": pay_labels.get(k, k), **v} for k, v in data["by_payment"].items()],
        "deliveries": [{"label": del_labels.get(k, k), **v} for k, v in data["by_delivery"].items()],
        "low_limit": LOW_STOCK,
        "first_day": data["daily"][0]["date"] if data["daily"] else "",
        "last_day": data["daily"][-1]["date"] if data["daily"] else "",
    }
    return render(request, "admin/analytics/report.html", context)
