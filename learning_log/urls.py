"""Корневые маршруты проекта Learning Log."""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def healthz(request):
    """Проверка живости для Docker и хостинга. Не обращается к базе данных."""
    return HttpResponse('ok', content_type='text/plain')


admin.site.site_header = 'Learning Log - администрирование'
admin.site.site_title = 'Learning Log'
admin.site.index_title = 'Управление данными'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('healthz/', healthz, name='healthz'),
    path('', include('learning_logs.urls')),
]
