"""
Generated concrete model for Oid

This model is generated from the abstract Oid model.
"""

from ehr_common.models import Oid as AbstractOid


class Oid(AbstractOid):
    class Meta:
        verbose_name = "Oid"
        verbose_name_plural = "Oids"
        app_label = "fhir"
