# users/serializers.py
# type: ignore[no-untyped-call]

"""Serializer for user registration and validation."""

from .models import User
from rest_framework import serializers 
from typing import Optional, Dict
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserRegistrationSerializer(serializers.ModelSerializer[User]):
    """Serializer for user registration."""

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
        help_text="Confirm your password. Must Match the password field.",
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "confirm_password")
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
        }
        
    def validate_email(self, value: str) -> str:
        """ Validate email uniqueness"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        return value.lower()

    def validate_password(self, value: str) -> str:
        """ Validate password strength using Django's built-in validators """
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return value
    
    
    def validate(self, attrs: Dict[str, str]) -> Dict[str, str]:
        """ Validate that password and confirm_password match """
        password: Optional[str] = attrs.get("password")
        confirm_password: Optional[str] = attrs.get("confirm_password")
        
        if not password or not confirm_password:
            raise serializers.ValidationError(
                {"password": " Both Password and confirm password are required."}
            )
            
        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Password confirmation do not match."}
            )
            
        attrs.pop("confirm_password", None)  # Remove confirm_password from attrs

        return attrs

    def create(self, validated_data: Dict[str, str]) -> User:
        """Create and return a new user instance."""
        password: str = validated_data.pop("password")
        
        user: User = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        
        return user
