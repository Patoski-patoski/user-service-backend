# users/view.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request as DRFRequest
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from django.conf import settings
# from user_service import settings
from django.core.mail import send_mail
# from django.utils import timezone


from typing import Dict, Any
from .serializers import UserRegistrationSerializer
# from datetime import timezone
import logging

from .models import User

logger: logging.Logger = logging.getLogger(__name__)
# Create your views here.


class RegisterView(APIView):
    """
    Handle user registration by accepting email and password, creating a user,
    and sending an activation email.
    """

    throttle_classes: list[type[AnonRateThrottle] | type[UserRateThrottle]] = [AnonRateThrottle, UserRateThrottle]

    def post(self, request: DRFRequest) -> Response:
        """Register a new user and send an activation email."""
        serializer = UserRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Registration failed: {serializer.errors}")
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = serializer.save()
            activation_link: str = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/api/users/activate/{user.activation_token}"

            email_sent: bool = self.send_activation_email(user.email, activation_link)

            response_data: Dict[str, Any] = {
                "message": "Registration successful. Please check your email to activate your account.",
            }

            if not email_sent:
                response_data["warning"] = (
                    "Registration successful, but failed to send activation email"
                )

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
                message=f"Click the link to activate your account: {activation_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False,
            )
            logger.info(f"Activation email sent successfully to {recipient_email}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to send activation email to {recipient_email}: {str(e)}"
            )
            return False

class ActivateView(APIView):
    """
    Handle user account activation by verifying the activation token.
    """

    def get(self, request: DRFRequest, token: str) -> Response:
        try:
            user: User = User.objects.get(activation_token=token)
            if user.is_active:
                return Response(
                    {"message": "Account is already activated."},
                    status=status.HTTP_200_OK,
                )
            from django.utils import timezone

            if (
                user.activation_token_expiry
                and user.activation_token_expiry < timezone.now()
            ):
                return Response(
                    {"error": "Activation token has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.is_active = True
            user.save(update_fields=["is_active"])

            logger.info(f"User {user.email} activated successfully.")

            return Response(
                {
                    "message": "Account activated successfully.",
                    "email": user.email,
                },
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"error": "Invalid activation token."},
                status=status.HTTP_400_BAD_REQUEST,  # Changed from 404 to 400
            )

        except Exception as e:
            logger.error(f"Unexpected error during account activation: {str(e)}")
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )