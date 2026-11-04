"""
App admin interfaces.

This module exports all admin classes for the app.
"""

from .notification_attempt_admin import NotificationAttemptAdmin
from .notification_delivery_admin import NotificationDeliveryAdmin
from .notification_preference_admin import NotificationPreferenceAdmin
from .notification_template_admin import NotificationTemplateAdmin

__all__ = [
    "NotificationAttemptAdmin",
    "NotificationDeliveryAdmin",
    "NotificationPreferenceAdmin",
    "NotificationTemplateAdmin",
]
