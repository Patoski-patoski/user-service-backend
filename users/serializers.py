# users/serializers.py

"""Serializer for user registration and validation."""

from .models import User, PendingUser
from rest_framework import serializers 
from typing import Optional, Dict
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password

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
        fields = (
            "email", 
            "first_name", 
            "last_name", 
            "password", 
            "confirm_password")
        
        extra_kwargs: Dict[str, Dict[str, bool]] = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def validate_email(self, value: str) -> str:
        """Validate email uniqueness in both User and PendingUser models."""
        if User.objects.filter(email__iexact=value).exists() or \
           PendingUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists or is pending verification."}
            )
        return value.lower()

    def validate_password(self, password: str) -> str:
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

    def create(
        self, validated_data: Dict[str, str]
    ) -> PendingUser:
        """Create and return a new pending user instance."""
        validated_data["password"] = make_password(validated_data["password"])
        return PendingUser.objects.create(**validated_data)

class UserLoginSerializer(serializers.ModelSerializer[User]):
    """Serializer for user login."""
    email = serializers.CharField(
        required=True,
        label="Email",
        help_text="Enter your email.",
    )
    password = serializers.CharField(
        style={"input_type": "password"},
        write_only=True,
        required=True,
        label="Password",
        help_text="Enter your password.",
    )

    class Meta:
        model = User
        fields: list[str] = ["email", "password"]

    def validate(self, attrs: Dict[str, str]) -> Dict[str, str]:
        """Validate user credentials."""
        email: Optional[str] = attrs.get("email")
        password: Optional[str] = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError({"detail": "Email and password are required."})

        user = authenticate(email=email, password=password)
        print("Login validate: user", user)
        if user is None:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        return attrs