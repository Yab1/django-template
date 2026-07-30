"""
Generated concrete model for Integer

This model is generated from the abstract Integer model.
"""

from ehr_common.models import Integer as AbstractInteger


class Integer(AbstractInteger):
    class Meta:
        verbose_name = "Integer"
        verbose_name_plural = "Integers"
        app_label = "fhir"
