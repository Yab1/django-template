"""
Generated concrete model for Author

This model is generated from the abstract Author model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Author as AbstractAuthor


class Author(AbstractAuthor):
    author_reference = models.ForeignKey(
        "fhir.Reference",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="author_author_reference",
        help_text=_("Reference to Practitioner | PractitionerRole | Patient | RelatedPerson | Organization"),
    )

    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        app_label = "fhir"
