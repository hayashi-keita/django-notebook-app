from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, AuthenticationForm
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'