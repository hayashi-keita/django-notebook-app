from django.views.generic import ListView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from ..models import Notification
from django.contrib.auth.mixins import LoginRequiredMixin

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notebook/notification_list.html'

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).order_by('-created_at')
    
    def post(self, request, *args, **kwargs):
        if 'read_id' in request.POST:
            notification = get_object_or_404(Notification, pk=request.POST['read_id'], recipient=request.user)
            notification.is_read = True
            notification.save()
            messages.success(request, '通知を既読にしました。')
        
        elif 'delete_id' in request.POST:
            notification = get_object_or_404(Notification, pk=request.POST['delete_id'], recipient=request.user)
            notification.delete()
            messages.info(request, '通知を削除しました。')
        
        return redirect('notebook:notification_list')