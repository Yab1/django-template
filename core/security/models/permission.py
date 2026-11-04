from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.mixins import ReferenceIdMixin
from core.common.models import BaseModel


class Permission(ReferenceIdMixin, BaseModel):
    """
    Product capability. Not a Django ContentType perm.

    Codes are registered in app ``ready()`` and synced into this table.
    Roles hold permissions; views check ``code``, never a role name.
    """

    reference_id_prefix = "PRM"

    code = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text=_("Stable capability code, e.g. cookbook:recipe:publish."),
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("Permission")
        verbose_name_plural = _("Permissions")
        ordering = ["code"]

    def __str__(self) -> str:
        return self.code
