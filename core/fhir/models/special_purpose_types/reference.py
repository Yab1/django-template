"""
Generated concrete model for Reference

This model is generated from the abstract Reference model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Reference as AbstractReference


class Reference(AbstractReference):
    type = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reference_type",
        help_text=_("Type the reference refers to (e.g. 'Patient') - must be a resource in resources"),
    )

    identifier = models.ForeignKey(
        "fhir.Identifier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reference_identifier",
        help_text=_(
            "Logical reference, when literal reference is not known. An identifier that can be used to resolve the reference"
        ),
    )

    class Meta:
        verbose_name = "Reference"
        verbose_name_plural = "References"
        app_label = "fhir"
