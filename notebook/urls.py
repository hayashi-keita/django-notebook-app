from django.urls import path
from . import views

app_name = 'notebook'

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('record/create/', views.DailyRecordCreateView.as_view(), name='record_create'),
    path('student/records/', views.StudentRecordListView.as_view(), name='student_record_list'),
    path('student/<int:pk>/detail/', views.StudentRecordDetailView.as_view(), name='student_record_detail'),
    path('teacher/records/', views.TeacherRecordListView.as_view(), name='teacher_record_list'),
    path('teacher/<int:pk>/detail/', views.TeacherRecordDetailView.as_view(), name='teacher_record_detail'),
]