"""
Generated concrete model for Id

This model is generated from the abstract Id model.
"""

from ehr_common.models import Id as AbstractId


class Id(AbstractId):
    class Meta:
        verbose_name = "Id"
        verbose_name_plural = "Ids"
        app_label = "fhir"
