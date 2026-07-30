"""
Generated concrete model for DateTime

This model is generated from the abstract DateTime model.
"""

from ehr_common.models import DateTime as AbstractDateTime


class DateTime(AbstractDateTime):
    class Meta:
        verbose_name = "Date Time"
        verbose_name_plural = "Date Times"
        app_label = "fhir"
