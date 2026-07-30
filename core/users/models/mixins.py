from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class VisibleMixin(models.Model):
    is_visible = models.BooleanField(
        default=True,
        db_index=True,
        help_text=_("Whether this record is visible in list APIs and admin."),
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
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


class HistoryMixin(models.Model):
    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True
