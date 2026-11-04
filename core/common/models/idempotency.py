from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.models.base import BaseModel


class IdempotencyRecord(BaseModel):
    """Completed replay row. Inserted in the same transaction as the business rows."""

    class State(models.TextChoices):
        COMPLETED = "completed", _("Completed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="idempotency_records",
    )
    operation = models.CharField(max_length=64)
    key = models.CharField(max_length=128)
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField()
    response_body = models.JSONField()
    resource_id = models.UUIDField(null=True, blank=True)
    state = models.CharField(max_length=16, choices=State.choices, default=State.COMPLETED)

    class Meta:
        verbose_name = _("Idempotency record")
        verbose_name_plural = _("Idempotency records")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "operation", "key"],
                name="common_idempotency_user_operation_key",
            ),
            models.CheckConstraint(
                condition=models.Q(state="completed"),
                name="common_idempotency_state_completed",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.operation}:{self.key}"
