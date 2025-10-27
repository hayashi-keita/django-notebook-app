from django.views.generic import ListView, DetailView, UpdateView, CreateView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from django.db.models import  Avg, Prefetch
from datetime import date, timedelta
from ..models import DailyRecord, Memo, TeacherLog, Notification
from ..forms import MemoForm, TeacherLogForm
from accounts.mixins import TeacherAndAdminOnlyMixin
import json

CustomUser = get_user_model()

class TeacherRecordListView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, ListView):
    model = CustomUser
    template_name = 'notebook/teacher_record_list.html'
    paginate_by = 30

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

    
    def get_queryset(self):
        # 担任が担当するクラスを取得
        homeroom_classes = self.request.user.homeroom_classes.all()
        # date_for をメソッドの冒頭で初期化する
        date_for = None
        # 選択された日付の特定（デフォルト昨日）
        date_param = self.request.GET.get('date')
        if date_param:
            try:
                date_for = date.fromisoformat(date_param)
            except ValueError:
                # パラメータが無効ならデフォルトに戻す
                date_for = self.get_default_schoolday()
        else:   # パラメータがない場合、デフォルトで「昨日」の記録日を選択
            date_for = self.get_default_schoolday()
        
        self.selected_date = date_for
        # 担任クラスに所属し、ロールが生徒のユーザーを取得
        queryset = CustomUser.objects.filter(
            classroom__in=homeroom_classes,
            role='STUDENT',
        ).order_by('student_id')
        # 選択された日付のレコードを取得するクエリ
        records_for_date = DailyRecord.objects.filter(
            date_for=self.selected_date,
        ).select_related('read_by')
        # Prefetchを使って、生徒リストにその日の記録を紐づける
        queryset = queryset.prefetch_related(
            Prefetch('daily_records', queryset=records_for_date, to_attr='record_of_the_day'),
        )
        # ステータスによる生徒リストの絞り込み
        status_param = self.request.GET.get('status')
        if status_param == 'submitted':
            # 提出済の生徒のみ
            queryset = queryset.filter(daily_records__date_for=self.selected_date)
        elif status_param == 'unsubmitted':
            # 未提出の生徒のみ
            queryset = queryset.exclude(daily_records__date_for=self.selected_date)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートに渡すデータ
        context['selected_date'] = self.selected_date
        context['date_filter_value'] = self.selected_date.isoformat()
        context['selected_status'] = self.request.GET.get('status', 'all')
        # 通知処理
        homeroom_classes = self.request.user.homeroom_classes.all()
        relevant_student_pks = CustomUser.objects.filter(
            classroom__in=homeroom_classes,
            role='STUDENT',
        ).values_list('pk', flat=True)
        unread_record_count = DailyRecord.objects.filter(
            student__pk__in=relevant_student_pks,
            date_for=self.selected_date,
            is_read=False,
        ).count()
        context['unread_record_count'] = unread_record_count

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
        current_memo = getattr(record, 'memos', None)
        context['current_memo'] = current_memo
        if current_memo:
            context['memo_form'] = MemoForm(instance=current_memo)
        else:
            context['memo_form'] = MemoForm()
        return context
    # 既読処理 / 既読取り消しアクション
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        record = self.object
        # --- 既読処理アクション ---
        if 'mark_read' in request.POST and not record.is_read:
            record.is_read = True
            record.read_at = date.today()
            record.read_by = request.user
            record.save(update_fields=['is_read', 'read_at', 'read_by'])
            messages.success(request, f'{record.date_for}分の連絡帳を既読処理しました。')
            Notification.objects.create(
                sender=request.user,
                recipient=record.student,
                message=f'{record.date_for}分の連絡帳が{request.user.full_name}先生に確認されました。',
                related_record=record,
            )
        # --- 既読取り消し（差し戻し）アクション ---
        elif 'unmark_read' in request.POST and record.is_read:
            record.is_read = False
            record.read_at = None
            record.read_by = None
            record.save(update_fields=['is_read', 'read_at', 'read_by'])
            messages.info(request, f'{record.date_for}分の連絡帳の既読処理を取り消し、未読に戻しました。')
            Notification.objects.create(
                sender=request.user,
                recipient=record.student,
                message=f'{record.date_for}分の連絡帳が{request.user.full_name}先生に差し戻しされました。',
                related_record=record,
            )
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
        memo = getattr(self.record, 'memos', None)
        if memo:
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

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'ADMIN':
            return queryset
        return queryset.filter(teacher=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, '指導メモを更新しました。')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record'] = self.object.record
        return context
    
    def get_success_url(self):
        return reverse('notebook:teacher_record_detail', kwargs={'pk': self.object.record.pk})

class MemoDeleteView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, DeleteView):
    model = Memo
    template_name = 'notebook/memo_delete.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_admin:
            return queryset
        return queryset.filter(teacher=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['record'] = self.object.record
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '指導メモを削除しました。')
        return super().delete(request, *args, **kwargs)
    
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
        context['selected_teacher_pk'] = self.request.GET.get('teacher_pk', '')
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

class TeacherLogUpdateView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, UpdateView):
    model = TeacherLog
    form_class = TeacherLogForm
    template_name = 'notebook/teacher_log_form.html'
    success_url = reverse_lazy('notebook:teacher_log_list')

    def get_queryset(self):
        if self.request.user.is_admin:
            return TeacherLog.objects.all()
        return TeacherLog.objects.filter(teacher=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'ログを更新しました。')
        return super().form_valid(form)

class TeacherLogDeleteView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, DeleteView):
    model = TeacherLog
    template_name = 'notebook/teacher_log_delete.html'
    success_url = reverse_lazy('notebook:teacher_log_list')

    def get_queryset(self):
        if self.request.user.is_admin:
            return TeacherLog.objects.all()
        return TeacherLog.objects.filter(teacher=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'ログを削除しました。')
        return super().delete(request, *args, **kwargs)

class TeacherLogDetailView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, DetailView):
    model = TeacherLog
    template_name = 'notebook/teacher_log_detail.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return TeacherLog.objects.all()
        
        current_grade = user.grade
        if not current_grade:
            return TeacherLog.objects.none()
        
        return TeacherLog.objects.filter(
            student__grade=current_grade,
        ).select_related('student', 'teacher', 'student__classroom')

# 先生が全生徒の評価推移を把握するためのグラフビュー
class TeacherRecordGraphView(LoginRequiredMixin, TeacherAndAdminOnlyMixin, TemplateView):
    template_name = 'notebook/teacher_record_graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        #フィルタリングパラメータの取得
        filter_type = request.GET.get('filter', 'all')
        filter_value = request.GET.get('value', '')

        current_classroom = request.user.classroom
        # 担当クラスが存在しない場合はデータを表示しない
        if not current_classroom:
            context['total_records'] = 0
            context['datasets_json'] = json.dumps([])
            context['filter_params'] = json.dumps({'filter': filter_type, 'value': filter_value})
            return context

        # クエリセット
        all_record_base = DailyRecord.objects.select_related('student__classroom', 'student').order_by('date_for')
        # 担当クラス
        my_class_record_base = all_record_base.filter(student__classroom=current_classroom)
        # グラフ表示データとベンチマーク
        main_queryset = my_class_record_base
        compare_queryset = None
        if filter_type == 'grade' and filter_value:
            # フィルタ対象：担当クラス内の特定学年
            main_queryset = my_class_record_base.filter(student__grade=filter_value)
            context['current_filter_label'] = f'担当クラス内： {filter_value}学年の平均'
            # 比較対象：担当クラスの同学年（filter_value）の全平均
            compare_queryset = all_record_base.filter(student__grade=filter_value)
            context['compare_label'] = f'他クラス： {filter_value}学年の平均'
        
        elif filter_type == 'student' and filter_value:
            # 特定の生徒でフィルタリング
            main_queryset = my_class_record_base.filter(student__pk=filter_value)
            try:
                student = main_queryset.first().student
                context['current_filter_label'] = f'生徒個人： {student.get_full_name()}'
                # 比較対象：その生徒が所属する学年のクラス平均
                compare_queryset = all_record_base.filter(
                    student__classroom=current_classroom)
                context['compare_label'] = f'他クラス： {student.grade}学年の平均'
            except AttributeError:
                context['current_filter_label'] = '特定生徒'
        
        else:  # filter_type == 'all' またはデフォルト (担当クラス全体平均)
            # フィルタ対象：担当クラス全体
            context['current_filter_label'] = '担当クラス全体の平均'
            # 比較対象：担当クラス外の全レコード（学校全体の平均）
            compare_queryset = all_record_base
            context['compare_label'] = '学校全体の平均'
        
        if not main_queryset.exists():
            all_students = current_classroom.members.filter(role='STUDENT').order_by('grade', 'pk')
            grades = sorted(list(set(s.grade.number for s in all_students if s.grade is not None)))

            context['total_records'] = 0
            context['datasets_json'] = json.dumps([])
            context['error_message'] = '該当するレコードがありません。フィルタ条件を変更してください。'
            context['available_grades'] = json.dumps(grades)
            context['available_students'] = json.dumps([{'pk': s.pk, 'name': s.full_name} for s in all_students])
            context['filter_params'] = json.dumps({'filter': filter_type, 'value': filter_value})
            return context

        # データを取得・整形するヘルパー関数
        def get_average_data(queryset):
            """クエリセットから日ごとの体調とメンタルの平均を計算し、マップを返す"""
            aggregated_data = queryset.values('date_for').annotate(
                avg_physical=Avg('physical_level'),
                avg_mental=Avg('mental_level'),
            ).order_by('date_for')
            # 小数点第二位までをマップに格納
            avg_physical_map = {item['date_for'].strftime('%Y-%m-%d'): round(item['avg_physical'], 2) for item in aggregated_data}
            avg_mental_map = {item['date_for'].strftime('%Y-%m-%d'): round(item['avg_mental'], 2) for item in aggregated_data}

            return avg_physical_map, avg_mental_map
        
        #  グラフのメインデータセットを生成
        datasets = []
        sorted_dates = []
        if filter_type == 'student' and filter_value:
            # A. 個別生徒モード: 個人のデータをそのまま表示
            records = main_queryset.order_by('date_for')
            physical_data = [r.physical_level for r in records]
            mental_data = [r.mental_level for r in records]
            sorted_dates = [r.date_for.strftime('%Y-%m-%d') for r in records]

            datasets.append({
                'label': '体調（個人）',
                'data': physical_data,
                'borderColor': 'rgb(54, 162, 235)',
                'tension': 0.3,
                'pointRadius': 5,
            })
            datasets.append({
                'label': 'メンタル（個人）',
                'data': mental_data,
                'borderColor': 'rgb(255, 99, 132)',
                'tension': 0.3,
                'pointRadius': 5,
            })
            if compare_queryset:
                compare_physical_map, compare_mental_map = get_average_data(compare_queryset)
                compare_phys_data = [compare_physical_map.get(d) for d in sorted_dates]
                compare_ment_data = [compare_mental_map.get(d) for d in sorted_dates]
                datasets.append({
                'label': f"体調（{context.get('compare_label', '比較対象')}）",
                'data': compare_phys_data,
                'borderColor': 'rgb(108, 117, 125)',
                'borderDash': [5, 5],
                'tension': 0.3,
                'pointRadius': 3,
                'pointHoverRadius': 5,
                'spanGaps': True,
                })
                datasets.append({
                    'label': f"メンタル（{context.get('compare_label', '比較対象')}）",
                    'data': compare_ment_data,
                    'borderColor': 'rgb(108, 117, 125)',
                    'borderDash': [5, 5],
                    'tension': 0.3,
                    'pointRadius': 3,
                    'pointHoverRadius': 5,
                    'spanGaps': True,
                })
            context['yAxisLabel'] = '評価レベル（1-10）'

        else:
            # B. グループ平均モード: 担当クラス/学年平均とベンチマークを比較
            main_physical_map, main_mental_map = get_average_data(main_queryset)
            # 比較データ（ベンチマーク）の生成
            if compare_queryset:
                compare_physical_map, compare_mental_map = get_average_data(compare_queryset)
            else:
                compare_physical_map, compare_mental_map = {}, {}
            # グラフに使う全日付を統合
            all_dates_set = set(main_physical_map.keys()) | set(compare_physical_map.keys())
            sorted_dates = sorted(list(all_dates_set))
            # グラフデータ配列の生成
            main_phys_data = [main_physical_map.get(d) for d in sorted_dates]
            main_ment_data = [main_mental_map.get(d) for d in sorted_dates]
            compare_phys_data = [compare_physical_map.get(d) for d in sorted_dates]
            compare_ment_data = [compare_mental_map.get(d) for d in sorted_dates]
            # データセットに追加 (メインデータ)
            datasets.append({
                'label': '体調平均（メイン）',
                'data': main_phys_data,
                'borderColor': 'rgb(54, 162, 235)',
                'tension': 0.3,
                'pointRadius': 5,
                'spanGaps': True,
            })
            datasets.append({
                'label': 'メンタル平均（メイン）',
                'data': main_ment_data,
                'borderColor': 'rgb(255, 99, 132)',
                'tension': 0.3,
                'pointRadius': 5,
                'spanGaps': True,
            })
            # データセットに追加 (比較データ - ベンチマーク)
            datasets.append({
                'label': f"体調（{context.get('compare_label', '比較対象')}）",
                'data': compare_phys_data,
                'borderColor': 'rgb(108, 117, 125)',
                'borderDash': [5, 5],
                'tension': 0.3,
                'pointRadius': 3,
                'pointHoverRadius': 5,
                'spanGaps': True,
            })
            datasets.append({
                'label': f"メンタル（{context.get('compare_label', '比較対象')}）",
                'data': compare_ment_data,
                'borderColor': 'rgb(108, 117, 125)',
                'borderDash': [5, 5],
                'tension': 0.3,
                'pointRadius': 3,
                'pointHoverRadius': 5,
                'spanGaps': True,
            })
            context['yAxisLabel'] = '平均評価レベル（1-10）'

        # フィルタオプションと現在の設定をコンテキストに追加
        context['dates_json'] = json.dumps(sorted_dates)
        context['datasets_json'] = json.dumps(datasets)
        context['total_records'] = all_record_base.count()
        # フィルタリングオプションのための生徒と学年を取得
        all_students = current_classroom.members.filter(role='STUDENT').order_by('grade', 'pk')
        grades = sorted(list(set(s.grade.number for s in all_students if s.grade is not None)))

        context['available_grades'] = json.dumps(grades)
        context['available_students'] = json.dumps([{'pk': s.pk, 'name': s.full_name} for s in all_students])
        context['filter_params'] = json.dumps({'filter': filter_type, 'value': filter_value})

        return context