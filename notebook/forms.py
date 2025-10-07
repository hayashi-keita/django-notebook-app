from django import forms
from .models import DailyRecord

class DailyRecordForm(forms.ModelForm):
    class Meta:
        model = DailyRecord
        fields = ['physical_condition', 'mental_condition', 'reflection']
        widgets = {
            'physical': forms.TextInput(attrs={'class': 'form-control'}),
            'mental_condition': forms.TextInput(attrs={'class': 'form-control'}),
            'reflection': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'physical_condition': '体調（例： よかった、疲れ気味）',
            'mental_condition': 'メンタル（例： ふつう、元気）',
            'reflection': '今日の振り返り（授業や部活、気づいたこと）',
        }