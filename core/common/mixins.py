"""
Abstract model mixins. Opt in per model via multiple inheritance.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.common.utils.reference_id import generate_reference_id


class ReferenceIdMixin(models.Model):
    """
    Human-readable reference ID (e.g. DT-NTF-A3X9K2).

    Set ``reference_id_prefix`` on the concrete model (exactly 3 chars).
    Generated when missing (``clean`` / ``save``).
    """

    reference_id = models.CharField(
        max_length=32,
        unique=True,
        blank=True,
        db_index=True,
        help_text=_("Human-readable reference ID for display and lookups."),
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self._ensure_reference_id()
        return super().save(*args, **kwargs)

    def clean(self) -> None:
        self._ensure_reference_id()
        super().clean()

    def _ensure_reference_id(self) -> None:
        if self.reference_id:
            return
        self.reference_id = generate_reference_id(model=type(self))


class VisibleMixin(models.Model):
    """List/admin visibility flag."""

    is_visible = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this record is visible in list APIs and admin."),
    )

    class Meta:
        abstract = True

    def activate(self) -> None:
        self.is_visible = True
        self.save(update_fields=["is_visible"])

    def deactivate(self) -> None:
        self.is_visible = False
        self.save(update_fields=["is_visible"])


class SoftDeleteMixin(models.Model):
    """Soft delete: ``delete()`` stamps ``deleted_at`` instead of removing the row."""

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_("When set, the record is treated as deleted (soft delete)."),
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
        help_text=_("User who performed the soft delete, if any."),
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, user=None):
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self) -> None:
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
