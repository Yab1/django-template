from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.models import BaseModel


class UserRole(BaseModel):
    """A user holds a role. Effective perms are the union across assignments."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="security_role_links",
    )
    role = models.ForeignKey(
        "security.Role",
        on_delete=models.CASCADE,
        related_name="user_links",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_roles_assigned",
    )

    class Meta:
        verbose_name = _("User role")
        verbose_name_plural = _("User roles")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role"],
                name="security_userrole_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.role_id}"
