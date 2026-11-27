from django.conf import settings
from rest_framework import exceptions as drf_exceptions
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

from . import google
from .models import GarageCar
from .serializers import GarageCarSerializer, PasswordChangeSerializer, RegisterSerializer, UserSerializer


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ {username, password} → JWT tokens. At most 10 attempts per minute per IP."""

    throttle_scope = "auth"


class LogoutView(generics.GenericAPIView):
    """POST /api/auth/logout/ {refresh} — sign out: the refresh token is blacklisted and can't be used again."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(request=inline_serializer("Logout", {"refresh": serializers.CharField()}), responses={205: None})
    def post(self, request):
        try:
            RefreshToken(request.data.get("refresh", "")).blacklist()
        except TokenError:
            pass  # already expired / blacklisted: the user is signed out anyway
        return Response(status=status.HTTP_205_RESET_CONTENT)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — create a customer account and sign in straight away (returns JWT tokens)."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    @extend_schema(responses=inline_serializer("RegisterResult", {
        "user": UserSerializer(), "access": serializers.CharField(), "refresh": serializers.CharField(),
    }))
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {"user": UserSerializer(user).data, "access": str(refresh.access_token), "refresh": str(refresh)},
            status=status.HTTP_201_CREATED,
        )


class GoogleConfigView(generics.GenericAPIView):
    """GET /api/auth/google/config/ — the Google OAuth client ID ("" = Google sign-in is off)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=inline_serializer("GoogleConfig", {"client_id": serializers.CharField()}))
    def get(self, request):
        return Response({"client_id": settings.GOOGLE_CLIENT_ID})


class GoogleLoginView(generics.GenericAPIView):
    """POST /api/auth/google/ {credential} — sign in (or sign up) with a Google ID token; returns JWT tokens."""

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    @extend_schema(
        request=inline_serializer("GoogleLogin", {"credential": serializers.CharField()}),
        responses=inline_serializer("GoogleLoginResult", {
            "user": UserSerializer(), "access": serializers.CharField(), "refresh": serializers.CharField(),
            "created": serializers.BooleanField(),
        }),
    )
    def post(self, request):
        credential = request.data.get("credential", "")
        if not isinstance(credential, str) or not credential:
            raise drf_exceptions.ValidationError({"credential": "This field is required."})
        user, created = google.user_for(google.verify(credential))
        refresh = RefreshToken.for_user(user)
        return Response({"user": UserSerializer(user).data, "access": str(refresh.access_token),
                         "refresh": str(refresh), "created": created})


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/me/ — current user's profile (name, email, phone, address, language)."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch"]

    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """POST /api/auth/password/ {old_password, new_password}"""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=PasswordChangeSerializer, responses={204: None})
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GarageViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    GET    /api/auth/garage/       — my saved cars
    POST   /api/auth/garage/       {car_id, year} — save a car
    DELETE /api/auth/garage/{id}/  — remove it
    """

    serializer_class = GarageCarSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return GarageCar.objects.none()
        return GarageCar.objects.filter(user=self.request.user).select_related("car")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
