"""
Generated concrete model for TimingRepeat

This model is generated from the abstract TimingRepeat model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import TimingRepeat as AbstractTimingRepeat


class TimingRepeat(AbstractTimingRepeat):
    bounds_duration = models.ForeignKey(
        "fhir.Quantity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timing_repeat_bounds_duration",
        help_text=_("Length/Range of lengths, or (Start and/or end) limits. Duration value"),
    )

    bounds_range = models.ForeignKey(
        "fhir.Range",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timing_repeat_bounds_range",
        help_text=_("Length/Range of lengths, or (Start and/or end) limits. Range value"),
    )

    bounds_period = models.ForeignKey(
        "fhir.Period",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timing_repeat_bounds_period",
        help_text=_("Length/Range of lengths, or (Start and/or end) limits. Period value"),
    )

    duration_unit = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timing_repeat_duration_unit",
        help_text=_("Units of time for duration (s | min | h | d | wk | mo | a)"),
    )

    period_unit = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="timing_repeat_period_unit",
        help_text=_("Units of time for period (s | min | h | d | wk | mo | a)"),
    )

    day_of_week = models.ManyToManyField(
        "fhir.Coding",
        blank=True,
        related_name="timing_repeat_day_of_week",
        help_text=_("Mon | Tue | Wed | Thu | Fri | Sat | Sun. The days of the week when the event should occur"),
    )

    when = models.ManyToManyField(
        "fhir.Coding",
        blank=True,
        related_name="timing_repeat_when",
        help_text=_("Code for time period of occurrence. When the event should occur during the day"),
    )

    class Meta:
        verbose_name = "Timing Repeat"
        verbose_name_plural = "Timing Repeats"
        app_label = "fhir"
