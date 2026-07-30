"""
Generated concrete model for Url

This model is generated from the abstract Url model.
"""

from ehr_common.models import Url as AbstractUrl


class Url(AbstractUrl):
    class Meta:
        verbose_name = "Url"
        verbose_name_plural = "Urls"
        app_label = "fhir"
