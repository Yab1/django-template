from rest_framework import serializers

from core.notifications.constants import FORMAT_HTML, FORMAT_TEXT
from core.notifications.models import NotificationTemplate


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = (
            "id",
            "reference_id",
            "channel",
            "category",
            "locale",
            "subject",
            "body",
            "format",
            "is_active",
            "created_at",
            "updated_at",
        )


class NotificationTemplateUpdateInputSerializer(serializers.Serializer):
    subject = serializers.CharField(required=False)
    body = serializers.CharField(required=False)
    format = serializers.ChoiceField(choices=[FORMAT_TEXT, FORMAT_HTML], required=False)
    is_active = serializers.BooleanField(required=False)
