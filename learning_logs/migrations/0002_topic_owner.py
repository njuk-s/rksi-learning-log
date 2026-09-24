"""
Добавляет владельца темы.

Как в учебнике, существующие темы получают существующего пользователя, но
без постоянного default=1 в модели: поле сначала добавляется как
необязательное, затем данные переносятся, и только потом поле становится
обязательным. Так миграция работает и на пустой базе, и на базе с данными.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def assign_existing_owner(apps, schema_editor):
    Topic = apps.get_model('learning_logs', 'Topic')
    orphans = Topic.objects.filter(owner__isnull=True)
    if not orphans.exists():
        return
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    owner = (User.objects.filter(is_superuser=True).order_by('id').first()
             or User.objects.order_by('id').first())
    if owner is None:
        # Пользователей ещё нет: создаём неактивную учётную запись без пароля.
        owner = User.objects.create(username='legacy_owner', is_active=False, password='!')
    orphans.update(owner=owner)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(assign_existing_owner, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='topic',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                    to=settings.AUTH_USER_MODEL),
        ),
    ]
