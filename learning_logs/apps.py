from django.apps import AppConfig


class LearningLogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'learning_logs'
    verbose_name = 'Учебный журнал'

    def ready(self):
        from . import sqlite_unicode
        sqlite_unicode.install()
