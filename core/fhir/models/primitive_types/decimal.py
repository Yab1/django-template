"""
Generated concrete model for Decimal

This model is generated from the abstract Decimal model.
"""

from ehr_common.models import Decimal as AbstractDecimal


class Decimal(AbstractDecimal):
    class Meta:
        verbose_name = "Decimal"
        verbose_name_plural = "Decimals"
        app_label = "fhir"
