import uuid

from django.db import models
from simple_history.models import HistoricalRecords


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(db_index=True, auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Developer metadata for integrations and interoperability needs.",
    )
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True
