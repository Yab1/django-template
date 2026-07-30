"""
Generated concrete model for Uuid

This model is generated from the abstract Uuid model.
"""

from ehr_common.models import Uuid as AbstractUuid


class Uuid(AbstractUuid):
    class Meta:
        verbose_name = "Uuid"
        verbose_name_plural = "Uuids"
        app_label = "fhir"
