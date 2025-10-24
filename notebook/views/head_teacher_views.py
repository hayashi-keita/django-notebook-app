from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Avg
from django.utils import timezone
from datetime import date, timedelta
from ..models import Classroom, DailyRecord, TeacherLog
from accounts.mixins import HeadTeacherAndAdminOnlyMixin
import json

CustomUser = get_user_model()

class HeadTeacherRecordListView(LoginRequiredMixin, HeadTeacherAndAdminOnlyMixin, ListView):
    model = DailyRecord
    template_name = 'notebook/head_teacher_record_list.html'
    paginate_by = 20

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
        user_grade = self.request.user.head_of_grade

        date_param = self.request.GET.get('date')
        if date_param:
            try:
                date_for = date.fromisoformat(date_param)
            except ValueError:
                date_for = self.get_default_schoolday()
        else:
            date_for = self.get_default_schoolday()
        self.selected_date = date_for
        
        queryset = DailyRecord.objects.filter(
            student__grade=user_grade,
            date_for=self.selected_date,
        ).select_related(
            'student', 'student__classroom', 'student__grade',
        ).order_by('-date_for')
        # クラス名によるフィルタリング（例: ?classroom=1組）
        classroom_name = self.request.GET.get('classroom')
        if classroom_name:
            if classroom_name and classroom_name.lower() != 'all':
                queryset = queryset.filter(student__classroom__name=classroom_name)
        # 確認フィルタ
        read_filter = self.request.GET.get('read', 'all')
        if read_filter == 'unread':
            queryset = queryset.filter(is_read=False)
        elif read_filter == 'read':
            queryset = queryset.filter(is_read=True)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_grade = self.request.user.head_of_grade
        # 担当学年に属するすべてのクラスのリストを取得し、テンプレートに渡す
        # これをフィルタリング用のドロップダウンリストに使用
        context['classrooms'] = Classroom.objects.filter(grade=user_grade).order_by('name')
        # 現在のフィルタ状態をテンプレートに渡す
        context['current_classroom'] = self.request.GET.get('classroom', 'all')
        context['current_read_filter'] = self.request.GET.get('read', 'all')
        context['selected_date'] = getattr(self, 'selected_date', self.get_default_schoolday())
        context['date_filter_value'] = context['selected_date'].isoformat()
        return context
    
class HeadTeacherRecordDetailView(LoginRequiredMixin, HeadTeacherAndAdminOnlyMixin, DetailView):
    model = DailyRecord
    template_name = 'notebook/head_teacher_record_detail.html'

    def get_queryset(self):
        user_grade = self.request.user.head_of_grade
        queryset = DailyRecord.objects.filter(
            student__grade=user_grade,
        ).select_related('student', 'student__classroom', 'student__grade',
        ).order_by('-date_for')
        return queryset

class HeadTeacherLogListView(LoginRequiredMixin, HeadTeacherAndAdminOnlyMixin, ListView):
    model = TeacherLog
    template_name = 'notebook/head_teacher_log_list.html'
    paginate_by = 10

    def get_queryset(self):
        current_grade = self.request.user.grade
        if not current_grade:
            return TeacherLog.objects.none()
        queryset = TeacherLog.objects.filter(
            student__grade=current_grade,
        ).select_related('student', 'teacher', 'student__classroom',
        ).order_by('-created_at')
        # 重要フラグフィルター
        important_param = self.request.GET.get('important')
        if important_param == 'true':
            queryset =queryset.filter(is_important=True)
        # 作成者フィルター
        teacher_pk_param = self.request.GET.get('teacher_pk')
        if teacher_pk_param:
            try:
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
            teachers_in_grade = CustomUser.objects.filter(
                grade=current_grade,
                role__in=['TEACHER', 'ADMIN']
            ).order_by('full_name')
        context['teacher_in_grade'] = teachers_in_grade
        # 選択された先生オブジェクトをコンテキストに追加する
        selected_teacher_pk = self.request.GET.get('teacher_pk')
        context['selected_teacher_pk'] = selected_teacher_pk
        selected_teacher_obj = None

        if selected_teacher_pk:
            try:
                # CustomUser (Teacher) モデルからPKで先生を検索
                selected_teacher_obj = CustomUser.objects.get(pk=selected_teacher_pk)
                # 存在しない場合はNoneのまま
            except CustomUser.DoesNotExist:
                pass
        context['selected_teacher_obj'] = selected_teacher_obj
        return context
        
class HeadTeacherLogDetailView(LoginRequiredMixin, HeadTeacherAndAdminOnlyMixin, DetailView):
    model = TeacherLog
    template_name = 'notebook/head_teacher_log_detail.html'

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

class HeadTeacherRecordGraphView(LoginRequiredMixin, HeadTeacherAndAdminOnlyMixin, TemplateView):
    template_name = 'notebook/head_teacher_record_graph.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        #フィルタリングパラメータの取得
        filter_type = request.GET.get('filter', 'all')
        filter_value = request.GET.get('value', '')

        current_grade = request.user.grade
        # 担当学年が存在しない場合はデータを表示しない
        if not current_grade:
            context['total_records'] = 0
            context['datasets_json'] = json.dumps([])
            context['error_message'] = 'データ閲覧には、ユーザー情報に学年設定が必要です。'
            return context

        # クエリセット
        all_record_base = DailyRecord.objects.select_related('student__classroom', 'student').order_by('date_for')
        # 担当学年
        my_grade_record_base = all_record_base.filter(student__grade=current_grade)
        # グラフ表示データとベンチマーク
        main_queryset = my_grade_record_base
        compare_queryset = all_record_base
        context['current_filter_label'] = f'{current_grade}学年全体の平均'
        context['compare_label'] = '学校全体の平均'

        if filter_type == 'classroom' and filter_value:
            # フィルタ対象：特定クラス
            main_queryset = my_grade_record_base.filter(student__classroom__pk=filter_value)
            try:
                classroom = get_object_or_404(Classroom, pk=filter_value)
                context['current_filter_label'] = f'{current_grade} {classroom.name}の平均'
            except:
                pass
        
        if not main_queryset.exists():
            context['total_records'] = 0
            context['datasets_json'] = json.dumps([])
            context['error_message'] = '該当するレコードがありません。フィルタ条件を変更してください。'
            classrooms_in_grade = Classroom.objects.filter(grade=current_grade).order_by('name')
            context['available_classrooms'] = json.dumps([
                {'pk': c.pk, 'name': f'{c.grade}年 {c.name}'} for c in classrooms_in_grade
            ])
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
        main_physical_map, main_mental_map = get_average_data(main_queryset)
        if compare_queryset:
            compare_physical_map, compare_mental_map = get_average_data(compare_queryset)
        else:
            compare_physical_map, compare_mental_map = {}, {}
        
        all_dates_set = set(main_physical_map.keys()) | set(compare_physical_map.keys())
        sorted_dates = sorted(list(all_dates_set))
        main_phys_data = [main_physical_map.get(d) for d in sorted_dates]
        main_ment_data = [main_mental_map.get(d) for d in sorted_dates]
        compare_phys_data = [compare_physical_map.get(d) for d in sorted_dates]
        compare_ment_data = [compare_mental_map.get(d) for d in sorted_dates]

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
        datasets.append({
            'label': f"体調({context.get('compare_label', '比較対象')})",
            'data': compare_phys_data,
            'borderColor': 'rgb(108, 117, 125)',
            'borderDash': [5, 5],
            'tension': 0.3,
            'pointRadius': 3,
            'pointHoverRadius': 5,
            'spanGaps': True,
        })
        datasets.append({
            'label': f"メンタル({context.get('compare_label', '比較対象')})",
            'data': compare_ment_data,
            'borderColor': 'rgb(108, 117, 125)',
            'borderDash': [5, 5],
            'tension': 0.3,
            'pointRadius': 3,
            'pointHoverRadius': 5,
            'spanGaps': True,
        })
        context['yAxisLabel'] = '評価レベル（1-10）'

        # フィルタオプションと現在の設定をコンテキストに追加
        context['dates_json'] = json.dumps(sorted_dates)
        context['datasets_json'] = json.dumps(datasets)
        context['total_records'] = all_record_base.count()
        # フィルタリングオプションのための生徒と学年を取得
        classrooms_in_grade = Classroom.objects.filter(grade=current_grade).order_by('name')
        context['available_classrooms'] = json.dumps([{'pk': c.pk, 'name': f'{c.grade}年 {c.name}'} for c in classrooms_in_grade])
        context['filter_params'] = json.dumps({'filter': filter_type, 'value': filter_value})

        return context