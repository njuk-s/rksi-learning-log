"""Представления приложения users."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import RegisterForm


class SiteLoginView(auth_views.LoginView):
    """Вход. Уже вошедший пользователь сразу уходит на рабочую страницу."""
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'С возвращением, {self.request.user.username}!')
        return response


class SiteLogoutView(auth_views.LogoutView):
    """Выход только методом POST с CSRF-токеном."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, 'Вы вышли из аккаунта.')
        return response


def register(request):
    """Регистрирует нового пользователя и сразу выполняет вход."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    if request.method != 'POST':
        form = RegisterForm()
    else:
        form = RegisterForm(data=request.POST)
        if form.is_valid():
            new_user = form.save()
            login(request, new_user)
            messages.success(request, f'Аккаунт создан. Добро пожаловать, {new_user.username}!')
            return redirect(settings.LOGIN_REDIRECT_URL)

    return render(request, 'users/register.html', {'form': form})


@login_required
def password_done(request):
    messages.success(request, 'Пароль изменён.')
    return redirect(settings.LOGIN_REDIRECT_URL)
