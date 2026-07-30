"""
Generated concrete model for String

This model is generated from the abstract String model.
"""

from ehr_common.models import String as AbstractString


class String(AbstractString):
    class Meta:
        verbose_name = "String"
        verbose_name_plural = "Strings"
        app_label = "fhir"
