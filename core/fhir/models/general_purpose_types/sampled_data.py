"""
Generated concrete model for SampledData

This model is generated from the abstract SampledData model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import SampledData as AbstractSampledData


class SampledData(AbstractSampledData):
    origin = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.PROTECT,
        related_name="sampled_data_origin",
        help_text=_("Zero value and units. The base quantity that a measured value of zero represents"),
    )

    interval_unit = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.PROTECT,
        related_name="sampled_data_interval_unit",
        help_text=_("Units of time for the interval (UCUM codes)"),
    )

    class Meta:
        verbose_name = "Sampled Data"
        verbose_name_plural = "Sampled Data"
        app_label = "fhir"
