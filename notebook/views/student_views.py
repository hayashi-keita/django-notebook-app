from django.shortcuts import redirect
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from datetime import date, timedelta
from ..models import DailyRecord, Notification
from ..forms import DailyRecordForm
from accounts.mixins import StudentAndAdminMixin
import json


class DailyRecordCreateView(LoginRequiredMixin, StudentAndAdminMixin, CreateView):
    model = DailyRecord
    form_class = DailyRecordForm
    template_name = 'notebook/record_form.html'
    success_url = reverse_lazy('notebook:student_record_list')

    def get_initial(self):
        # 初期値記録日を設定
        default_date = date.today() - timedelta(days=1)
        return {'date_for': default_date}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートにデフォルトの日付を渡すが、ユーザーはフォームで変更可能
        context['default_record_date'] = date.today() - timedelta(days=1)
        return context
    
    def form_valid(self, form):
        # フォーム送信時、生徒と記録日を自動セット
        form.instance.student = self.request.user
        submitted_date = form.cleaned_data.get('date_for')
        # 提出された日付に対して、既にレコードが存在するかをチェック
        if DailyRecord.objects.filter(student=self.request.user, date_for=submitted_date).exists():
            messages.error(self.request, f'{submitted_date}分の連絡帳は既に提出済です。')
            return redirect(self.success_url)
        messages.success(self.request, f'{submitted_date}分の連絡帳を提出しました。')
        Notification.objects.create(
            user=self.request.user.classroom.homeroom_teacher,
            message=f'{self.request.user.get_full_name()}さんが{submitted_date}分の連絡帳を提出しました。',
            related_record=form.instance,
        )

        return super().form_valid(form)

class StudentRecordListView(LoginRequiredMixin, StudentAndAdminMixin, ListView):
    model = DailyRecord
    template_name = 'notebook/student_record_list.html'

    def get_queryset(self):
        return DailyRecord.objects.filter(student=self.request.user).order_by('-date_for')

class StudentRecordDetailView(LoginRequiredMixin, StudentAndAdminMixin, DetailView):
    model = DailyRecord
    template_name = 'notebook/student_record_detail.html'

    def get_queryset(self):
        queryset = DailyRecord.objects.filter(
            student=self.request.user,
        ).select_related('read_by', 'student__classroom',
        ).prefetch_related('memos__teacher')
        return queryset
    
    def get_object(self, queryset=None):
        record = super().get_object(queryset)
        if record.is_returned_to_student:
            record.is_returned_to_student = False
            record.save(update_fields=['is_returned_to_student'])
        return record

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