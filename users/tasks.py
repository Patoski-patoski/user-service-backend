from celery import shared_task
from django.utils import timezone

from .models import PendingUser


@shared_task
def delete_expired_pending_users() -> int:
    """Delete expired pending users."""
    deleted, _ = PendingUser.objects.filter(expires_at__lt=timezone.now()).delete()
    return deleted
