"""
Generated concrete model for VirtualServiceDetail

This model is generated from the abstract VirtualServiceDetail model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import VirtualServiceDetail as AbstractVirtualServiceDetail


class VirtualServiceDetail(AbstractVirtualServiceDetail):
    channel_type = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="virtual_service_detail_channel_type",
        help_text=_("Channel Type (Coding) for the virtual service"),
    )

    address_contact_point = models.ForeignKey(
        "fhir.ContactPoint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="virtual_service_detail_address_contact_point",
        help_text=_("Contact address/number as ContactPoint"),
    )

    address_extended_contact_detail = models.ForeignKey(
        "fhir.ExtendedContactDetail",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="virtual_service_detail_address_extended_contact_detail",
        help_text=_("Contact address/number as ExtendedContactDetail"),
    )

    class Meta:
        verbose_name = "Virtual Service Detail"
        verbose_name_plural = "Virtual Service Details"
        app_label = "fhir"
