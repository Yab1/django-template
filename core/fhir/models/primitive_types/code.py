"""
Generated concrete model for Code

This model is generated from the abstract Code model.
"""

from ehr_common.models import Code as AbstractCode


class Code(AbstractCode):
    class Meta:
        verbose_name = "Code"
        verbose_name_plural = "Codes"
        app_label = "fhir"
