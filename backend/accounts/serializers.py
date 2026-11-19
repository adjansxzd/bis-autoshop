import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from catalog.models import CarModel

from .models import GarageCar

User = get_user_model()

PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{10,20}$")


def clean_phone(value):
    if value and not PHONE_RE.match(value):
        raise serializers.ValidationError("Enter a valid phone number, e.g. +7 700 123 45 67.")
    return value


class UserSerializer(serializers.ModelSerializer):
    """GET/PATCH /api/auth/me/ — the profile. Role and username can't be changed by the user."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "phone", "address", "role", "preferred_language"]
        read_only_fields = ["id", "username", "role"]
        extra_kwargs = {"email": {"validators": []}}

    def validate_email(self, value):
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already used by another account.")
        return value.lower()

    def validate_phone(self, value):
        return clean_phone(value)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, label="Repeat password")

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2", "first_name", "last_name", "phone"]
        # our own validate_email gives a clearer, case-insensitive check than the model's unique validator
        extra_kwargs = {"email": {"required": True, "validators": []}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_phone(self, value):
        return clean_phone(value)

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        # Django's password rules: length, not too common, not only digits, not similar to the username
        validate_password(attrs["password"], user=User(username=attrs.get("username"), email=attrs.get("email")))
        return attrs

    def create(self, validated_data):
        # create_user hashes the password; self-registration is always a customer
        return User.objects.create_user(**validated_data, role=User.Role.CUSTOMER)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is wrong.")
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context["request"].user)
        return value


class GarageCarSerializer(serializers.ModelSerializer):
    car_id = serializers.PrimaryKeyRelatedField(source="car", queryset=CarModel.objects.all())
    make = serializers.CharField(source="car.make", read_only=True)
    model = serializers.CharField(source="car.model", read_only=True)

    class Meta:
        model = GarageCar
        fields = ["id", "car_id", "make", "model", "year", "created_at"]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        car, year = attrs["car"], attrs["year"]
        if not car.year_from <= year <= car.year_to:
            raise serializers.ValidationError({"year": f"{car.make} {car.model} exists for {car.year_from}–{car.year_to}."})
        user = self.context["request"].user
        if GarageCar.objects.filter(user=user, car=car, year=year).exists():
            raise serializers.ValidationError({"car_id": "This car is already in your garage."})
        return attrs
