"""
Generated concrete model for Quantity

This model is generated from the abstract Quantity model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Quantity as AbstractQuantity


class Quantity(AbstractQuantity):
    comparator = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quantity_comparator",
        help_text=_("How to understand the value"),
    )

    code = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quantity_code",
        help_text=_("Coded form of the unit. A coded form of the unit from the specified system"),
    )

    class Meta:
        verbose_name = "Quantity"
        verbose_name_plural = "Quantities"
        app_label = "fhir"
