"""Модели Learning Log: тема и записи в ней."""
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class Topic(models.Model):
    """Тема, которую изучает пользователь."""
    text = models.CharField('тема', max_length=200)
    date_added = models.DateTimeField('создана', auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics',
                              verbose_name='владелец')
    public = models.BooleanField(
        'открытая тема', default=False,
        help_text='Открытую тему могут читать все посетители, но изменять - только вы.',
    )

    class Meta:
        ordering = ['date_added']
        verbose_name = 'тема'
        verbose_name_plural = 'темы'

    def __str__(self):
        """Возвращает строковое представление модели."""
        return self.text

    def get_absolute_url(self):
        return reverse('learning_logs:topic', args=[self.id])


class Entry(models.Model):
    """Информация, изученная пользователем по теме."""
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='entries',
                              verbose_name='тема')
    text = models.TextField('запись')
    date_added = models.DateTimeField('добавлена', auto_now_add=True)
    date_modified = models.DateTimeField('изменена', auto_now=True)

    class Meta:
        ordering = ['-date_added']
        verbose_name = 'запись'
        verbose_name_plural = 'entries'

    def __str__(self):
        """Возвращает первые 50 символов записи."""
        if len(self.text) > 50:
            return f'{self.text[:50]}...'
        return self.text

    @property
    def was_edited(self):
        return (self.date_modified - self.date_added).total_seconds() > 60
