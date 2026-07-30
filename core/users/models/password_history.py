from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.models import BaseModel


class PasswordHistory(BaseModel):
    """Stores retired password hashes for reuse detection (see ``PasswordHistoryValidator``)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_histories",
        help_text=_("User whose previous password hash is stored."),
    )
    hashed_password = models.CharField(
        max_length=128,
        help_text=_("Encoded password hash retired when the user changed password."),
    )

    class Meta:
        db_table = "users_password_history"
        verbose_name = _("Password history")
        verbose_name_plural = _("Password histories")
        ordering = ["-created_at"]
        default_related_name = "password_histories"
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"PasswordHistory {self.id}"
