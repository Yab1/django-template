"""
Generated concrete model for Boolean

This model is generated from the abstract Boolean model.
"""

from ehr_common.models import Boolean as AbstractBoolean


class Boolean(AbstractBoolean):
    class Meta:
        verbose_name = "Boolean"
        verbose_name_plural = "Booleans"
        app_label = "fhir"
