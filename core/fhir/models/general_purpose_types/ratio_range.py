"""
Generated concrete model for RatioRange

This model is generated from the abstract RatioRange model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import RatioRange as AbstractRatioRange


class RatioRange(AbstractRatioRange):
    low_numerator = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratio_range_low_numerator",
        help_text=_("Low numerator value. The lower bound of the numerator range"),
    )

    high_numerator = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratio_range_high_numerator",
        help_text=_("High numerator value. The upper bound of the numerator range"),
    )

    denominator = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratio_range_denominator",
        help_text=_("Denominator value. If the denominator is missing, it means the denominator is 1"),
    )

    class Meta:
        verbose_name = "Ratio Range"
        verbose_name_plural = "Ratio Ranges"
        app_label = "fhir"
