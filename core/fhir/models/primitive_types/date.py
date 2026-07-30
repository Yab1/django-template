"""
Generated concrete model for Date

This model is generated from the abstract Date model.
"""

from ehr_common.models import Date as AbstractDate


class Date(AbstractDate):
    class Meta:
        verbose_name = "Date"
        verbose_name_plural = "Dates"
        app_label = "fhir"
