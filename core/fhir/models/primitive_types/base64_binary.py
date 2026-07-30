"""
Generated concrete model for Base64Binary

This model is generated from the abstract Base64Binary model.
"""

from ehr_common.models import Base64Binary as AbstractBase64Binary


class Base64Binary(AbstractBase64Binary):
    class Meta:
        verbose_name = "Base64Binary"
        verbose_name_plural = "Base64Binaries"
        app_label = "fhir"
