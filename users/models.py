from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для модели пользователя с поддержкой email и username"""

    def create_user(self, email=None, username=None, password=None, **extra_fields):
        """
        Создает и сохраняет пользователя с email или username и паролем
        """
        if not email and not username:
            raise ValueError(_('Должен быть указан либо email, либо username'))

        if email:
            email = self.normalize_email(email)

        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, username=None, password=None, **extra_fields):
        """
        Создает и сохраняет суперпользователя
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not email and not username:
            raise ValueError(_('Для суперпользователя должен быть указан либо email, либо username'))

        return self.create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя с авторизацией по email ИЛИ username
    """
    # можно использовать username
    email = models.EmailField(
        _("Email"),
        unique=True,
        blank=True,
        null=True,
        help_text=_("Необязательное поле. Можно использовать для входа")
    )

    # можно использовать email
    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Необязательное поле. Можно использовать для входа")
    )

    phone = models.CharField(
        max_length=35,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Введите номер телефона"
    )

    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
        help_text="Загрузите свой аватар"
    )

    token = models.CharField(
        max_length=100,
        verbose_name="Token",
        blank=True,
        null=True
    )

    # кастомный менеджер
    objects = CustomUserManager()

    # USERNAME_FIELD динамический
    REQUIRED_FIELDS = []  # Для createsuperuser команды

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        permissions = [
            ("can_manage_bookings", "Can manage all bookings"),
            ("can_view_all_bookings", "Can view all bookings"),
        ]

    def __str__(self):
        return self.email if self.email else self.username

    def clean(self):
        """Валидация модели"""
        from django.core.exceptions import ValidationError
        if not self.email and not self.username:
            raise ValidationError(_('Должен быть указан либо email, либо username'))

    def save(self, *args, **kwargs):
        """Переопределяем save для валидации"""
        self.clean()
        super().save(*args, **kwargs)