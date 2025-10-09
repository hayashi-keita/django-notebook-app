from django import forms
from .models import DailyRecord, Grade, Classroom, Memo

class DailyRecordForm(forms.ModelForm):
    class Meta:
        model = DailyRecord
        fields = ['physical_condition', 'mental_condition', 'reflection']
        widgets = {
            'physical_condition': forms.TextInput(attrs={'class': 'form-control'}),
            'mental_condition': forms.TextInput(attrs={'class': 'form-control'}),
            'reflection': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'physical_condition': '体調（例： よかった、疲れ気味）',
            'mental_condition': 'メンタル（例： ふつう、元気）',
            'reflection': '今日の振り返り（授業や部活、気づいたこと）',
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['name']
        labels = {'name': '学年名'}

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name']
        labels = {'name': 'クラス名'}

class MemoForm(forms.ModelForm):
    
    class Meta:
        model = Memo
        fields = ['text', 'stamp']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': '指導メモを記入してください',
                'class': 'form-control',
            }),
            'stamp': forms.RadioSelect,
        }
        labels = {'text': '指導メモ', 'stamp': 'スタンプリアクション'}

