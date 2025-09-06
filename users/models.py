# users/models.py

"""Custom user model for the application."""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.db import models
import uuid
from typing import Any, Optional, TypeVar, TYPE_CHECKING
from datetime import datetime, timedelta

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



class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as the unique identifier."""

    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False, 
        unique=True,
        help_text="Unique identifier for the user."
    )
    email = models.EmailField(unique=True, max_length=100)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)
    last_login = models.DateTimeField(null=True, blank=True)

    if TYPE_CHECKING:
        objects: UserManager["User"] = UserManager()
    else:
        objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    class Meta:
        swappable: str = "AUTH_USER_MODEL"


def default_pending_user_expiry() -> datetime:
    return timezone.now() + timedelta(minutes=10)


class PendingUser(models.Model):
    """Model for temporarily storing user data pending email verification."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=100)
    password = models.CharField(max_length=128)  # Stores hashed password
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    expires_at = models.DateTimeField(default=default_pending_user_expiry)

    def __str__(self) -> str:
        return self.email
