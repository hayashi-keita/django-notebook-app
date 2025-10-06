from django.contrib import admin
from .models import Grade, Classroom, DailyRecord

admin.site.register(Grade)
admin.site.register(Classroom)
admin.site.register(DailyRecord)
