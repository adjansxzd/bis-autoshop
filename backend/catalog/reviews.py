"""Review rules in one place (used by the API and the tests)."""
from django.db.models import Avg, Count, IntegerField, OuterRef, Subquery
from django.db.models.functions import Coalesce

from orders.models import Order, OrderItem

from .models import Review


def has_bought(user, product) -> bool:
    """A customer may review a product only after buying it (any order that was not cancelled)."""
    if not user.is_authenticated:
        return False
    return OrderItem.objects.filter(
        order__user=user, product=product
    ).exclude(order__status=Order.Status.CANCELLED).exists()


def with_ratings(queryset):
    """Annotate products with rating_avg / rating_count via subqueries
    (subqueries, not joins: joins with compatible cars would count reviews twice)."""
    per_product = Review.objects.filter(product=OuterRef("pk")).values("product")
    return queryset.annotate(
        rating_avg=Subquery(per_product.annotate(a=Avg("rating")).values("a")[:1]),
        rating_count=Coalesce(
            Subquery(per_product.annotate(c=Count("pk")).values("c")[:1], output_field=IntegerField()), 0
        ),
    )


def summary(product):
    """Average, total and how many 5/4/3/2/1-star reviews."""
    stats = product.reviews.aggregate(avg=Avg("rating"), count=Count("pk"))
    distribution = {str(stars): 0 for stars in range(5, 0, -1)}
    for row in product.reviews.values("rating").annotate(n=Count("pk")):
        distribution[str(row["rating"])] = row["n"]
    return {
        "avg": round(stats["avg"], 1) if stats["avg"] is not None else None,
        "count": stats["count"],
        "distribution": distribution,
    }
