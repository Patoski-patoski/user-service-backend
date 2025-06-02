from rest_framework import status  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.request import Request as DRFRequest  # type: ignore
from rest_framework.views import APIView  # type: ignore
from rest_framework.authtoken.models import Token  # type: ignore
from django.http import QueryDict
from django.core.mail import send_mail
from typing import Any, Dict, Optional

from .models import User

# Create your views here.


class RegisterView(APIView):
    """
    Handle user registration by accepting email and password, creating a user,
    and sending an activation email.
    """
    def post(self, request: DRFRequest) -> Response:
        data: QueryDict = request.data
        
        email: Optional[str] = data.get("email")
        password: Optional[str] = data.get("password")

        # validate input
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create user
        user = User.objects.create_user(email=email, password=password)
        activation_link: str = (
            f"http://localhost:8000/api/users/activate/{user.activation_token}"
        )

        send_mail(
            subject="Activate your account",
            message=f"Click the link to activate your account\n: {activation_link}",
            from_email="codesbypatrick@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response(
            {
                "message": "Registration successful. Please check your email to activate your account."
            },
            status=status.HTTP_201_CREATED,
        )

class ActivateView(APIView):
    """
    Handle user account activation by verifying the activation token.
    """

    def get(self, request: DRFRequest, token: str) -> Response:
        
        try:
            user: User = User.objects.get(activation_token=token)
            user.is_active = True
            user.save()
            
            return Response(
                {"message": "Account activated successfully."},
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid activation token."},
                status=status.HTTP_400_BAD_REQUEST
            )
            