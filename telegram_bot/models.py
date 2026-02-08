from django.db import models
from lots.models import Lot


class TelegramDialog(models.Model):
    tg_user_id = models.BigIntegerField(unique=True)
    topic_id = models.BigIntegerField(null=True, blank=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)

    current_lot = models.ForeignKey(
        Lot, on_delete=models.SET_NULL, null=True, blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=(
            ("open", "Открыт"),
            ("closed", "Закрыт"),
        ),
        default="open"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name or ''} @{self.username or ''} ({self.tg_user_id})"


class TelegramMessage(models.Model):
    dialog = models.ForeignKey(
        TelegramDialog, on_delete=models.CASCADE, related_name="messages"
    )
    text = models.TextField()
    is_from_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = "USER" if self.is_from_user else "ADMIN"
        return f"{who}: {self.text[:40]}"