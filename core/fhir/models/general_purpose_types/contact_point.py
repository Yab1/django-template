"""
Generated concrete model for ContactPoint

This model is generated from the abstract ContactPoint model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import ContactPoint as AbstractContactPoint


class ContactPoint(AbstractContactPoint):
    system = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_point_system",
        help_text=_("Telecommunications form for contact point"),
    )

    use = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_point_use",
        help_text=_("Identifies the purpose for the contact point"),
    )

    period = models.ForeignKey(
        "fhir.Period",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_point_period",
        help_text=_("Time period when the contact point was/is in use"),
    )

    class Meta:
        verbose_name = "Contact Point"
        verbose_name_plural = "Contact Points"
        app_label = "fhir"
