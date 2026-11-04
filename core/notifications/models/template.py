from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.mixins import ReferenceIdMixin, SoftDeleteMixin, VisibleMixin
from core.common.models import BaseModel
from core.notifications.constants import BodyFormat, Category, Channel


class NotificationTemplate(ReferenceIdMixin, VisibleMixin, SoftDeleteMixin, BaseModel):
    """Per-channel subject/body used when enqueueing a delivery."""

    reference_id_prefix = "NTM"

    channel = models.CharField(max_length=32, choices=Channel.choices)
    category = models.CharField(max_length=32, choices=Category.choices)
    locale = models.CharField(max_length=16, default="en")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    format = models.CharField(max_length=16, choices=BodyFormat.choices, default=BodyFormat.TEXT)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "notifications_template"
        verbose_name = _("Notification template")
        verbose_name_plural = _("Notification templates")
        ordering = ["channel", "category", "locale"]
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "category", "locale"],
                condition=models.Q(deleted_at__isnull=True),
                name="notifications_template_active_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.channel}/{self.category}/{self.locale}"
