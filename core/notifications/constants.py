from django.db import models
from django.utils.translation import gettext_lazy as _

OPENAPI_TAG_NOTIFICATIONS = "notifications"

CHANNEL_IN_APP = "in_app"
CHANNEL_EMAIL = "email"
CHANNEL_SMS = "sms"
CHANNEL_PUSH = "push"
CHANNEL_TELEGRAM = "telegram"

CHANNELS = (
    CHANNEL_IN_APP,
    CHANNEL_EMAIL,
    CHANNEL_SMS,
    CHANNEL_PUSH,
    CHANNEL_TELEGRAM,
)

CATEGORY_WELCOME = "welcome"
CATEGORY_ALERT = "alert"
CATEGORY_STATUS = "status"
CATEGORY_TRANSACTIONAL = "transactional"
CATEGORY_SECURITY = "security"

CATEGORIES = (
    CATEGORY_WELCOME,
    CATEGORY_ALERT,
    CATEGORY_STATUS,
    CATEGORY_TRANSACTIONAL,
    CATEGORY_SECURITY,
)

STATUS_PENDING = "pending"
STATUS_SENDING = "sending"
STATUS_SENT = "sent"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"

STATUSES = (
    STATUS_PENDING,
    STATUS_SENDING,
    STATUS_SENT,
    STATUS_FAILED,
    STATUS_SKIPPED,
)

PRIORITY_LOW = "low"
PRIORITY_NORMAL = "normal"
PRIORITY_HIGH = "high"

FORMAT_TEXT = "text"
FORMAT_HTML = "html"

# Defaults when the user has no stored preference row.
DEFAULT_CHANNEL_ENABLED = {
    CHANNEL_IN_APP: True,
    CHANNEL_EMAIL: True,
    CHANNEL_SMS: False,
    CHANNEL_PUSH: False,
    CHANNEL_TELEGRAM: False,
}

# Cannot be turned off via preferences (deployment flags can still disable the channel).
MANDATORY_CHANNELS_BY_CATEGORY = {
    CATEGORY_SECURITY: frozenset({CHANNEL_IN_APP, CHANNEL_EMAIL}),
}


class Channel(models.TextChoices):
    IN_APP = CHANNEL_IN_APP, _("In-app")
    EMAIL = CHANNEL_EMAIL, _("Email")
    SMS = CHANNEL_SMS, _("SMS")
    PUSH = CHANNEL_PUSH, _("Push")
    TELEGRAM = CHANNEL_TELEGRAM, _("Telegram")


class Category(models.TextChoices):
    WELCOME = CATEGORY_WELCOME, _("Welcome")
    ALERT = CATEGORY_ALERT, _("Alert")
    STATUS = CATEGORY_STATUS, _("Status")
    TRANSACTIONAL = CATEGORY_TRANSACTIONAL, _("Transactional")
    SECURITY = CATEGORY_SECURITY, _("Security")


class DeliveryStatus(models.TextChoices):
    PENDING = STATUS_PENDING, _("Pending")
    SENDING = STATUS_SENDING, _("Sending")
    SENT = STATUS_SENT, _("Sent")
    FAILED = STATUS_FAILED, _("Failed")
    SKIPPED = STATUS_SKIPPED, _("Skipped")


class Priority(models.TextChoices):
    LOW = PRIORITY_LOW, _("Low")
    NORMAL = PRIORITY_NORMAL, _("Normal")
    HIGH = PRIORITY_HIGH, _("High")


class BodyFormat(models.TextChoices):
    TEXT = FORMAT_TEXT, _("Text")
    HTML = FORMAT_HTML, _("HTML")
