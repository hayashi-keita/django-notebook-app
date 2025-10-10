from django import forms
from .models import DailyRecord, Grade, Classroom, Memo, TeacherLog

class DailyRecordForm(forms.ModelForm):
    class Meta:
        model = DailyRecord
        fields = ['physical_level', 'physical_condition', 'mental_level', 'mental_condition', 'reflection']
        widgets = {
            'physical_condition': forms.TextInput(attrs={'class': 'form-control'}),
            'mental_condition': forms.TextInput(attrs={'class': 'form-control'}),
            'reflection': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'physical_level': '体調（10段階評価）',
            'physical_condition': '体調補足メモ',
            'mental_level': 'メンタル（10段階評価）',
            'mental_condition': 'メンタル補足メモ',
            'reflection': '今日の振り返り（授業や部活、気づいたこと）',
        }
        help_texts = {
            'physical_level': '1が最低、10が最高の状態です。',
            'physical_condition': '具体的に体調に関して気づいた点があれば記入してください。',
            'mental_level': '1が最低、10が最高の状態です。',
            'mental_condition': '具体的にメンタルに関して気づいた点があれば記入してください。',
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
                'class': 'form-control',
                'rows': 3,
                'placeholder': '指導メモを記入してください',
            }),
            'stamp': forms.RadioSelect,
        }
        labels = {'text': '指導メモ', 'stamp': 'スタンプリアクション'}

class TeacherLogForm(forms.ModelForm):
    class Meta:
        model = TeacherLog
        fields = ['text', 'is_important']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '生徒の状況に関するメモ（他の先生にも共有されます）',
            }),
            'is_important': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'text': '共有メモ',
            'is_important': '学年会議での重要議題としてマーク'
        }