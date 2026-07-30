"""
Generated concrete model for Availability

This model is generated from the abstract Availability model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Availability as AbstractAvailability


class Availability(AbstractAvailability):
    available_times = models.ManyToManyField(
        "fhir.AvailableTime",
        blank=True,
        related_name="availability_available_times",
        help_text=_("Times the item is available"),
    )

    not_available_times = models.ManyToManyField(
        "fhir.NotAvailableTime",
        blank=True,
        related_name="availability_not_available_times",
        help_text=_("Not available during this time due to provided reason"),
    )

    class Meta:
        verbose_name = "Availability"
        verbose_name_plural = "Availabilities"
        app_label = "fhir"
