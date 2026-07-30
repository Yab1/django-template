"""
Generated concrete model for NotAvailableTime

This model is generated from the abstract NotAvailableTime model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import NotAvailableTime as AbstractNotAvailableTime


class NotAvailableTime(AbstractNotAvailableTime):
    during = models.ForeignKey(
        "fhir.Period",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="not_available_time_during",
        help_text=_("Service not available during this period"),
    )

    class Meta:
        verbose_name = "Not Available Time"
        verbose_name_plural = "Not Available Times"
        app_label = "fhir"
