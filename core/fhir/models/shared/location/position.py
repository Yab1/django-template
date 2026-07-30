"""
Generated concrete model for LocationPosition

This model is generated from the abstract LocationPosition model.
"""

from ehr_common.models import LocationPosition as AbstractLocationPosition


class LocationPosition(AbstractLocationPosition):
    class Meta:
        verbose_name = "Location Position"
        verbose_name_plural = "Location Positions"
        app_label = "fhir"
