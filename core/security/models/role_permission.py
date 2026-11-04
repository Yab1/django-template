from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.models import BaseModel


class RolePermission(BaseModel):
    """Through table: a role holds a permission."""

    role = models.ForeignKey(
        "security.Role",
        on_delete=models.CASCADE,
        related_name="permission_links",
    )
    permission = models.ForeignKey(
        "security.Permission",
        on_delete=models.CASCADE,
        related_name="role_links",
    )

    class Meta:
        verbose_name = _("Role permission")
        verbose_name_plural = _("Role permissions")
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="security_rolepermission_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.role_id}:{self.permission_id}"
