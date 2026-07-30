"""
Generated concrete model for Instant

This model is generated from the abstract Instant model.
"""

from ehr_common.models import Instant as AbstractInstant


class Instant(AbstractInstant):
    class Meta:
        verbose_name = "Instant"
        verbose_name_plural = "Instants"
        app_label = "fhir"
