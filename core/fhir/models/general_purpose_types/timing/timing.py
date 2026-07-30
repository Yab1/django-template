"""
Generated concrete model for Timing

This model is generated from the abstract Timing model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Timing as AbstractTiming


class Timing(AbstractTiming):
    code = models.ForeignKey(
        "fhir.CodeableConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timing_code",
        help_text=_(
            "BID | TID | QID | AM | PM | QD | QOD | Q4H | Q6H | etc. A coded concept that defines the timing pattern"
        ),
    )

    repeat = models.ForeignKey(
        "fhir.TimingRepeat",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timing_repeat",
        help_text=_("A repeating schedule for the event"),
    )

    class Meta:
        verbose_name = "Timing"
        verbose_name_plural = "Timings"
        app_label = "fhir"
