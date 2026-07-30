"""
Generated concrete model for Range

This model is generated from the abstract Range model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Range as AbstractRange


class Range(AbstractRange):
    low = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="range_low",
        help_text=_("Low limit. The lower bound of the range"),
    )

    high = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="range_high",
        help_text=_("High limit. The upper bound of the range"),
    )

    class Meta:
        verbose_name = "Range"
        verbose_name_plural = "Ranges"
        app_label = "fhir"
