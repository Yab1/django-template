from pathlib import Path

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.common.mixins import ReferenceIdMixin, SoftDeleteMixin, VisibleMixin
from core.common.models import BaseModel


def storage_key(*, resource: str, object_id, field: str, file_id, filename: str, when=None) -> str:
    ext = Path(filename).suffix.lower()[:9]
    moment = when or timezone.now()
    return f"{resource}/{object_id}/{field}/{moment:%Y/%m}/{file_id}{ext}"


def file_upload_to(instance: "FileObject", filename: str) -> str:
    return storage_key(
        resource=instance.resource,
        object_id=instance.object_id,
        field=instance.field,
        file_id=instance.id,
        filename=filename,
    )


class FileObject(ReferenceIdMixin, VisibleMixin, SoftDeleteMixin, BaseModel):
    """Stored blob attached to another row via ContentType + object_id."""

    reference_id_prefix = "FIL"

    file = models.FileField(upload_to=file_upload_to, max_length=512)
    filename = models.CharField(max_length=255)
    media_type = models.CharField(max_length=128)
    size = models.PositiveBigIntegerField()
    content_hash = models.CharField(max_length=64, blank=True, default="")
    driver = models.CharField(max_length=32)
    resource = models.CharField(max_length=64, db_index=True)
    field = models.CharField(max_length=64, db_index=True)
    content_type = models.ForeignKey("contenttypes.ContentType", on_delete=models.CASCADE)
    object_id = models.UUIDField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files_uploaded",
    )

    class Meta:
        db_table = "files_object"
        verbose_name = _("File")
        verbose_name_plural = _("Files")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id", "field"]),
            models.Index(fields=["resource", "object_id"]),
        ]

    def __str__(self) -> str:
        return self.reference_id or str(self.id)
