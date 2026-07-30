"""
Generated concrete model for Location

This model is generated from the abstract Location model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from ehr_common.models import Location as AbstractLocation


class Location(AbstractLocation):
    identifier = models.ManyToManyField(
        "fhir.Identifier",
        blank=True,
        related_name="location_identifier",
        help_text=_("Unique code or number identifying the location to its users"),
    )

    status = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_status",
        help_text=_("The operational status of the location"),
    )

    operational_status = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_operational_status",
        help_text=_("The operational status of the location (typically only for a bed/room)"),
    )

    mode = models.ForeignKey(
        "fhir.Coding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_mode",
        help_text=_("Indicates whether a resource instance represents a specific location or a class of locations"),
    )

    type = models.ManyToManyField(
        "fhir.CodeableConcept",
        blank=True,
        related_name="location_type",
        help_text=_("Indicates the type of function performed at the location"),
    )

    contact = models.ManyToManyField(
        "fhir.ExtendedContactDetail",
        blank=True,
        related_name="location_contact",
        help_text=_("Contact details of the location"),
    )

    address = models.ForeignKey(
        "fhir.Address",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_address",
        help_text=_("Physical location"),
    )

    form = models.ForeignKey(
        "fhir.CodeableConcept",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_form",
        help_text=_("Physical form of the location"),
    )

    managing_organization = models.ForeignKey(
        "fhir.Reference",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_managing_organization",
        help_text=_("Organization responsible for provisioning and upkeep"),
    )

    part_of = models.ForeignKey(
        "fhir.Reference",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_part_of",
        help_text=_("Another Location this Location is physically part of"),
    )

    characteristic = models.ManyToManyField(
        "fhir.CodeableConcept",
        blank=True,
        related_name="location_characteristic",
        help_text=_("A characteristic of the location"),
    )

    hours_of_operation = models.ManyToManyField(
        "fhir.Availability",
        blank=True,
        related_name="location_hours_of_operation",
        help_text=_("What days/times during a week is this location usually open"),
    )

    virtual_service = models.ManyToManyField(
        "fhir.VirtualServiceDetail",
        blank=True,
        related_name="location_virtual_service",
        help_text=_("Connection details of a virtual service (e.g. conference call, webex)"),
    )

    endpoint = models.ManyToManyField(
        "fhir.Reference",
        blank=True,
        related_name="location_endpoint",
        help_text=_("Technical endpoints providing access to services operated for the location"),
    )

    position = models.ForeignKey(
        "fhir.LocationPosition",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="location_position",
        help_text=_("The absolute geographic location"),
    )

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        app_label = "fhir"
