from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

CustomUser = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **options):
        if not CustomUser.objects.filter(username='kanri').exists():
            CustomUser.objects.create_superuser(
                username='kanri',
                email='',
                password='admin7216',
                role='ADMIN',
            )