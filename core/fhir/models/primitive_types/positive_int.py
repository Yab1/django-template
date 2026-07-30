"""
Generated concrete model for PositiveInt

This model is generated from the abstract PositiveInt model.
"""

from ehr_common.models import PositiveInt as AbstractPositiveInt


class PositiveInt(AbstractPositiveInt):
    class Meta:
        verbose_name = "Positive Int"
        verbose_name_plural = "Positive Ints"
        app_label = "fhir"
