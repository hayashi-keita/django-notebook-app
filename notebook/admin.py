from django.contrib import admin
from .models import Grade, Classroom, DailyRecord, Memo, TeacherLog, Notification

admin.site.register(Grade)
admin.site.register(Classroom)
admin.site.register(DailyRecord)
admin.site.register(Memo)
admin.site.register(TeacherLog)
admin.site.register(Notification)
