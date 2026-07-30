"""Shared serializers for ``django.contrib.contenttypes.models.ContentType``."""

from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.common.utils import content_type_from_natural_key


@extend_schema_serializer(component_name="ContentTypeCompactSerializer")
class ContentTypeCompactSerializer(serializers.Serializer):
    """
    Compact representation of a ContentType row.

    ``name`` is Django's ``ContentType.name`` property (verbose name of the model class),
    not a database column.
    """

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    app_label = serializers.CharField(read_only=True)


@extend_schema_serializer(component_name="ContentTypeNaturalKeyField")
class ContentTypeNaturalKeyField(serializers.CharField):
    """
    Read/write field for ContentType via natural key ``app_label.model_name``.

    Accepts strings like ``individuals.practitioner`` on input and returns
    the corresponding ``content_type_id`` integer value for model/service code.
    """

    def to_internal_value(self, data):
        natural_key = super().to_internal_value(data).strip().lower()
        content_type = content_type_from_natural_key(natural_key=natural_key)
        return content_type.id

    def to_representation(self, value):
        if value is None:
            return None
        if isinstance(value, ContentType):
            return f"{value.app_label}.{value.model}"
        if isinstance(value, int):
            content_type = ContentType.objects.filter(id=value).first()
            if content_type:
                return f"{content_type.app_label}.{content_type.model}"
        return str(value)
