# users/serializers.py

"""Serializer for user registration and validation."""

from typing import Any, Dict, Optional

# from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import PendingUser, User, UserProfile


class PendingUserSerializer(serializers.ModelSerializer[PendingUser]):
    """Serializer for pending user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Password must be at least 8 characters long",
    )

    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
        help_text="Confirm your password. Must match the password field.",
    )

    class Meta:
        model = PendingUser
        fields = ("email", "first_name", "last_name", "password", "confirm_password")

        extra_kwargs: Dict[str, Dict[str, bool]] = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def validate_email(self, value: str) -> str:
        """Validate email uniqueness in both User and PendingUser models."""
        if (
            User.objects.filter(email__iexact=value).exists()
            or PendingUser.objects.filter(email__iexact=value).exists()
        ):
            raise serializers.ValidationError(
                {
                    "email": "A user with this email already exists or is pending verification."
                }
            )
        return value.lower()

    def validate_raw_password(self, password: str) -> str:
        """Validate password strength using Django's built-in validators"""
        try:
            validate_password(password)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return password

    def validate(self, attrs: Dict[str, str]) -> Dict[str, str]:
        """Validate that password and confirm_password match"""
        password: Optional[str] = attrs.get("password")
        confirm_password: Optional[str] = attrs.get("confirm_password")

        if not password or not confirm_password:
            raise serializers.ValidationError(
                {"password": "Both password and confirm password are required."}
            )

        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Password confirmation do not match."}
            )

        attrs.pop("confirm_password", None)  # Remove confirm_password from attrs
        return attrs

    def create(self, validated_data: Dict[str, str]) -> PendingUser:
        """Create and return a new pending user instance."""
        return PendingUser.objects.create(**validated_data)


class UserLoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "No active account found with the given credentials"
    }

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        data = super().validate(attrs)
        if not getattr(self, "user", None) or not getattr(self.user, "is_active", False):
            raise serializers.ValidationError(
                self.error_messages["no_active_account"], code="no_active_account"
            )
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model.
    """

    class Meta:
        model = UserProfile
        fields = ("bio", "location", "birth_date")
