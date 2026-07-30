"""
Location models package.

This module exports all location-related models.
"""

from .location import Location
from .position import LocationPosition

__all__ = [
    "Location",
    "LocationPosition",
]
