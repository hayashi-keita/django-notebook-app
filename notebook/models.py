from email.quoprimime import header_check
from django.db import models
from django.conf import settings

class Grade(models.Model):
    number = models.PositiveSmallIntegerField(verbose_name='学年')
    name = models.CharField(max_length=50, blank=True, verbose_name='学年名')

    def __str__(self):
        return f'{self.number}年'

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
    CONDITION_CHOICES = [(i, str(i)) for i in range(1, 11)]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_records')
    date_for = models.DateField(verbose_name='記録日')
    created_at = models.DateTimeField(auto_now_add=True)
    
    physical_level = models.PositiveSmallIntegerField(
        choices=CONDITION_CHOICES,
        default=5,
        help_text='体調を10段階で評価してください（1:最低, 10:最高）。',
        verbose_name='体調（10段階評価）',
    )
    physical_condition = models.CharField(
        max_length=100,
        blank=True,
        help_text='体調に関して具体的に気づいたこと（例：昨晩はあまり眠れなかった、頭痛があるなど）を記入してください。',
        verbose_name='体調補足メモ',
    )
    mental_level = models.PositiveSmallIntegerField(
        choices=CONDITION_CHOICES,
        default=5,
        help_text='メンタル状態を10段階で評価してください（1:最低, 10:最高）。',
        verbose_name='メンタル（10段階評価）',
    )
    mental_condition = models.CharField(
        max_length=100,
        blank=True,
        help_text='メンタルに関して具体的に気づいたこと（例：授業中に集中できた、友人関係で悩んでいるなど）を記入してください。',
        verbose_name='メンタル補足メモ',
    )
    
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
    
class Memo(models.Model):
    STAMP_CHOICES = (
        ('NONE', 'スタンプなし'),
        ('LIKE', 'イイネ！'),
        ('GOOD', 'がんばったね！'),
        ('TRY', '次回に期待'),
        ('CHECK', '確認済'),
    )

    record = models.OneToOneField(DailyRecord, on_delete=models.CASCADE, related_name='memos')
    # 担任のみ選択可能
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'TEACHER'})
    text = models.TextField(blank=True, null=True, verbose_name='メモ内容')
    stamp = models.CharField(max_length=20, choices=STAMP_CHOICES, default='NONE', verbose_name='スタンプ')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '指導メモ'
        verbose_name_plural = '指導メモ'
        unique_together = ('record', 'teacher')
    
    def __str__(self):
        return f'Memo for {self.record} by {self.teacher}'

class TeacherLog(models.Model):
    # どの生徒に関するログか
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='logs',
        # 生徒のみ選択
        limit_choices_to={'role': 'STUDENT'},
        verbose_name='対象生徒',
    )
    # ログの作成者は誰か
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_logs',
        limit_choices_to={'role__in': ['TEACHER', 'ADMIN']},
        verbose_name='作成者',
    )
    # ログ内容
    text = models.TextField(verbose_name='ログ内容')
    # 教師間での重要度を示すフラグ
    is_important = models.BooleanField(default=False, verbose_name='重要フラグ（会議議題など）')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    class Meta:
        verbose_name = '教師間共有ログ'
        verbose_name_plural = '教師間共有ログ'
        ordering = ['-created_at']
    
    def __str__(self):
        created_date_str = self.created_at.strftime('%Y/%m/%d %H:%M')
        return f"{self.student.full_name}に関する by {self.teacher.full_name} ({created_date_str})"
    
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='受信者',
    )
    related_record = models.ForeignKey(
        DailyRecord,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='notifications'
    )
    message = models.CharField(max_length=255, verbose_name='メッセージ')
    is_read = models.BooleanField(default=False, verbose_name='既読')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')

    def __str__(self):
        return f'{self.user} - {self.message}'