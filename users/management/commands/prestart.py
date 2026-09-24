"""
Подготовка при запуске контейнера за один запуск Django.

Миграции, администратор из окружения и (при SEED_DEMO=True) демо-данные.
Раньше это были три отдельные команды manage.py; на слабом процессоре
бесплатного хостинга каждая загрузка Django стоит несколько секунд,
поэтому одна команда заметно ускоряет пробуждение сайта.
"""
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'migrate + ensure_admin + seed_demo (если SEED_DEMO=True) одной командой.'

    def handle(self, *args, **options):
        call_command('migrate', interactive=False, verbosity=1)
        call_command('ensure_admin')
        if os.getenv('SEED_DEMO', 'False').strip().lower() == 'true':
            call_command('seed_demo')
