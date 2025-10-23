from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('追加情報', {'fields': ('role', 'grade', 'classroom', 'full_name', 'student_id', 'gender')}),
    )
    list_display = ('username', 'email', 'role', 'grade', 'classroom', 'full_name', 'student_id', 'gender')

admin.site.register(CustomUser, CustomUserAdmin)
