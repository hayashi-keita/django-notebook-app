from os import name
from django.urls import path

from notebook.views import notification_views
from .views import main_views, student_views, teacher_views, admin_views


app_name = 'notebook'

urlpatterns = [
    # トップページ
    path('', main_views.Index.as_view(), name='index'),
    # 連絡帳作成
    path('record/create/', student_views.DailyRecordCreateView.as_view(), name='record_create'),
    # 生徒関連
    path('student/records/', student_views.StudentRecordListView.as_view(), name='student_record_list'),
    path('student/record/<int:pk>/detail/', student_views.StudentRecordDetailView.as_view(), name='student_record_detail'),
    path('student/record/<int:pk>/update/', student_views.StudentRecordUpdateView.as_view(), name='student_record_update'),
    path('student/record/<int:pk>/delete/', student_views.StudentRecordDeleteView.as_view(), name='student_record_delete'),
    path('student/record/graph/', student_views.StudentRecordGraphView.as_view(), name='student_record_graph'),
    # 担任関連
    path('teacher/records/', teacher_views.TeacherRecordListView.as_view(), name='teacher_record_list'),
    path('teacher/record/<int:pk>/detail/', teacher_views.TeacherRecordDetailView.as_view(), name='teacher_record_detail'),
    path('teacher/record/<int:record_pk>/memo/create/', teacher_views.MemoCreateView.as_view(), name='record_memo_create'),
    path('teacher/record/<int:pk>/memo/update/', teacher_views.MemoUpdateView.as_view(), name='record_memo_update'),
    path('teacher/logs/', teacher_views.TeacherLogListView.as_view(), name='teacher_log_list'),
    path('teacher/log/<int:student_pk>/create/', teacher_views.TeacherLogCreateView.as_view(), name='teacher_log_create'),
    path('teacher/record/graph/', teacher_views.TeacherRecordGraphView.as_view(), name='teacher_record_graph'),
    # 管理者向け学年管理
    path('management/grades/', admin_views.GradeListView.as_view(), name='grade_list'),
    path('management/grade/create/', admin_views.GradeCreateView.as_view(), name='grade_create'),
    path('management/grade/<int:pk>/update/', admin_views.GradeUpdateView.as_view(), name='grade_update'),
    path('management/grade/<int:pk>/delete/', admin_views.GradeDeleteView.as_view(), name='grade_delete'),
    # 管理者向けクラス管理
    path('management/classrooms/', admin_views.ClassroomListView.as_view(), name='classroom_list'),
    path('management/classroom/create/', admin_views.ClassroomCreateView.as_view(), name='classroom_create'),
    path('management/classroom/<int:pk>/update/', admin_views.ClassroomUpdateView.as_view(), name='classroom_update'),
    path('management/classroom/<int:pk>/delete/', admin_views.ClassroomDeleteView.as_view(), name='classroom_delete'),
    # 通知管理
    path('notifications/', notification_views.NotificationListView.as_view(), name='notification_list'),
]