"""
Generated concrete model for Coding

This model is generated from the abstract Coding model.
"""

from ehr_common.models import Coding as AbstractCoding


class Coding(AbstractCoding):
    class Meta:
        verbose_name = "Coding"
        verbose_name_plural = "Codings"
        app_label = "fhir"
