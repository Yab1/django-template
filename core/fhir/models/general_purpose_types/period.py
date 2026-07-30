"""
Generated concrete model for Period

This model is generated from the abstract Period model.
"""

from ehr_common.models import Period as AbstractPeriod


class Period(AbstractPeriod):
    class Meta:
        verbose_name = "Period"
        verbose_name_plural = "Periods"
        app_label = "fhir"
