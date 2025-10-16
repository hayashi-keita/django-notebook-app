from .models import DailyRecord, Notification
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def unread_notification_context(request):
    unread_count = 0
    
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()

    return {'unread_notification_count': unread_count}