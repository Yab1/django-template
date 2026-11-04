from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.models import BaseModel
from core.notifications.constants import DeliveryStatus


class NotificationAttempt(BaseModel):
    """One send try against a delivery row."""

    delivery = models.ForeignKey(
        "notifications.NotificationDelivery",
        on_delete=models.CASCADE,
        related_name="attempt_log",
    )
    attempt = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=16, choices=DeliveryStatus.choices)
    error = models.TextField(blank=True, default="")

    class Meta:
        db_table = "notifications_attempt"
        verbose_name = _("Notification attempt")
        verbose_name_plural = _("Notification attempts")
        ordering = ["delivery", "attempt"]

    def __str__(self) -> str:
        return f"{self.delivery_id}#{self.attempt} {self.status}"
