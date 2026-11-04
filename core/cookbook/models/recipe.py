from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.mixins import AuthorshipMixin, ReferenceIdMixin, SoftDeleteMixin, VisibleMixin
from core.common.models import BaseModel


class Recipe(ReferenceIdMixin, VisibleMixin, SoftDeleteMixin, AuthorshipMixin, BaseModel):
    """
    Specimen model for house style. Not a product entity.

    Copy this layout into a real app, then rename the nouns.
    Attach files via ``POST /files/upload/`` with resource=recipe, field=file, object_id=this id.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    reference_id_prefix = "RCP"

    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Recipe")
        verbose_name_plural = _("Recipes")
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                # Literal values: Meta cannot see sibling Status. Keep in sync with Status.
                condition=models.Q(status__in=["draft", "published"]),
                name="cookbook_recipe_status_valid",
            ),
        ]

    def __str__(self) -> str:
        return self.title
