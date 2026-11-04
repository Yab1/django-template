from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.http import Http404

from core.files.constants import RESOURCE_ID_DOCUMENT
from core.files.models import FileObject
from core.files.targets import get_file_target, model_for_resource
from core.security.services import user_has_permission
from core.users.models import User


def file_object_get(*, file_id: UUID) -> FileObject:
    try:
        return FileObject.objects.get(pk=file_id, deleted_at__isnull=True)
    except FileObject.DoesNotExist as exc:
        raise Http404("File not found.") from exc


def file_object_visible_to(*, row: FileObject, user: User) -> bool:
    if row.resource == RESOURCE_ID_DOCUMENT:
        return False
    if user_has_permission(user=user, action="files:file:list_all"):
        return True
    return row.created_by_id == user.id or row.object_id == user.id


def file_object_list(
    *,
    user: User,
    resource: str,
    object_id: UUID,
    field: str | None = None,
) -> QuerySet[FileObject]:
    if resource.strip().lower() == RESOURCE_ID_DOCUMENT:
        raise Http404("File not found.")
    if field:
        target = get_file_target(resource=resource, field=field)
        model = target.model
    else:
        model = model_for_resource(resource=resource)
    if not user_has_permission(user=user, action="files:file:list_all") and object_id != user.id:
        try:
            instance = model.objects.get(pk=object_id)
        except model.DoesNotExist as exc:
            raise Http404("File not found.") from exc
        owner_id = getattr(instance, "created_by_id", None)
        if owner_id != user.id:
            raise Http404("File not found.")

    content_type = ContentType.objects.get_for_model(model)
    qs = FileObject.objects.filter(
        content_type=content_type,
        object_id=object_id,
        deleted_at__isnull=True,
        is_visible=True,
    )
    if field:
        qs = qs.filter(field=field.strip().lower())
    return qs
