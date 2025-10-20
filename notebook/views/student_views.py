from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView, View
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta
from ..models import DailyRecord, Notification, RecordAttachment
from ..forms import DailyRecordForm
from accounts.mixins import StudentAndAdminMixin
from datetime import datetime
import json


class DailyRecordCreateView(LoginRequiredMixin, StudentAndAdminMixin, CreateView):
    model = DailyRecord
    form_class = DailyRecordForm
    template_name = 'notebook/record_form.html'
    success_url = reverse_lazy('notebook:student_record_list')

    def get_default_schoolday(self):
        today = date.today()
        weekday = today.weekday()

        if weekday == 0:
            default_date = today - timedelta(days=3)
        elif weekday == 6:
            default_date = today - timedelta(days=2)
        elif weekday == 5:
            default_date = today - timedelta(days=1)
        else:
            default_date =today - timedelta(days=1)
        return default_date

    def get_initial(self):
        # 初期値記録日を設定
        return {'date_for': self.get_default_schoolday()}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートにデフォルトの日付を渡すが、ユーザーはフォームで変更可能
        context['default_record_date'] = self.get_default_schoolday()
        return context
    
    def form_valid(self, form):
        # フォーム送信時、生徒と記録日を自動セット
        form.instance.student = self.request.user
        submitted_date = form.cleaned_data.get('date_for')
        # 提出された日付に対して、既にレコードが存在するかをチェック
        if DailyRecord.objects.filter(student=self.request.user, date_for=submitted_date).exists():
            messages.error(self.request, f'{submitted_date}分の連絡帳は既に提出済です。')
            return redirect(self.success_url)
        
        if not self.request.user.classroom or not self.request.user.classroom.homeroom_teacher:
            messages.error(self.request, "担任が設定されていないため提出できません。")
            return redirect(self.success_url)
        
        response = super().form_valid(form)
        # ファイルを取得
        files = self.request.FILES.getlist('file')
        for f in files:
            RecordAttachment.objects.create(record=self.object, file=f)

        messages.success(self.request, f'{submitted_date}分の連絡帳を提出しました。')

        Notification.objects.create(
            sender=self.request.user,
            recipient=self.request.user.classroom.homeroom_teacher,
            message=f'{self.request.user.full_name}さんが{submitted_date}分の連絡帳を提出しました。',
            related_record=form.instance,
        )
        return response

class StudentRecordListView(LoginRequiredMixin, StudentAndAdminMixin, ListView):
    model = DailyRecord
    template_name = 'notebook/student_record_list.html'
    paginate_by = 10

    def get_queryset(self):
        queryset = DailyRecord.objects.filter(student=self.request.user).order_by('-date_for')

        self.start_date_param = self.request.GET.get('start_date')
        self.end_date_param = self.request.GET.get('end_date')
        self.selected_read_status = self.request.GET.get('read_status', 'all')
        # start_date 処理: 開始日以降
        if self.start_date_param:
            try:
                start_date_obj = date.fromisoformat(self.start_date_param)
                queryset = queryset.filter(date_for__gte=start_date_obj)
            except ValueError:
                pass
        # end_date 処理: 終了日以前
        if self.end_date_param:
            try:
                end_date_obj = date.fromisoformat(self.end_date_param)
                queryset = queryset.filter(date_for__lte=end_date_obj)
            except ValueError:
                pass
        
        if self.selected_read_status == 'unread':
            queryset = queryset.filter(is_read=False)
        elif self.selected_read_status == 'read':
            queryset = queryset.filter(is_read=True)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['start_date_filter_value'] = self.start_date_param if self.start_date_param else ''
        context['end_date_filter_value'] = self.end_date_param if self.end_date_param else ''
        context['selected_read_status'] = self.selected_read_status
        # 未読レコード数の計算
        context['unread_record_count'] = DailyRecord.objects.filter(
            student=self.request.user,
            is_read=False,
        ).count()    
        return context

class StudentRecordDetailView(LoginRequiredMixin, StudentAndAdminMixin, DetailView):
    model = DailyRecord
    template_name = 'notebook/student_record_detail.html'

    def get_queryset(self):
        queryset = DailyRecord.objects.filter(
            student=self.request.user,
        ).select_related('read_by', 'student__classroom',
        ).prefetch_related('memos__teacher')
        return queryset

    # コンテキストデータに既存のメモ情報（表示用）
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.get_object()
        context['current_memo'] = getattr(record, 'memos', None)
        return context

class StudentRecordUpdateView(LoginRequiredMixin, StudentAndAdminMixin, UpdateView):
    model = DailyRecord
    form_class = DailyRecordForm
    template_name = 'notebook/record_form.html'

    def get_queryset(self):
        return DailyRecord.objects.filter(student=self.request.user)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.is_read:
            raise PermissionDenied('担任に確認された記録は編集できません。')
        return obj
    
    def form_valid(self, form):
        response = super().form_valid(form)
        files = self.request.FILES.getlist('file')
        for f in files:
            RecordAttachment.objects.create(record=self.object, file=f)
        messages.success(self.request, '連絡帳を更新しました。')
        return response

    def get_success_url(self):
        return reverse('notebook:student_record_detail', kwargs={'pk': self.object.pk})

class StudentRecordDeleteView(LoginRequiredMixin, StudentAndAdminMixin, DeleteView):
    model = DailyRecord
    template_name = 'notebook/student_record_delete.html'
    success_url = reverse_lazy('notebook:student_record_list')

    def get_queryset(self):
        return DailyRecord.objects.filter(student=self.request.user)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.is_read:
            raise PermissionDenied('担任に確認された記録は削除できません。')
        return obj
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '記録を削除しました。')
        return super().delete(request, *args, **kwargs)

# グラフ表示用ビュー
class StudentRecordGraphView(LoginRequiredMixin, StudentAndAdminMixin, TemplateView):
    template_name = 'notebook/student_record_graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # データ取得
        records = DailyRecord.objects.filter(student=self.request.user).order_by('date_for')
        # グラフ用にデータを整形
        dates = []
        physical_levels = []
        mental_levels = []
        for record in records:
            # 日付をラベル用にフォーマット
            dates.append(record.date_for.strftime('%Y-%m-%d'))
            # 評価レベルをリストに追加
            physical_levels.append(record.physical_level)
            mental_levels.append(record.mental_level)
        # テンプレートに渡すためんいJSON文字列に変換
        context['dates_json'] = json.dumps(dates)
        context['physical_levels_json'] = json.dumps(physical_levels)
        context['mental_levels_json'] = json.dumps(mental_levels)
        context['total_records'] = records.count()

        return context

class RecordAttachmentDeleteView(LoginRequiredMixin, StudentAndAdminMixin, View):
    def post(self, request, pk):
        attachment = get_object_or_404(RecordAttachment, pk=pk)
        if attachment.record.student != request.user:
            raise PermissionDenied
        record_pk = attachment.record.pk
        attachment.delete()
        return redirect('notebook:student_record_update', pk=record_pk)
