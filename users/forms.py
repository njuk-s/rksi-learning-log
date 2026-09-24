from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
    """Стандартная форма регистрации Django с понятными подсказками."""

    class Meta(UserCreationForm.Meta):
        fields = ('username',)
        help_texts = {
            'username': 'Буквы, цифры и символы @/./+/-/_, не длиннее 150 знаков.',
        }
