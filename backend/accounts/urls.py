from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    GarageViewSet, GoogleConfigView, GoogleLoginView, LoginView, LogoutView, MeView, PasswordChangeView, RegisterView,
)

router = DefaultRouter()
router.register("garage", GarageViewSet, basename="garage")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("google/config/", GoogleConfigView.as_view(), name="google-config"),
    path("google/", GoogleLoginView.as_view(), name="google-login"),
    path("me/", MeView.as_view(), name="me"),
    path("password/", PasswordChangeView.as_view(), name="password-change"),
] + router.urls
