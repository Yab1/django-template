from rest_framework import serializers

from core.notifications.constants import CATEGORIES, CHANNELS, STATUSES
from core.notifications.models import NotificationAttempt, NotificationDelivery


class NotificationDeliverySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_id = serializers.CharField()
    user_id = serializers.UUIDField()
    channel = serializers.CharField()
    category = serializers.CharField()
    destination = serializers.CharField()
    subject = serializers.CharField()
    body = serializers.CharField()
    format = serializers.CharField()
    status = serializers.CharField()
    attempts = serializers.IntegerField()
    max_attempts = serializers.IntegerField()
    next_attempt_at = serializers.DateTimeField(allow_null=True)
    last_error = serializers.CharField()
    provider_ref = serializers.CharField()
    idempotency_key = serializers.CharField(allow_null=True)
    read_at = serializers.DateTimeField(allow_null=True)
    event_code = serializers.CharField()
    resource_type = serializers.CharField()
    resource_id = serializers.UUIDField(allow_null=True)
    priority = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class NotificationAttemptSerializer(serializers.Serializer):
    attempt = serializers.IntegerField()
    status = serializers.CharField()
    error = serializers.CharField()
    created_at = serializers.DateTimeField()


class NotificationDeliveryDetailSerializer(NotificationDeliverySerializer):
    attempt_log = NotificationAttemptSerializer(many=True)


class NotificationSendInputSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    category = serializers.ChoiceField(choices=CATEGORIES)
    channels = serializers.ListField(
        child=serializers.ChoiceField(choices=CHANNELS),
        required=False,
        allow_empty=True,
    )
    data = serializers.DictField(required=False)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)
    event_code = serializers.CharField(max_length=128, required=False, default="admin.send")
    resource_type = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    resource_id = serializers.UUIDField(required=False, allow_null=True)


class NotificationInboxQuerySerializer(serializers.Serializer):
    unread = serializers.BooleanField(required=False, default=False)


class NotificationDeliveryListQuerySerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False)
    channel = serializers.ChoiceField(choices=CHANNELS, required=False)
    status = serializers.ChoiceField(choices=STATUSES, required=False)
    category = serializers.ChoiceField(choices=CATEGORIES, required=False)


class UnreadCountSerializer(serializers.Serializer):
    unread = serializers.IntegerField()


class ReadAllOutputSerializer(serializers.Serializer):
    updated = serializers.IntegerField()


# ModelSerializer used only so attempt_log prefetch serializes without extra mapping.
class NotificationAttemptModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationAttempt
        fields = ("attempt", "status", "error", "created_at")


class NotificationDeliveryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationDelivery
        fields = (
            "id",
            "reference_id",
            "user_id",
            "channel",
            "category",
            "destination",
            "subject",
            "body",
            "format",
            "status",
            "attempts",
            "max_attempts",
            "next_attempt_at",
            "last_error",
            "provider_ref",
            "idempotency_key",
            "read_at",
            "event_code",
            "resource_type",
            "resource_id",
            "priority",
            "created_at",
            "updated_at",
        )
