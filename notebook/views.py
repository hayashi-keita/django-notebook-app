from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Q
from datetime import date, timedelta
from .models import DailyRecord
from .forms import DailyRecordForm
from accounts.mixins import StudentOnlyMixin, TeacherAndAdminOnlyMixin

class Index(TemplateView):
    template_name = 'notebook/index.html'

class DailyRecordCreateView(LoginRequiredMixin, StudentOnlyMixin, CreateView):
    model = DailyRecord
    form_class = DailyRecordForm
    template_name = 'notebook/record_form.html'
    success_url = reverse_lazy('notebook:student_record_list')
    
    # 処理開始前に重複チェック
    def dispatch(self, request, *args, **kwargs):
        self.record_date = date.today() - timedelta(days=1)
        # 提出済みなら即座にリダイレクト
        if DailyRecord.objects.filter(student=request.user, date_for=self.record_date).exists():
            messages.warning(request, f'{self.record_date}分の連絡帳は既に提出済みです。')
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        # 初期値記録日を設定
        return {'date_for': self.record_date}
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get_initial で設定した日付をコンテキストに追加
        # (self)に 'record_date' という属性が設定されているか判定
        if hasattr(self, 'record_date'):
            context['record_date'] = self.record_date
        # もし record_date が self に設定されていない場合は、再度計算する
        else:
            context['record_date'] = date.today() - timedelta(days=1)
        return context
    
    def form_valid(self, form):
        # フォーム送信時、生徒と記録日を自動セット
        form.instance.student = self.request.user
        form.instance.date_for = self.record_date
        messages.success(self.request, f'{self.record_date}分の連絡帳を提出しました。')
        return super().form_valid(form)

class StudentRecordListView(LoginRequiredMixin, StudentOnlyMixin, ListView):
    model = DailyRecord
    template_name = 'notebook/student_record_list.html'

    def get_queryset(self):
        return DailyRecord.objects.filter(student=self.request.user).order_by('date_for')

class StudentRecordDetailView(LoginRequiredMixin, StudentOnlyMixin, DetailView):
    model = DailyRecord
    template_name = 'notebook/student_record_detail.html'

    def get_queryset(self):
        queryset = DailyRecord.objects.filter(student=self.request.user).select_related(
            'read_by', 'student__classroom',
        )
        return queryset

class StudentRecordUpdateView(LoginRequiredMixin, StudentOnlyMixin, UpdateView):
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

class StudentRecordDeleteView(LoginRequiredMixin, StudentOnlyMixin, DeleteView):
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

class TeacherRecordListView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, ListView):
    model = DailyRecord
    template_name = 'notebook/teacher_record_list.html'

    def get_queryset(self):
        # 担任が受け持つクラスを取得
        homeroom_classes = self.request.user.homeroom_classes.all()
        # 担任クラスの生徒の記録のみに絞り込み、生徒・クラス情報をまとめて取得
        queryset = DailyRecord.objects.filter(
            student__classroom__in=homeroom_classes,
        ).select_related('student', 'student__classroom')
        # 未読を優先して日付の新しい順番に並び替え
        queryset = queryset.order_by('is_read', '-date_for')
        return queryset

class TeacherRecordDetailView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, DetailView):
    model = DailyRecord
    template_name = 'notebook/teacher_record_detail.html'
    # 担任は自分の生徒の記録しか見れない
    def get_queryset(self):
        homeroom_classes = self.request.user.homeroom_classes.all()
        # 担当クラスの生徒の記録のみに絞り込む
        queryset = DailyRecord.objects.filter(
            student__classroom__in=homeroom_classes
        ).select_related('student', 'student__classroom', 'read_by')
        return queryset
    # 既読処理アクション
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        record = self.object
        if 'mark_read' in request.POST and not record.is_read:
            # 既読フラグと確認者、確認日時セット
            record.is_read = True
            record.read_at = date.today()
            record.read_by = request.user
            record.save()
            messages.success(request, f'{record.date_for}分の連絡帳を既読処理しました。')
        # 処理後、同じページに戻るか、一覧画面に戻る
        return HttpResponseRedirect(reverse('notebook:teacher_record_list'))
    