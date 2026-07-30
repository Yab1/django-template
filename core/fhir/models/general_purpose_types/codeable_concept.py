"""
Generated concrete model for CodeableConcept

This model is generated from the abstract CodeableConcept model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import CodeableConcept as AbstractCodeableConcept


class CodeableConcept(AbstractCodeableConcept):
    coding = models.ManyToManyField(
        "fhir.Coding",
        blank=True,
        related_name="codeable_concept_coding",
        help_text=_("Code defined by a terminology system. A set of coded values from one or more coding systems"),
    )

    class Meta:
        verbose_name = "Codeable Concept"
        verbose_name_plural = "Codeable Concepts"
        app_label = "fhir"
