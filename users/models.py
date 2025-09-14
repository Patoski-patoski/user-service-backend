# users/models.py

"""Custom user model for the application."""

import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional, TypeVar

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

# Type variable for User model
# Define a type variable for the User class to avoid circular references
if TYPE_CHECKING:
    from .models import User

U = TypeVar("U", bound="User")


# Create your models here.
class UserManager(BaseUserManager[U]):
    """Custom user manager for User model."""

    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: Any
    ) -> U:
        """Create and return a user with an email and password."""
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user: U = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields: Any,
    ) -> U:
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


def default_activation_token_expiry() -> datetime:
    return timezone.now() + timedelta(seconds=10)


def default_pending_user_expiry() -> datetime:
    return timezone.now() + timedelta(minutes=10)


class PendingUser(models.Model):
    """Model for temporarily storing user data pending email verification."""

    id: models.UUIDField = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email: models.EmailField = models.EmailField(unique=True, max_length=100)
    password: models.CharField = models.CharField(max_length=128)
    first_name: models.CharField = models.CharField(max_length=30, blank=True)
    last_name: models.CharField = models.CharField(max_length=30, blank=True)
    verification_token: models.UUIDField = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )
    created_at: models.DateTimeField = models.DateTimeField(default=timezone.now, editable=False)
    expires_at: models.DateTimeField = models.DateTimeField(default=default_pending_user_expiry)

    def __str__(self) -> str:
        return self.email


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the unique identifier."""

    id: models.UUIDField = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Unique identifier for the user.",
    )
    email: models.EmailField = models.EmailField(unique=True, max_length=100)
    first_name: models.CharField = models.CharField(max_length=30, blank=True)
    last_name: models.CharField = models.CharField(max_length=30, blank=True)
    is_active: models.BooleanField = models.BooleanField(default=False)
    is_staff: models.BooleanField = models.BooleanField(default=False)
    date_joined: models.DateTimeField = models.DateTimeField(default=timezone.now, editable=False)
    last_login: models.DateTimeField = models.DateTimeField(null=True, blank=True)

    # if TYPE_CHECKING:
        # objects: UserManager["User"] = UserManager()
    # else:
    objects: UserManager["User"] = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    class Meta:
        swappable: str = "AUTH_USER_MODEL"


class UserProfile(models.Model):
    """
    Model to store additional user profile information.
    """

    user: models.OneToOneField = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        primary_key=True,
        help_text="The user associated with this profile.",
    )
    bio: models.TextField = models.TextField(blank=True, help_text="A short bio of the user.")
    location: models.CharField = models.CharField(
        max_length=100, blank=True, help_text="The user's location."
    )
    birth_date: models.DateField = models.DateField(
        null=True, blank=True, help_text="The user's birth date."
    )

    def __str__(self) -> str:
        return self.user.email
