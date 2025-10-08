from os import name
from django.urls import path

from notebook import admin_views
from . import views
from . import admin_views

app_name = 'notebook'

urlpatterns = [
    # トップページ
    path('', views.Index.as_view(), name='index'),
    # 連絡帳作成
    path('record/create/', views.DailyRecordCreateView.as_view(), name='record_create'),
    # 生徒関連
    path('student/records/', views.StudentRecordListView.as_view(), name='student_record_list'),
    path('student/record/<int:pk>/detail/', views.StudentRecordDetailView.as_view(), name='student_record_detail'),
    path('student/record/<int:pk>/update/', views.StudentRecordUpdateView.as_view(), name='student_record_update'),
    path('student/record/<int:pk>/delete/', views.StudentRecordDeleteView.as_view(), name='student_record_delete'),
    # 担任関連
    path('teacher/records/', views.TeacherRecordListView.as_view(), name='teacher_record_list'),
    path('teacher/record/<int:pk>/detail/', views.TeacherRecordDetailView.as_view(), name='teacher_record_detail'),
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
]