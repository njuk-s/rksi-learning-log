"""Тесты Learning Log: доступ, владельцы, формы, удаление, миграция владельца."""
from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from .models import Entry, Topic


class BaseCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.anna = User.objects.create_user('anna', password='pass-12345')
        cls.boris = User.objects.create_user('boris', password='pass-12345')
        cls.topic = Topic.objects.create(owner=cls.anna, text='Django')
        cls.entry = Entry.objects.create(topic=cls.topic, text='Первая запись')
        cls.public = Topic.objects.create(owner=cls.anna, text='Открытая', public=True)

    def login(self, user):
        self.client.force_login(user)


class PublicPagesTests(BaseCase):
    def test_index_opens_for_anonymous(self):
        response = self.client.get(reverse('learning_logs:index'))
        self.assertContains(response, 'Регистрация')

    def test_index_shows_stats_for_user(self):
        self.login(self.anna)
        response = self.client.get(reverse('learning_logs:index'))
        self.assertContains(response, 'Привет, anna')
        self.assertEqual(response.context['topic_count'], 2)

    def test_healthz(self):
        self.assertEqual(self.client.get('/healthz/').content, b'ok')

    def test_unknown_url_is_404(self):
        self.assertEqual(self.client.get('/no-such-page/').status_code, 404)


class LoginRequiredTests(BaseCase):
    def test_private_pages_redirect_to_login(self):
        urls = [
            reverse('learning_logs:topics'),
            reverse('learning_logs:new_topic'),
            reverse('learning_logs:new_entry', args=[self.topic.id]),
            reverse('learning_logs:edit_entry', args=[self.entry.id]),
            reverse('learning_logs:edit_topic', args=[self.topic.id]),
            reverse('learning_logs:delete_topic', args=[self.topic.id]),
        ]
        login_url = reverse('users:login')
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f'{login_url}?next={url}')

    def test_anonymous_cannot_read_private_topic(self):
        response = self.client.get(reverse('learning_logs:topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 404)


class OwnershipTests(BaseCase):
    def test_topics_list_shows_only_own(self):
        Topic.objects.create(owner=self.boris, text='Шахматы')
        self.login(self.anna)
        response = self.client.get(reverse('learning_logs:topics'))
        self.assertContains(response, 'Django')
        self.assertNotContains(response, 'Шахматы')

    def test_foreign_private_topic_is_404(self):
        self.login(self.boris)
        response = self.client.get(reverse('learning_logs:topic', args=[self.topic.id]))
        self.assertEqual(response.status_code, 404)

    def test_foreign_objects_cannot_be_changed(self):
        self.login(self.boris)
        cases = [
            ('learning_logs:edit_entry', self.entry.id, {'text': 'взлом'}),
            ('learning_logs:new_entry', self.topic.id, {'text': 'взлом'}),
            ('learning_logs:edit_topic', self.topic.id, {'text': 'взлом'}),
            ('learning_logs:delete_topic', self.topic.id, {}),
            ('learning_logs:delete_entry', self.entry.id, {}),
        ]
        for name, pk, data in cases:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=[pk])).status_code, 404)
                self.assertEqual(self.client.post(reverse(name, args=[pk]), data).status_code, 404)
        self.entry.refresh_from_db()
        self.topic.refresh_from_db()
        self.assertEqual(self.entry.text, 'Первая запись')
        self.assertEqual(self.topic.text, 'Django')
        self.assertEqual(self.topic.entries.count(), 1)

    def test_public_topic_is_read_only_for_others(self):
        Entry.objects.create(topic=self.public, text='Общая запись')
        response = self.client.get(reverse('learning_logs:topic', args=[self.public.id]))
        self.assertContains(response, 'Общая запись')
        self.assertNotContains(response, reverse('learning_logs:new_entry', args=[self.public.id]))
        self.login(self.boris)
        response = self.client.post(reverse('learning_logs:new_entry', args=[self.public.id]), {'text': 'x'})
        self.assertEqual(response.status_code, 404)

    def test_public_topics_page(self):
        response = self.client.get(reverse('learning_logs:public_topics'))
        self.assertContains(response, 'Открытая')
        self.assertNotContains(response, '>Django<')

    def test_missing_ids_are_404(self):
        self.login(self.anna)
        for name in ('learning_logs:topic', 'learning_logs:edit_topic', 'learning_logs:new_entry'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=[99999])).status_code, 404)
        self.assertEqual(self.client.get(reverse('learning_logs:edit_entry', args=[99999])).status_code, 404)


class FormTests(BaseCase):
    def test_new_topic_gets_current_owner(self):
        self.login(self.boris)
        response = self.client.post(reverse('learning_logs:new_topic'),
                                    {'text': 'Шахматы', 'owner': self.anna.id})
        topic = Topic.objects.get(text='Шахматы')
        self.assertEqual(topic.owner, self.boris)
        self.assertRedirects(response, reverse('learning_logs:topic', args=[topic.id]))

    def test_empty_topic_shows_form_error(self):
        self.login(self.anna)
        response = self.client.post(reverse('learning_logs:new_topic'), {'text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)

    def test_add_and_edit_entry(self):
        self.login(self.anna)
        self.client.post(reverse('learning_logs:new_entry', args=[self.topic.id]), {'text': 'Вторая'})
        self.assertEqual(self.topic.entries.count(), 2)
        self.client.post(reverse('learning_logs:edit_entry', args=[self.entry.id]), {'text': 'Исправлено'})
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.text, 'Исправлено')

    def test_search(self):
        self.login(self.anna)
        response = self.client.get(reverse('learning_logs:topics'), {'q': 'первая'})
        self.assertEqual(list(response.context['topics']), [self.topic])


class DeleteTests(BaseCase):
    def test_get_shows_confirmation_and_keeps_data(self):
        self.login(self.anna)
        response = self.client.get(reverse('learning_logs:delete_topic', args=[self.topic.id]))
        self.assertContains(response, 'Да, удалить')
        self.assertTrue(Topic.objects.filter(id=self.topic.id).exists())

    def test_post_deletes_topic_with_entries(self):
        self.login(self.anna)
        self.client.post(reverse('learning_logs:delete_topic', args=[self.topic.id]))
        self.assertFalse(Topic.objects.filter(id=self.topic.id).exists())
        self.assertFalse(Entry.objects.filter(id=self.entry.id).exists())

    def test_post_deletes_entry(self):
        self.login(self.anna)
        self.client.post(reverse('learning_logs:delete_entry', args=[self.entry.id]))
        self.assertFalse(Entry.objects.filter(id=self.entry.id).exists())


class OwnerMigrationTests(TransactionTestCase):
    """Темы, созданные до появления владельца, получают существующего пользователя."""

    before = [('learning_logs', '0001_initial')]
    after = [('learning_logs', '0002_topic_owner')]
    auth = [('auth', '0012_alter_user_first_name_max_length')]

    def test_existing_topics_get_owner(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.before)
        old_apps = executor.loader.project_state(self.before + self.auth).apps
        OldTopic = old_apps.get_model('learning_logs', 'Topic')
        OldUser = old_apps.get_model('auth', 'User')
        admin = OldUser.objects.create(username='admin', is_superuser=True, is_staff=True)
        OldTopic.objects.create(text='Старая тема')

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.after)
        new_apps = executor.loader.project_state(self.after).apps
        NewTopic = new_apps.get_model('learning_logs', 'Topic')
        self.assertEqual(NewTopic.objects.get(text='Старая тема').owner_id, admin.id)

        # Вернуть схему в актуальное состояние для остальных тестов.
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
