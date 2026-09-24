"""Представления Learning Log.

Любая тема или запись для изменения достаётся вместе с проверкой владельца,
поэтому чужой или несуществующий ID всегда даёт 404.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Max, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import EntryForm, TopicForm
from .models import Entry, Topic

ENTRIES_PER_PAGE = 10


def owned_topic(request, topic_id):
    """Тема текущего пользователя или 404."""
    return get_object_or_404(Topic, id=topic_id, owner=request.user)


def owned_entry(request, entry_id):
    """Запись из темы текущего пользователя или 404."""
    return get_object_or_404(Entry.objects.select_related('topic'), id=entry_id,
                             topic__owner=request.user)


def with_stats(queryset):
    return queryset.annotate(entry_count=Count('entries'), last_entry=Max('entries__date_added'))


def index(request):
    """Домашняя страница приложения Learning Log."""
    context = {}
    if request.user.is_authenticated:
        topics = Topic.objects.filter(owner=request.user)
        context = {
            'recent_topics': with_stats(topics).order_by('-date_added')[:3],
            'topic_count': topics.count(),
            'entry_count': Entry.objects.filter(topic__owner=request.user).count(),
            'public_count': topics.filter(public=True).count(),
        }
    return render(request, 'learning_logs/index.html', context)


@login_required
def topics(request):
    """Выводит список тем текущего пользователя, с поиском."""
    query = request.GET.get('q', '').strip()
    topics = with_stats(Topic.objects.filter(owner=request.user)).order_by('date_added')
    if query:
        matching = Topic.objects.filter(
            Q(text__icontains=query) | Q(entries__text__icontains=query), owner=request.user,
        ).values('id')
        topics = topics.filter(id__in=matching)
    return render(request, 'learning_logs/topics.html', {'topics': topics, 'query': query})


def public_topics(request):
    """Открытые темы всех пользователей: читать может любой посетитель."""
    topics = with_stats(Topic.objects.filter(public=True).select_related('owner')).order_by('-date_added')
    return render(request, 'learning_logs/public_topics.html', {'topics': topics})


def topic(request, topic_id):
    """Выводит одну тему и все её записи.

    Владелец видит тему всегда, остальные - только открытую.
    """
    topic = get_object_or_404(Topic.objects.select_related('owner'), id=topic_id)
    is_owner = request.user.is_authenticated and topic.owner_id == request.user.id
    if not is_owner and not topic.public:
        raise Http404

    page = Paginator(topic.entries.all(), ENTRIES_PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'learning_logs/topic.html', {
        'topic': topic, 'entries': page, 'page_obj': page, 'is_owner': is_owner,
    })


@login_required
def new_topic(request):
    """Определяет новую тему."""
    if request.method != 'POST':
        # Данные не отправлялись; создаётся пустая форма.
        form = TopicForm()
    else:
        # Отправлены данные POST; обработать данные.
        form = TopicForm(data=request.POST)
        if form.is_valid():
            new_topic = form.save(commit=False)
            new_topic.owner = request.user
            new_topic.save()
            messages.success(request, f'Тема «{new_topic}» создана.')
            return redirect('learning_logs:topic', topic_id=new_topic.id)

    return render(request, 'learning_logs/new_topic.html', {'form': form})


@login_required
def edit_topic(request, topic_id):
    """Переименовывает тему или меняет её видимость."""
    topic = owned_topic(request, topic_id)
    if request.method != 'POST':
        form = TopicForm(instance=topic)
    else:
        form = TopicForm(instance=topic, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Тема сохранена.')
            return redirect('learning_logs:topic', topic_id=topic.id)

    return render(request, 'learning_logs/edit_topic.html', {'topic': topic, 'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_topic(request, topic_id):
    """GET показывает подтверждение, удаляет только POST."""
    topic = owned_topic(request, topic_id)
    if request.method == 'POST':
        topic.delete()
        messages.success(request, f'Тема «{topic}» удалена вместе с записями.')
        return redirect('learning_logs:topics')
    return render(request, 'learning_logs/confirm_delete.html', {
        'object': topic,
        'kind': 'тему',
        'details': f'Вместе с ней удалятся все записи ({topic.entries.count()}).',
        'cancel_url': topic.get_absolute_url(),
    })


@login_required
def new_entry(request, topic_id):
    """Добавляет новую запись по конкретной теме."""
    topic = owned_topic(request, topic_id)

    if request.method != 'POST':
        form = EntryForm()
    else:
        form = EntryForm(data=request.POST)
        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.topic = topic
            new_entry.save()
            messages.success(request, 'Запись добавлена.')
            return redirect('learning_logs:topic', topic_id=topic.id)

    return render(request, 'learning_logs/new_entry.html', {'topic': topic, 'form': form})


@login_required
def edit_entry(request, entry_id):
    """Редактирует существующую запись."""
    entry = owned_entry(request, entry_id)
    topic = entry.topic

    if request.method != 'POST':
        # Исходный запрос; форма заполняется данными текущей записи.
        form = EntryForm(instance=entry)
    else:
        # Отправка данных POST; обработать данные.
        form = EntryForm(instance=entry, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись сохранена.')
            return redirect('learning_logs:topic', topic_id=topic.id)

    return render(request, 'learning_logs/edit_entry.html', {'entry': entry, 'topic': topic, 'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def delete_entry(request, entry_id):
    """GET показывает подтверждение, удаляет только POST."""
    entry = owned_entry(request, entry_id)
    topic = entry.topic
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Запись удалена.')
        return redirect('learning_logs:topic', topic_id=topic.id)
    return render(request, 'learning_logs/confirm_delete.html', {
        'object': entry,
        'kind': 'запись',
        'details': f'Из темы «{topic}».',
        'cancel_url': topic.get_absolute_url(),
    })
