from django.views.generic import ListView
from ..models import Notification
from django.contrib.auth.mixins import LoginRequiredMixin

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notebook/notification_list.html'

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
        ).order_by('-created_at')