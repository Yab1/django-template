"""
Generated concrete model for AvailableTime

This model is generated from the abstract AvailableTime model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import AvailableTime as AbstractAvailableTime


class AvailableTime(AbstractAvailableTime):
    days_of_week = models.ManyToManyField(
        "fhir.Coding",
        blank=True,
        related_name="available_time_days_of_week",
        help_text=_("Days of week: mon | tue | wed | thu | fri | sat | sun"),
    )

    class Meta:
        verbose_name = "Available Time"
        verbose_name_plural = "Available Times"
        app_label = "fhir"
