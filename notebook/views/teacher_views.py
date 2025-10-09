from django.views.generic import ListView, DetailView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from datetime import date
from ..models import DailyRecord, Memo
from ..forms import MemoForm
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