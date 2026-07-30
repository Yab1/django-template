"""
Generated concrete model for ExtendedContactDetail

This model is generated from the abstract ExtendedContactDetail model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import ExtendedContactDetail as AbstractExtendedContactDetail


class ExtendedContactDetail(AbstractExtendedContactDetail):
    purpose = models.ForeignKey(
        "fhir.CodeableConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extended_contact_detail_purpose",
        help_text=_("The purpose of the contact information"),
    )

    name = models.ManyToManyField(
        "fhir.HumanName",
        blank=True,
        related_name="extended_contact_detail_name",
        help_text=_("Name of the contact"),
    )

    telecom = models.ManyToManyField(
        "fhir.ContactPoint",
        blank=True,
        related_name="extended_contact_detail_telecom",
        help_text=_("Contact details for telephone, email, etc"),
    )

    address = models.ForeignKey(
        "fhir.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extended_contact_detail_address",
        help_text=_("Address for the contact"),
    )

    organization = models.ForeignKey(
        "fhir.Reference",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extended_contact_detail_organization",
        help_text=_("Reference to Organization"),
    )

    period = models.ForeignKey(
        "fhir.Period",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="extended_contact_detail_period",
        help_text=_("Period during which the contact information is valid"),
    )

    class Meta:
        verbose_name = "Extended Contact Detail"
        verbose_name_plural = "Extended Contact Details"
        app_label = "fhir"
