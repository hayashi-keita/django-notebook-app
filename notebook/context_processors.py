from .models import DailyRecord
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

def unread_notification_context(request):
    unread_count = 0
    
    if request.user.is_authenticated:
        user = request.user

        if user.role == 'ADMIN':
            unread_count = DailyRecord.objects.filter(is_read=False).count()
        
        elif user.role == 'TEACHER':
            homeroom_classes = user.homeroom_classes.all()
            student_ids = CustomUser.objects.filter(
                classroom__in=homeroom_classes,
                role='STUDENT',
            ).values_list('pk', flat=True)
            unread_count = DailyRecord.objects.filter(
                student__id__in=student_ids,
                is_read=False,
            ).count()
    
    return {'unread_notification_count': unread_count}

def get_returned_count_for_student(request):
    user = request.user
    if not user.is_authenticated or user.role != 'STUDENT':
        return {'returned_count': 0}
    
    returned_count = DailyRecord.objects.filter(
        student=user,
        is_returned_to_student=True,
    ).count()
    
    return {'returned_count': returned_count}