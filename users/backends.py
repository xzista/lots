from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Кастомный бэкенд для аутентификации по email ИЛИ username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        try:
            # Ищем пользователя по email или username
            user = UserModel.objects.get(
                Q(email=username) | Q(username=username)
            )
        except UserModel.DoesNotExist:
            # Возвращаем None если пользователь не найден
            return None
        except UserModel.MultipleObjectsReturned:
            # На случай если email и username совпадают (маловероятно)
            user = UserModel.objects.filter(
                Q(email=username) | Q(username=username)
            ).first()

        if user and user.check_password(password):
            return user

        return None