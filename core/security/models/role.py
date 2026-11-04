from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.mixins import ReferenceIdMixin, SoftDeleteMixin, VisibleMixin
from core.common.models import BaseModel


class Role(ReferenceIdMixin, VisibleMixin, SoftDeleteMixin, BaseModel):
    """Named bag of permissions. Identifier is ``code``. Never authorize on this name."""

    reference_id_prefix = "ROL"

    code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Stable role identifier, e.g. claims_adjuster."),
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    permissions = models.ManyToManyField(
        "security.Permission",
        through="security.RolePermission",
        related_name="roles",
        blank=True,
    )

    class Meta:
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code
