"""
Generated concrete model for UnsignedInt

This model is generated from the abstract UnsignedInt model.
"""

from ehr_common.models import UnsignedInt as AbstractUnsignedInt


class UnsignedInt(AbstractUnsignedInt):
    class Meta:
        verbose_name = "Unsigned Int"
        verbose_name_plural = "Unsigned Ints"
        app_label = "fhir"
