"""
Metadata Types models.

This package contains metadata types models.
"""

from .author import Author
from .availability.availability import Availability
from .availability.available_time import AvailableTime
from .availability.not_available_time import NotAvailableTime
from .extended_contact_detail import ExtendedContactDetail
from .virtual_service_detail import VirtualServiceDetail

__all__ = [
    "Availability",
    "AvailableTime",
    "NotAvailableTime",
    "ExtendedContactDetail",
    "VirtualServiceDetail",
    "Author",
]
