"""
Generated concrete model for Ratio

This model is generated from the abstract Ratio model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Ratio as AbstractRatio


class Ratio(AbstractRatio):
    numerator = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratio_numerator",
        help_text=_("Numerator value. If the numerator is missing, it means the numerator is 1"),
    )

    denominator = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratio_denominator",
        help_text=_("Denominator value. If the denominator is missing, it means the denominator is 1"),
    )

    class Meta:
        verbose_name = "Ratio"
        verbose_name_plural = "Ratios"
        app_label = "fhir"
