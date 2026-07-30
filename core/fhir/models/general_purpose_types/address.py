"""
Generated concrete model for Address

This model is generated from the abstract Address model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Address as AbstractAddress


class Address(AbstractAddress):
    use = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="address_use",
        help_text=_("Purpose of this address: home | work | temp | old | billing"),
    )

    type = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="address_type",
        help_text=_("Type of address: postal | physical | both"),
    )

    period = models.ForeignKey(
        "fhir.Period",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="address_period",
        help_text=_("Time period when address was/is in use"),
    )

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        app_label = "fhir"
