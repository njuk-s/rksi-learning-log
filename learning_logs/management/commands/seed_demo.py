"""
Наполняет пустой сайт демонстрационными данными для проверки.

Создаёт двух пользователей (anna и boris) с паролем из DEMO_PASSWORD и
несколько тем с записями. Повторный запуск ничего не дублирует.
Без DEMO_PASSWORD команда ничего не делает.
"""
import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from learning_logs.models import Topic

DEMO = {
    'anna': [
        ('Django', True, [
            'Проект создаётся командой django-admin startproject, приложение - python manage.py startapp.',
            'После изменения моделей нужны две команды: makemigrations и migrate.',
            'get_object_or_404(Topic, id=topic_id, owner=request.user) сразу проверяет и владельца, '
            'и существование объекта: чужая тема даёт 404.',
        ]),
        ('Английский', False, [
            'Present Perfect: have + третья форма глагола. I have already finished.',
            'Слово на сегодня: thorough - тщательный.',
        ]),
    ],
    'boris': [
        ('Шахматы', True, [
            'Дебют: развивать фигуры, бороться за центр, рано рокироваться.',
            'Вилка конём - самый частый тактический удар в партиях новичков.',
        ]),
        ('Личные заметки', False, [
            'Эту тему видит только boris: anna не откроет её даже по прямой ссылке.',
        ]),
    ],
}


class Command(BaseCommand):
    help = 'Создать демо-пользователей anna и boris с темами и записями.'

    @transaction.atomic
    def handle(self, *args, **options):
        password = os.getenv('DEMO_PASSWORD', '')
        if not password:
            self.stdout.write('seed_demo: DEMO_PASSWORD не задан, пропускаю.')
            return

        for username, topics in DEMO.items():
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.save()
            if Topic.objects.filter(owner=user).exists():
                continue
            for text, public, entries in topics:
                topic = Topic.objects.create(owner=user, text=text, public=public)
                for entry_text in entries:
                    topic.entries.create(text=entry_text)
            self.stdout.write(f'seed_demo: данные для {username} созданы.')
