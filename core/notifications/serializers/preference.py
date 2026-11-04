from rest_framework import serializers

from core.notifications.constants import CATEGORIES, CHANNELS
from core.notifications.models import NotificationPreference


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = (
            "id",
            "user_id",
            "channel",
            "category",
            "enabled",
            "destination",
            "created_at",
            "updated_at",
        )


class NotificationPreferenceItemInputSerializer(serializers.Serializer):
    channel = serializers.ChoiceField(choices=CHANNELS)
    category = serializers.ChoiceField(choices=CATEGORIES)
    enabled = serializers.BooleanField()
    destination = serializers.CharField(required=False, allow_blank=True, default="")


class NotificationPreferenceUpsertInputSerializer(serializers.Serializer):
    items = NotificationPreferenceItemInputSerializer(many=True)


class NotificationPreferenceEffectiveSerializer(serializers.Serializer):
    channel = serializers.CharField()
    category = serializers.CharField()
    enabled = serializers.BooleanField()
    default_enabled = serializers.BooleanField()
    mandatory = serializers.BooleanField()
    destination = serializers.CharField()
    stored = serializers.BooleanField()
