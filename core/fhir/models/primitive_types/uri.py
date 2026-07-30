"""
Generated concrete model for Uri

This model is generated from the abstract Uri model.
"""

from ehr_common.models import Uri as AbstractUri


class Uri(AbstractUri):
    class Meta:
        verbose_name = "Uri"
        verbose_name_plural = "Uris"
        app_label = "fhir"
