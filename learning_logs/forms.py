from django import forms

from .models import Entry, Topic


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['text', 'public']
        labels = {'text': 'Название темы'}
        widgets = {'text': forms.TextInput(attrs={'placeholder': 'Например: Django, шахматы, английский'})}


class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['text']
        labels = {'text': 'Что вы узнали?'}
        widgets = {'text': forms.Textarea(attrs={'cols': 80, 'rows': 10})}
