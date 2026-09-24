"""Тесты регистрации, входа, выхода и служебных команд."""
import os
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class RegisterTests(TestCase):
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newbie', 'password1': 'Sl0zhnyi-parol', 'password2': 'Sl0zhnyi-parol',
        }, follow=True)
        self.assertTrue(User.objects.filter(username='newbie').exists())
        self.assertEqual(response.context['user'].username, 'newbie')
        self.assertContains(response, 'newbie')

    def test_register_shows_errors(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newbie', 'password1': '123', 'password2': '456',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newbie').exists())
        self.assertTrue(response.context['form'].errors)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('anna', password='pass-12345')

    def test_login_redirects_to_next(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'anna', 'password': 'pass-12345', 'next': '/topics/',
        })
        self.assertRedirects(response, '/topics/')

    def test_login_ignores_external_next(self):
        response = self.client.post(reverse('users:login'), {
            'username': 'anna', 'password': 'pass-12345', 'next': 'https://evil.example/',
        })
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil', response['Location'])

    def test_logout_get_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_post_ends_session(self):
        self.client.force_login(self.user)
        self.client.post(reverse('users:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_csrf(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse('users:logout'))
        self.assertEqual(response.status_code, 403)


class CommandTests(TestCase):
    def test_ensure_admin_from_env(self):
        env = {'DJANGO_SUPERUSER_USERNAME': 'boss', 'DJANGO_SUPERUSER_PASSWORD': 'Adm1n-pass!'}
        with mock.patch.dict(os.environ, env):
            call_command('ensure_admin', stdout=StringIO())
            call_command('ensure_admin', stdout=StringIO())
        boss = User.objects.get(username='boss')
        self.assertTrue(boss.is_superuser)
        self.assertTrue(boss.check_password('Adm1n-pass!'))

    def test_ensure_admin_without_env_does_nothing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            call_command('ensure_admin', stdout=StringIO())
        self.assertFalse(User.objects.exists())

    def test_seed_demo_is_idempotent(self):
        with mock.patch.dict(os.environ, {'DEMO_PASSWORD': 'Demo-pass-1'}):
            call_command('seed_demo', stdout=StringIO())
            call_command('seed_demo', stdout=StringIO())
        anna = User.objects.get(username='anna')
        self.assertTrue(anna.check_password('Demo-pass-1'))
        self.assertEqual(User.objects.filter(username__in=['anna', 'boris']).count(), 2)
        self.assertTrue(self.client.login(username='boris', password='Demo-pass-1'))
