from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.mixins import SoftDeleteMixin, VisibleMixin
from core.common.models import BaseModel
from core.notifications.constants import Category, Channel


class NotificationPreference(VisibleMixin, SoftDeleteMixin, BaseModel):
    """Stored opt-in/out for one (user, channel, category)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    channel = models.CharField(max_length=32, choices=Channel.choices)
    category = models.CharField(max_length=32, choices=Category.choices)
    enabled = models.BooleanField(default=True)
    destination = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "notifications_preference"
        verbose_name = _("Notification preference")
        verbose_name_plural = _("Notification preferences")
        ordering = ["user", "channel", "category"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "channel", "category"],
                condition=models.Q(deleted_at__isnull=True),
                name="notifications_preference_active_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.channel}/{self.category}"
