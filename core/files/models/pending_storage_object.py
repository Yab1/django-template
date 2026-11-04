from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.models import BaseModel


class PendingStorageObject(BaseModel):
    """Committed claim for a storage key written before the FileObject row exists."""

    storage_key = models.CharField(max_length=512, unique=True)
    file_id = models.UUIDField(db_index=True)

    class Meta:
        verbose_name = _("Pending storage object")
        verbose_name_plural = _("Pending storage objects")

    def __str__(self) -> str:
        return self.storage_key
