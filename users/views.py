# users/view.py
# type: ignore[no-untyped-call]

from rest_framework import status 
from rest_framework.response import Response  
from rest_framework.request import Request as DRFRequest 
from rest_framework.views import APIView 

from django.conf import settings
from django.core.mail import send_mail

from typing import Optional, Dict, Any 
from .serializers import UserRegistrationSerializer
import logging
from .models import User

logger = logging.getLogger(__name__)
# Create your views here.

class RegisterView(APIView):
    """
    Handle user registration by accepting email and password, creating a user,
    and sending an activation email.
    """
    def post(self, request: DRFRequest) -> Response:
        """ Register a new user and send an activation email."""
        serializer = UserRegistrationSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Registration failed: {serializer.errors}")
            return Response(
                {"errors": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = serializer.save()
            activation_link: str = (
                f"http://localhost:8000/api/users/activate/{user.activation_token}"
            )

            email_sent = self.send_activation_email(user.email, activation_link)

            response_data: Dict[str, Any] = {
                "message": "Registration successful. Please check your email to activate your account.",
            }
            
            if not email_sent:
                response_data["warning"] = "Registration successful, but failed to send activation email"
                
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


    def send_activation_email(self, recipient_email: str, activation_link: str) -> bool:
        """
        Send an activation email to the user with the activation link.
        """
        try:
            send_mail(
                subject="Activate your account",
                message=f"Click the link to activate your account\n: {activation_link}",
                from_email="codesbypatrick@gmail.com",
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            return True
        
        except Exception as e:
            logger.error(f"Failed to send activation email to {recipient_email}: {str(e)}")
            return False


class ActivateView(APIView):
    """
    Handle user account activation by verifying the activation token.
    """
    def get(self, request: DRFRequest, token: str) -> Response:
        
        try:
            user = User.objects.get(activation_token=token)
            if user.is_active:
                return Response(
                    {"message": "Account is already activated."},
                    status=status.HTTP_200_OK
                )
            user.is_active = True
            user.save(update_fields=['is_active'])
            
            logger.info(f"User {user.email} activated successfully.")
            
            return Response(
                {
                    "message": "Account activated successfully.",
                    "email": user.email,
                },
                status=status.HTTP_200_OK
            )
            
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid activation token."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.error(f"Unexpected error during account activation: {str(e)}")
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )