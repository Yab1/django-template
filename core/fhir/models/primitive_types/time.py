"""
Generated concrete model for Time

This model is generated from the abstract Time model.
"""

from ehr_common.models import Time as AbstractTime


class Time(AbstractTime):
    class Meta:
        verbose_name = "Time"
        verbose_name_plural = "Times"
        app_label = "fhir"
