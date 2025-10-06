from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = (
            'username', 'full_name', 'role', 'email', 'grade', 'classroom', 'full_name', 'gender')
        labels = {
            'username': 'ユーザー名',
            'full_name': '氏名',
            'role': '所属',
            'email': 'メールアドレス',
            'grade': '学年',
            'classroom': 'クラス',
            'gender': '性別',
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = (
            'username', 'full_name', 'role', 'email', 'grade', 'classroom', 'full_name', 'gender')
        labels = {
            'username': 'ユーザー名',
            'full_name': '氏名',
            'role': '所属',
            'email': 'メールアドレス',
            'grade': '学年',
            'classroom': 'クラス',
            'gender': '性別',
        }