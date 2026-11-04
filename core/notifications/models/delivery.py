from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.mixins import ReferenceIdMixin, SoftDeleteMixin, VisibleMixin
from core.common.models import BaseModel
from core.notifications.constants import (
    BodyFormat,
    Category,
    Channel,
    DeliveryStatus,
    Priority,
)


class NotificationDelivery(ReferenceIdMixin, VisibleMixin, SoftDeleteMixin, BaseModel):
    """One outbound attempt plan. Sent in-app rows are the inbox."""

    reference_id_prefix = "NTF"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_deliveries",
    )
    channel = models.CharField(max_length=32, choices=Channel.choices, db_index=True)
    category = models.CharField(max_length=32, choices=Category.choices, db_index=True)
    template = models.ForeignKey(
        "notifications.NotificationTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
    )
    destination = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    format = models.CharField(max_length=16, choices=BodyFormat.choices, default=BodyFormat.TEXT)
    status = models.CharField(
        max_length=16,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        db_index=True,
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    next_attempt_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_error = models.TextField(blank=True, default="")
    provider_ref = models.CharField(max_length=255, blank=True, default="")
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    event_code = models.CharField(max_length=128, blank=True, default="")
    resource_type = models.CharField(max_length=64, blank=True, default="")
    resource_id = models.UUIDField(null=True, blank=True)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.NORMAL)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_delivery"
        verbose_name = _("Notification delivery")
        verbose_name_plural = _("Notification deliveries")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "channel", "status", "-created_at"]),
            models.Index(fields=["status", "next_attempt_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["idempotency_key", "channel"],
                condition=models.Q(idempotency_key__isnull=False),
                name="notifications_delivery_idempotency_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.reference_id} {self.channel} {self.status}"
