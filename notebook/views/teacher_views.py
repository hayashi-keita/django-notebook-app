from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from datetime import date
from ..models import DailyRecord, Memo, TeacherLog
from accounts.models import CustomUser
from ..forms import MemoForm, TeacherLogForm
from accounts.mixins import TeacherAndAdminOnlyMixin

class TeacherRecordListView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, ListView):
    model = DailyRecord
    template_name = 'notebook/teacher_record_list.html'
    paginate_by = 10

    def get_queryset(self):
        # 担任が受け持つクラスを取得
        homeroom_classes = self.request.user.homeroom_classes.all()
        #デフォルトで今日の日付にフィルター
        today = timezone.localdate()
        selected_date = today
        # 2. 日付パラメータがあれば適用
        date_param = self.request.GET.get('date')
        if date_param:
            try:
                from datetime import date
                selected_date = date.fromisoformat(date_param)
            except ValueError:
                pass
        # 3. 担当クラスと日付で基本クエリを構築
        queryset = DailyRecord.objects.filter(
            student__classroom__in=homeroom_classes,
            date_for=selected_date,
        ).select_related('student', 'student__classroom', 'read_by',
        ).prefetch_related('memos__teacher')
        # 4. ステータスによる絞り込み
        status_param = self.request.GET.get('status')
        if status_param == 'unread':
            queryset = queryset.filter(is_read=False)
        elif status_param == 'read':
            queryset = queryset.filter(is_read=True)
        
        queryset = queryset.order_by('student__student_id')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.request.GET.get('status', 'all')
        return context

class TeacherRecordDetailView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, DetailView):
    model = DailyRecord
    template_name = 'notebook/teacher_record_detail.html'
    # 担任は自分の生徒の記録しか見れない
    def get_queryset(self):
        homeroom_classes = self.request.user.homeroom_classes.all()
        # 担当クラスの生徒の記録のみに絞り込む
        queryset = DailyRecord.objects.filter(
            student__classroom__in=homeroom_classes,
        ).select_related('student', 'student__classroom', 'read_by',
        ).prefetch_related('memos__teacher')
        return queryset
    # メモ情報とフォームを追加
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self.get_object()
        current_memo = record.memos.first()
        context['current_memo'] = current_memo
        if current_memo:
            context['memo_form'] = MemoForm(instance=current_memo)
        else:
            context['memo_form'] = MemoForm()
        return context
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
        return HttpResponseRedirect(reverse('notebook:teacher_record_detail', kwargs={'pk': record.pk}))

# 連絡帳メモ関連
class MemoCreateView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, CreateView):
   model = Memo
   form_class = MemoForm
   template_name = 'notebook/teacher_record_detail.html'

   def dispatch(self, request, *args, **kwargs):
       # 既にメモが存在する場合、CreateViewではなくUpdateViewにリダイレクトする
       self.record = get_object_or_404(DailyRecord, pk=kwargs['record_pk'])
       if self.record.memos.exists():
           memo = self.record.memos.first()
           return redirect('notebook:record_memo_update', pk=memo.pk)
       return super().dispatch(request, *args, **kwargs)
   
   def form_valid(self, form):
       # 外部キーとメモ作成者を設定
       form.instance.record = self.record
       form.instance.teacher = self.request.user
       messages.success(self.request, '指導メモを登録しました。')
       return super().form_valid(form)
   
   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context['record'] = self.record
       return context
   
   def get_success_url(self):
       return reverse('notebook:teacher_record_detail', kwargs={'pk': self.record.pk })
   
class MemoUpdateView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, UpdateView):
    model = Memo
    form_class = MemoForm
    template_name = 'notebook/teacher_record_detail.html'
    
    def form_valid(self, form):
        messages.success(self.request, '指導メモを更新しました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record'] = self.object.record
        return context
    
    def get_success_url(self):
        return reverse('notebook:teacher_record_detail', kwargs={'pk': self.object.record.pk})

class TeacherLogCreateView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, CreateView):
    model = TeacherLog
    form_class = TeacherLogForm
    template_name = 'notebook/teacher_log_form.html'
    success_url = reverse_lazy('notebook:teacher_log_list')

    # ログ作成前に先生の学年設定を確認する
    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        if not user.grade:
            messages.error(request, 'メモを作成するには、あなたのユーザー情報に「学年」を設定してください。')
            return redirect('notebook:teacher_log_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        student_pk = self.kwargs.get('student_pk')
        student_instance = get_object_or_404(CustomUser, pk=student_pk, role='STUDENT')
        form.instance.teacher = self.request.user
        form.instance.student = student_instance
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student_pk = self.kwargs.get('student_pk')
        target_student = get_object_or_404(CustomUser, pk=student_pk, role='STUDENT')
        context['target_student'] = target_student
        return context

class TeacherLogListView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, ListView):
    model = TeacherLog
    template_name ='notebook/teacher_log_list.html'
    paginate_by = 10

    def get_queryset(self):
        # ログインしている先生の学年を取得
        current_grade = self.request.user.grade
        # 学年が設定されていない先生(管理者など)の場合は空のクエリセットを返す
        if not current_grade:
            return TeacherLog.objects.none()
        #「同じ学年の生徒」全員のログを取得
        queryset = TeacherLog.objects.filter(
            student__grade=current_grade,
        ).select_related(
            'student', 'teacher', 'student__classroom')
        # 1. 重要フラグによる絞り込み (is_important)
        important_param = self.request.GET.get('important')
        if important_param == 'true':
            queryset = queryset.filter(is_important=True)
        # 2. 作成者による絞り込み (teacher_pk)
        teacher_pk_param = self.request.GET.get('teacher_pk')
        if teacher_pk_param:
            try:
                # PKが有効な数値か確認
                teacher_pk = int(teacher_pk_param)
                queryset = queryset.filter(teacher__pk=teacher_pk)
            except ValueError:
                pass
        
        queryset = queryset.order_by('-is_important', '-created_at')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートで選択状態を維持するためにGETパラメータを渡す
        context['selected_important'] = self.request.GET.get('important', 'all')
        context['selected_teacher_pk'] = self.request.GET.get('teacher_pk')
        # 作成者フィルター用のオプションリスト (同じ学年の先生)
        current_grade = self.request.user.grade
        teachers_in_grade = CustomUser.objects.none()
        if current_grade:
            # 学年内の先生リストを取得
            teachers_in_grade = CustomUser.objects.filter(
                grade=current_grade,
                role__in=['TEACHER', 'ADMIN'],
            ).order_by('full_name')
        context['teachers_in_grade'] = teachers_in_grade
        # 選択された先生オブジェクトを特定し、テンプレートに渡す
        selected_teacher_obj = None
        teacher_pk = self.request.GET.get('teacher_pk')
        if teacher_pk and teacher_pk.isdigit():
            try:
                # teachers_in_gradeから該当する先生を検索
                selected_teacher_obj = teachers_in_grade.get(pk=int(teacher_pk))
                # 存在しない場合はNoneのまま
            except CustomUser.DoesNotExist:
                pass
        context['selected_teacher_obj'] = selected_teacher_obj

        return context