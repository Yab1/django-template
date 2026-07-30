from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


@extend_schema_serializer(component_name="SystemHealthCheckOutput")
class SystemHealthCheckOutputSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "unhealthy"])
    database = serializers.ChoiceField(choices=["ok", "error"])
    cache = serializers.ChoiceField(choices=["ok", "error"])
    rabbitmq = serializers.ChoiceField(choices=["ok", "error", "not_configured"])
    minio = serializers.ChoiceField(choices=["ok", "error", "not_configured"])
