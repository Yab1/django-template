from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.cookbook.models import Recipe


@extend_schema_serializer(component_name="RecipeOutput")
class RecipeOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_id = serializers.CharField()
    title = serializers.CharField()
    body = serializers.CharField()
    status = serializers.CharField()
    is_visible = serializers.BooleanField()
    created_by_id = serializers.UUIDField(allow_null=True)
    updated_by_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


@extend_schema_serializer(component_name="RecipeCreateInput")
class RecipeCreateInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField(required=False, allow_blank=True, default="")


@extend_schema_serializer(component_name="RecipeUpdateInput")
class RecipeUpdateInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    body = serializers.CharField(required=False, allow_blank=True)
    is_visible = serializers.BooleanField(required=False)
    metadata = serializers.JSONField(required=False)


class RecipeListQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Recipe.Status.choices, required=False)
    is_visible = serializers.BooleanField(required=False)
    title = serializers.CharField(required=False)
    order_by = serializers.ChoiceField(
        required=False,
        choices=["created_at", "-created_at", "updated_at", "-updated_at", "title", "-title"],
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)
    offset = serializers.IntegerField(required=False, min_value=0)
