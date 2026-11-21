from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BrandViewSet, CarModelViewSet, CategoryViewSet, ProductViewSet, ReviewViewSet, global_search

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("categories", CategoryViewSet, basename="category")
router.register("brands", BrandViewSet, basename="brand")
router.register("cars", CarModelViewSet, basename="car")
router.register("reviews", ReviewViewSet, basename="review")

urlpatterns = [path("search/", global_search, name="search")] + router.urls
