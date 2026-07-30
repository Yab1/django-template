"""
Generated concrete model for HumanName

This model is generated from the abstract HumanName model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import HumanName as AbstractHumanName


class HumanName(AbstractHumanName):
    use = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="human_name_use",
        help_text=_("Identifies the purpose for this name"),
    )

    period = models.ForeignKey(
        "fhir.Period",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="human_name_period",
        help_text=_("Time period when name was/is in use"),
    )

    class Meta:
        verbose_name = "Human Name"
        verbose_name_plural = "Human Names"
        app_label = "fhir"
