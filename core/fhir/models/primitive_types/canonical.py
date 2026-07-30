"""
Generated concrete model for Canonical

This model is generated from the abstract Canonical model.
"""

from ehr_common.models import Canonical as AbstractCanonical


class Canonical(AbstractCanonical):
    class Meta:
        verbose_name = "Canonical"
        verbose_name_plural = "Canonicals"
        app_label = "fhir"
