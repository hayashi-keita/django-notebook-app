from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('STUDENT', '生徒'),
        ('TEACHER', '先生'),
        ('ADMIN', '管理者'),
    )
    GENDER_CHOICES = (
        ('male', '男性'),
        ('female', '女性'),
        ('other', 'その他'),
        ('no_answer', '回答しない'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    grade = models.ForeignKey(
        'notebook.Grade',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users',
        verbose_name='学年',
    )
    classroom = models.ForeignKey(
        'notebook.Classroom',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='members',
        verbose_name='クラス'
    )
    full_name = models.CharField(max_length=50, verbose_name='氏名')
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='no_answer', verbose_name='性別')

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    def is_student(self):
        return self.role == 'STUDENT'
    
    def is_teacher(self):
        return self.role == 'TEACHER'
    
    def is_admim(self):
        return self.role == 'ADMIN'


