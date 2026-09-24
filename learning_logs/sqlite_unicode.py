"""
Поиск без учёта регистра для русского текста в SQLite.

Встроенный LIKE в SQLite не различает регистр только у латиницы, поэтому
запрос «первая» не находит «Первая». Здесь LIKE заменяется функцией на Python,
которая сравнивает строки через casefold(). В PostgreSQL это не нужно.
"""
import re
from functools import lru_cache

from django.db.backends.signals import connection_created


@lru_cache(maxsize=256)
def _compile(pattern, escape):
    parts, i = [], 0
    while i < len(pattern):
        char = pattern[i]
        if escape and char == escape and i + 1 < len(pattern):
            parts.append(re.escape(pattern[i + 1]))
            i += 2
            continue
        parts.append('.*' if char == '%' else '.' if char == '_' else re.escape(char))
        i += 1
    return re.compile(''.join(parts), re.DOTALL | re.IGNORECASE)


def _like(pattern, value, escape=None):
    if pattern is None or value is None:
        return None
    return _compile(pattern.casefold(), escape).fullmatch(str(value).casefold()) is not None


def _register(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.connection.create_function('like', 2, _like, deterministic=True)
        connection.connection.create_function('like', 3, _like, deterministic=True)


def install():
    connection_created.connect(_register, dispatch_uid='sqlite_unicode_like')
