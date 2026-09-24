"""Маршруты приложения users: вход, выход, регистрация, смена пароля."""
from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.SiteLoginView.as_view(), name='login'),
    # LogoutView в Django 5 принимает только POST: GET-запрос получает 405.
    path('logout/', views.SiteLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('password/', auth_views.PasswordChangeView.as_view(
        success_url=reverse_lazy('users:password_done'),
    ), name='password_change'),
    path('password/done/', views.password_done, name='password_done'),
]
