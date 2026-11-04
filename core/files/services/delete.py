from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.http import Http404

from core.files.constants import RESOURCE_ID_DOCUMENT
from core.files.models import FileObject
from core.files.selectors.file_object import file_object_get
from core.security.services import user_has_permission
from core.users.models import User


def _can_delete(*, row: FileObject, user: User) -> bool:
    if user_has_permission(user=user, action="files:file:list_all"):
        return True
    return row.created_by_id == user.id or row.object_id == user.id


def file_object_delete(*, file_id: UUID, user: User) -> FileObject:
    row = file_object_get(file_id=file_id)
    if row.resource == RESOURCE_ID_DOCUMENT:
        raise Http404("File not found.")
    if not _can_delete(row=row, user=user):
        raise PermissionDenied("You cannot delete this file.")
    row.delete(user=user)
    return row
