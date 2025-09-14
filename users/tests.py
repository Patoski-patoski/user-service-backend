# users/tests.py

"""Custom user model for the application."""

# import uuid
import uuid
from typing import Dict

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient, APITestCase

from .serializers import PendingUserSerializer
from .models import User, PendingUser

# Create your tests here.

class UserModelTests(TestCase):
    def setUp(self) -> None:
        self.email: str = "test@example.com"
        self.password: str = "securedpassword123"
        self.user: User = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name="Test",
            last_name="User",
        )

    def test_user_creation(self) -> None:
        """Test that a user can be created with email and password."""
        self.assertEqual(self.user.email, self.email.lower())
        self.assertTrue(self.user.check_password(self.password))
        self.assertFalse(self.user.is_active)
        self.assertFalse(hasattr(self.user, "activation_token"))
        self.assertEqual(self.user.full_name, "Test User")

    def test_create_superuser(self) -> None:
        """Test that a superuser can be created."""
        superuser: User = User.objects.create_superuser(
            email="superuser@example.com",
            password="supersecurepassword123",
            first_name="Super",
            last_name="User",
        )
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_str(self) -> None:
        """Test the string representation of the user."""
        self.assertEqual(str(self.user), self.email)


class PendingUserSerializerTests(TestCase):
    def setUp(self) -> None:
        self.valid_data: Dict[str, str] = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "newuserpassword123",
            "confirm_password": "newuserpassword123",
        }

        self.invalid_data: Dict[str, str] = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "newuserpassword123",
            "confirm_password": "newuserpassword124",  # Mismatched password
        }

    def test_valid_data(self) -> None:
        """Test serializer with valid data."""
        serializer = PendingUserSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, "newuser@example.com")
        

    def test_password_mismatch(self) -> None:
        """Test serializer with mismatched passwords"""
        serializer = PendingUserSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_password", serializer.errors)

    def test_duplicate_email(self) -> None:
        """Test serializer with duplicate email"""
        User.objects.create_user(email="newuser@example.com", password="password123")
        serializer = PendingUserSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)


class RegisterViewTests(APITestCase):
    def setUp(self) -> None:
        User.objects.all().delete()
        PendingUser.objects.all().delete()
        cache.clear()

        self.client: APIClient = APIClient()
        self.url = "/api/users/register/"
        self.base_valid_data: Dict[str, str] = {
            "first_name": "Tester",
            "last_name": "User",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123",
        }

    def tearDown(self) -> None:
        cache.clear()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [],  # Disable throttling for these tests
            "DEFAULT_THROTTLE_RATES": {},
        },
    )
    def test_successful_registration(self):
        """Test successful user registration."""
        valid_data  = self.base_valid_data.copy()
        valid_data["email"] = "testuser@example.com"
        response = self.client.post(self.url, valid_data, format="json")
        print("response", response.status_code)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["message"],
            "Registration successful. Please check your email to activate your account.",
        )
        pending_user = PendingUser.objects.filter(email="testuser@example.com").first()
        self.assertIsNotNone(pending_user)
        if pending_user is not None:
            self.assertFalse(User.objects.filter(email=pending_user.email).exists())
        self.assertEqual(len(mail.outbox), 1)
        print("\n\nOutbox", mail.outbox[0].subject)
        self.assertIn("Activate your account", str(mail.outbox[0].subject))

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": "5/minute",
            },
        }
    )
    def test_invalid_data(self) -> None:
        """Test registration with invalid data (e.g., password mismatch)."""
        invalid_data = self.base_valid_data.copy()
        invalid_data["email"] = "testuser@example.com"
        invalid_data["confirm_password"] = "DifferentPass123"
        response: Response = self.client.post(self.url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response.data["errors"])

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [],  # Disable throttling for this test
            "DEFAULT_THROTTLE_RATES": {},
        }
    )
    def test_duplicate_email(self) -> None:
        """Test registration with an email that already exists."""
        User.objects.create_user(email="testuser@example.com", password="password123")
        valid_data = self.base_valid_data.copy()
        valid_data["email"] = "testuser@example.com"
        response: Response = self.client.post(self.url, valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["errors"])

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "anon": "5/minute",
            },
        }
    )
    def test_rate_limiting(self) -> None:
        """Test rate limiting on registration endpoint."""

        cache.clear()

        for i in range(5):
            valid_data: Dict[str, str] = self.base_valid_data.copy()
            valid_data["email"] = f"testuser{i}@example.com"
            print("valid_data emails", valid_data["email"])
            response: Response = self.client.post(self.url, valid_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        valid_data = self.base_valid_data.copy()
        valid_data["email"] = "testuser6@example.com"
        response = self.client.post(self.url, valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Request was throttled", response.data.get("detail", ""))


class ActivateViewTests(APITestCase):
    def test_successful_activation(self) -> None:
        """Test successful user account activation."""
        pending_user = PendingUser.objects.create(
            email="testuser@example.com",
            password="SecurePass123",
        )
        token = str(pending_user.verification_token)
        url = f"/api/users/activate/{token}/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Account activated successfully.")

        user = User.objects.get(email=pending_user.email)
        self.assertTrue(user.is_active)

    def test_already_activated(self) -> None:
        """Test activation of an already activated account."""
        User.objects.create_user(
            email="testuser@example.com",
            password="SecurePass123",
            is_active=True,
        )
        pending_user = PendingUser.objects.create(
            email="testuser@example.com",
            password="SecurePass123",
        )
        token = str(pending_user.verification_token)
        url = f"/api/users/activate/{token}/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Account is already activated.")

    def test_invalid_token(self) -> None:
        """Test activation with an invalid token."""    
        invalid_url: str = f"/api/users/activate/{uuid.uuid4()}/"
        response: Response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
