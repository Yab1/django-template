from rest_framework import serializers

from core.api.serializers import ContentTypeNaturalKeyField
from core.files.models import FileObject


class FileUploadInputSerializer(serializers.Serializer):
    file = serializers.FileField()
    resource = serializers.CharField()
    field = serializers.CharField()
    object_id = serializers.UUIDField()


class FileListQuerySerializer(serializers.Serializer):
    resource = serializers.CharField()
    object_id = serializers.UUIDField()
    field = serializers.CharField(required=False)


class FileObjectSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    content_type = ContentTypeNaturalKeyField(source="content_type_id")

    class Meta:
        model = FileObject
        fields = (
            "id",
            "reference_id",
            "url",
            "filename",
            "media_type",
            "size",
            "driver",
            "resource",
            "field",
            "content_type",
            "object_id",
            "created_at",
            "updated_at",
        )

    def get_url(self, obj: FileObject) -> str:
        if obj.resource == "id_document":
            return ""
        if not obj.file:
            return ""
        return obj.file.url
