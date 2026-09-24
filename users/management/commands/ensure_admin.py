"""
Создаёт суперпользователя из переменных окружения, если его ещё нет.

Нужна для хостингов без консоли: при каждом запуске контейнера команда
проверяет DJANGO_SUPERUSER_USERNAME и DJANGO_SUPERUSER_PASSWORD.
Если переменные не заданы, команда ничего не делает.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создать или обновить администратора из DJANGO_SUPERUSER_* переменных.'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
        if not username or not password:
            self.stdout.write('ensure_admin: переменные не заданы, пропускаю.')
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': os.getenv('DJANGO_SUPERUSER_EMAIL', '')},
        )
        # Пароль из окружения считается главным: так его можно сменить без консоли.
        if created or not user.check_password(password) or not user.is_superuser:
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()
        self.stdout.write(f'ensure_admin: администратор {username} {"создан" if created else "на месте"}.')
