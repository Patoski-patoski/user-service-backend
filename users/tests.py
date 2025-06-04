# users/tests.py

"""Custom user model for the application."""

from django.test import TestCase
from .views import RegisterView, ActivateView
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from typing import Dict, Optional, Any, Union
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import UserManager, User
from users.serializers import UserRegistrationSerializer

# Create your tests here.

class UserModelTests(TestCase):
    def setUp(self) -> None:
        self.email: str = "test@example.com"
        self.password: str = "securedpassword123"
        self.user_manager: UserManager['User'] = UserManager()
        self.user: User = self.user_manager.create_user(
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
        self.assertIsInstance(self.user.activation_token, uuid.UUID)
        self.assertEqual(self.user.full_name, "Test User")
        
        
    def test_create_superuser(self) -> None:
        """Test that a superuser can be created."""
        superuser: User = self.user_manager.create_superuser(
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
        
        

class UserRegistrationSerializerTests(TestCase):
    def setup(self) -> None:
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
            "confirm_password": "newuserpassword124", # Mismatched password
        }
        
    def test_valid_data(self) -> None:
        """Test serializer with valid data."""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("newuserpassword123"))
        
    def test_password_mismatch(self) -> None:
        """Test serializer with mismatched passwords"""
        serializer = UserRegistrationSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("confirm_password", serializer.errors)
        
    
    def test_duplicate_email(self) -> None:
        """Test serializer with duplicate email"""
        User.objects.create_user(  
            email="newuser@example.com", 
            password="password123"
        )
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        

class RegisterViewTests(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.url = "/api/users/register/"
        self.valid_data: Dict[str, str] = {
            "email": "testuser@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "SecurePass123",
            "confirm_password": "SecurePass123",
        }
        self.invalid_data: Dict[str, str] = {
            "email": "testuser@example.com",
            "password": "SecurePass123",
            "confirm_password": "DifferentPass123",
        }
    def test_successful_registration(self) -> None:
        """Test successful user registration."""
        response = self.client.post(self.url, self.valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data['message'],
            "User registered successfully. Please check your email to activate your account."
        )
        
        # Check if user is created in the database
        user: Optional[User] =  User.objects.filter(email="testuser@example.com").first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_active)
