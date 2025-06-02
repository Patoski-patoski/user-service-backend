"""users/models.py:Custom user model for the application."""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from django.db import models
import uuid
from typing import Any, Dict, Optional, TypeVar

# Type variable for User model
# Define a type variable for the User class to avoid circular references
U = TypeVar("U", bound="User")


# Create your models here.
class UserManager(BaseUserManager[U]):
    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: Dict[str, Any]
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
    email = models.EmailField(unique=True, max_length=100)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects: UserManager['User'] = UserManager() # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self) -> str:
        return self.email

    class Meta:
        swappable = "AUTH_USER_MODEL"
