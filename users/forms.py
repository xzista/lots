from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomAuthenticationForm(AuthenticationForm):
    """
    Форма аутентификации, которая принимает email ИЛИ username
    """
    username = forms.CharField(
        label=_("Email или Username"),
        widget=forms.TextInput(attrs={'autofocus': True})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')

        # Проверяем, email это или username
        if '@' in username:
            # Если это email, ищем пользователя по email
            try:
                user = User.objects.get(email=username)
                return user.email if user.email else user.username
            except User.DoesNotExist:
                # Если пользователь не найден по email, пробуем как username
                pass

        # Возвращаем как есть (будет использоваться как username)
        return username


class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя
    """
    email = forms.EmailField(
        required=False,
        help_text=_("Необязательно. Можно указать позже")
    )

    username = forms.CharField(
        required=False,
        help_text=_("Необязательно. Можно указать позже")
    )

    class Meta:
        model = User
        fields = ("email", "username", "phone", "avatar")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")

        if not email and not username:
            raise ValidationError(
                _("Должен быть указан либо email, либо username")
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user