from venv import create
from django.db import models
from django.conf import settings

class Grade(models.Model):
    number = models.PositiveSmallIntegerField(verbose_name='学年')
    name = models.CharField(max_length=50, blank=True, verbose_name='学年名')

    def __str__(self):
        return f'{self.number}年{self.name}'

class Classroom(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='classrooms')
    name = models.CharField(max_length=50, verbose_name='クラス名')
    homeroom_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='homeroom_classes',
        verbose_name='担任教師'
    )

    def __str__(self):
        return f'{self.grade} {self.name}'

class DailyRecord(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_records')
    date_for = models.DateField(verbose_name='記録日')
    created_at = models.DateTimeField(auto_now_add=True)
    physical_condition = models.CharField(max_length=100, verbose_name='体調')
    mental_condition = models.CharField(max_length=100, verbose_name='メンタル')
    reflection = models.TextField(blank=True, verbose_name='振り返り')
    is_read = models.BooleanField(default=False, verbose_name='既読')
    read_at = models.DateField(blank=True, null=True)
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='checked_records',
        verbose_name='確認者',
    )

    class Meta:
        unique_together = ('student', 'date_for')
    
    def __str__(self):
        return f'{self.student.username} - {self.date_for}'