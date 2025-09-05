from datetime  import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from celery import shared_task


@shared_task
def delete_inactive_users() -> int:
    """Delete inactive users who registered before the threshold."""
    User = get_user_model()
    threshold = timezone.now() - timedelta(minutes=1)
    deleted, _ = User.objects.filter(
        is_active=False, date_joined__lt=threshold
    ).delete()
    
    return deleted
