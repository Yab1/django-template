"""
Generated concrete model for Identifier

This model is generated from the abstract Identifier model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Identifier as AbstractIdentifier


class Identifier(AbstractIdentifier):
    use = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identifier_use",
        help_text=_("Purpose of this identifier"),
    )

    type = models.ForeignKey(
        "fhir.CodeableConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identifier_type",
        help_text=_("A coded type for the identifier that indicates what kind of identifier it is"),
    )

    period = models.ForeignKey(
        "fhir.Period",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identifier_period",
        help_text=_("Time period when id is/was valid for use"),
    )

    assigner = models.ForeignKey(
        "fhir.Reference",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="identifier_assigner",
        help_text=_("The organization that assigned the identifier"),
    )

    class Meta:
        verbose_name = "Identifier"
        verbose_name_plural = "Identifiers"
        app_label = "fhir"
