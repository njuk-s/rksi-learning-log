from django.contrib import admin
from django.db.models import Count

from .models import Entry, Topic


class EntryInline(admin.StackedInline):
    model = Entry
    extra = 0
    fields = ('text', 'date_added')
    readonly_fields = ('date_added',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('text', 'owner', 'public', 'entry_count', 'date_added')
    list_filter = ('public', 'date_added', 'owner')
    search_fields = ('text', 'owner__username')
    list_select_related = ('owner',)
    date_hierarchy = 'date_added'
    inlines = [EntryInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_entries=Count('entries'))

    @admin.display(description='записей', ordering='_entries')
    def entry_count(self, obj):
        return obj._entries


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'topic', 'owner', 'date_added')
    list_filter = ('date_added', 'topic__owner')
    search_fields = ('text', 'topic__text')
    list_select_related = ('topic__owner',)
    date_hierarchy = 'date_added'

    @admin.display(description='владелец', ordering='topic__owner__username')
    def owner(self, obj):
        return obj.topic.owner
