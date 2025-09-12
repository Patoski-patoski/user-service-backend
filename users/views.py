# users/view.py

from rest_framework import status
from rest_framework.response import Response
from rest_framework.request import Request as DRFRequest
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView


from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from typing import Dict, Any
from .serializers import PendingUserSerializer, UserLoginSerializer, UserProfileSerializer
import logging

from .models import User, PendingUser, UserProfile

logger: logging.Logger = logging.getLogger(__name__)

class RegisterView(APIView):
    """
    Handle user registration by accepting email and password, creating a pending user,
    and sending an activation email.
    """

    throttle_classes: list[type[AnonRateThrottle] | type[UserRateThrottle]] = [AnonRateThrottle, UserRateThrottle]

    def post(self, request: DRFRequest) -> Response:
        """Register a new user and send an activation email."""
        serializer = PendingUserSerializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"Registration failed: {serializer.errors}")
            return Response(
                {"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            pending_user = serializer.save()
            activation_link: str = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}/api/users/activate/{pending_user.verification_token}"

            email_sent: bool = self.send_activation_email(pending_user.email, activation_link)

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
            pending_user: PendingUser = PendingUser.objects.get(verification_token=token)

            if pending_user.expires_at < timezone.now():
                return Response(
                    {"error": "Activation token has expired."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Create the user
            user: User = User.objects.create_user(
                email=pending_user.email,
                password=pending_user.password,  # The password is already hashed
                first_name=pending_user.first_name,
                last_name=pending_user.last_name,
            )
            user.set_password(pending_user.password) # Re-set password to ensure it's hashed correctly
            user.save()

            # Create a profile for the user
            UserProfile.objects.create(user=user)

            # Delete the pending user
            pending_user.delete()

            logger.info(f"User {user.email} activated successfully.")

            return Response(
                {
                    "message": "Account activated successfully.",
                    "email": user.email,
                },
                status=status.HTTP_200_OK,
            )

        except PendingUser.DoesNotExist:
            return Response(
                {"error": "Invalid activation token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            logger.error(f"Unexpected error during account activation: {str(e)}")
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(TokenObtainPairView):
    """
    Handle user login and return a JWT token pair.
    """
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request: DRFRequest, *args, **kwargs) -> Response:
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'])
            UserProfile.objects.get_or_create(user=user)
        return response


class ProfileView(APIView):
    """
    Handle user profile retrieval and updates.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: DRFRequest) -> Response:
        """
        Retrieve the user's profile.
        """
        user = request.user
        try:
            profile = UserProfile.objects.get(user=user)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request: DRFRequest) -> Response:
        """
        Update the user's profile.
        """
        user = request.user
        try:
            profile = UserProfile.objects.get(user=user)
            serializer = UserProfileSerializer(profile, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            # If profile does not exist, create one
            serializer = UserProfileSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
