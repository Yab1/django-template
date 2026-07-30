"""
Generated concrete model for CodeableReference

This model is generated from the abstract CodeableReference model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import CodeableReference as AbstractCodeableReference


class CodeableReference(AbstractCodeableReference):
    concept = models.ForeignKey(
        "fhir.CodeableConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="codeable_reference_concept",
        help_text=_("Reference to a concept (by class)"),
    )

    reference = models.ForeignKey(
        "fhir.Reference",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="codeable_reference_reference",
        help_text=_("Reference to a resource (by instance)"),
    )

    class Meta:
        verbose_name = "Codeable Reference"
        verbose_name_plural = "Codeable References"
        app_label = "fhir"
