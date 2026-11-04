from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from core.files.adapters.clamav import clamav_scan
from core.files.constants import RESOURCE_ID_DOCUMENT
from core.files.models import FileObject
from core.files.targets import FileTarget, get_file_target
from core.security.services import user_has_permission
from core.users.models import User


def _basename(name: str) -> str:
    cleaned = Path(name.replace("\\", "/")).name.strip()
    if not cleaned or cleaned in {".", ".."}:
        return "upload"
    return cleaned[:255]


def _media_type(*, upload: UploadedFile) -> str:
    raw = (getattr(upload, "content_type", None) or "").split(";")[0].strip().lower()
    if raw and raw != "application/octet-stream":
        return raw
    guessed, _ = mimetypes.guess_type(upload.name or "")
    return (guessed or "application/octet-stream").lower()


def _content_hash(*, upload: UploadedFile) -> str:
    digest = hashlib.sha256()
    for chunk in upload.chunks():
        digest.update(chunk)
    upload.seek(0)
    return digest.hexdigest()


def _allowed_types(target: FileTarget) -> set[str]:
    if target.types:
        return {item.lower() for item in target.types}
    return {item.lower() for item in getattr(settings, "FILE_ALLOWED_TYPES", ())}


def _assert_can_attach(*, user: User, target: FileTarget, instance) -> None:
    if user_has_permission(user=user, action="files:file:attach_any"):
        return
    if target.model is User and instance.pk == user.pk:
        return
    owner_id = getattr(instance, "created_by_id", None)
    if owner_id is not None and owner_id == user.pk:
        return
    raise ValidationError({"object_id": "You cannot attach a file to this record."})


def file_object_create(
    *,
    user: User,
    upload: UploadedFile,
    resource: str,
    field: str,
    object_id: UUID,
    caller_authorized: bool = False,
    content_scanned: bool = False,
    file_id: UUID | None = None,
    storage_name: str | None = None,
    prewritten: bool = False,
    size_checked: bool = False,
) -> FileObject:
    if not getattr(settings, "FILES_ENABLED", True):
        raise ValidationError({"file": "File uploads are disabled."})

    normalized = resource.strip().lower()
    if normalized == RESOURCE_ID_DOCUMENT and not caller_authorized:
        raise ValidationError({"resource": "Identity documents use the parties document API."})
    if normalized == RESOURCE_ID_DOCUMENT and not content_scanned:
        raise ValidationError({"file": "Identity document content must be scanned before storage."})

    target = get_file_target(resource=resource, field=field)
    try:
        instance = target.model.objects.get(pk=object_id)
    except target.model.DoesNotExist as exc:
        raise ValidationError({"object_id": "Record not found."}) from exc

    if not caller_authorized:
        _assert_can_attach(user=user, target=target, instance=instance)

    size = int(getattr(upload, "size", 0) or 0)
    max_bytes = int(getattr(settings, "FILE_MAX_BYTES", 10 * 1024 * 1024))
    if not size_checked:
        if size <= 0:
            raise ValidationError({"file": "Empty file."})
        if size > max_bytes:
            raise ValidationError({"file": "File exceeds max size."})

    media_type = _media_type(upload=upload)
    allowed = _allowed_types(target)
    if allowed and media_type not in allowed:
        raise ValidationError({"file": f"Content type {media_type} not allowed."})

    # Identity documents are scanned as plaintext by the parties service. Never scan ciphertext.
    if normalized != RESOURCE_ID_DOCUMENT and not content_scanned and getattr(settings, "CLAMAV_ENABLED", False):
        clamav_scan(upload=upload)
    content_hash = _content_hash(upload=upload)

    content_type = ContentType.objects.get_for_model(target.model)
    filename = _basename(upload.name or "")
    driver = str(getattr(settings, "STORAGE_DRIVER", "") or "local")

    with transaction.atomic():
        if target.replace:
            previous = FileObject.objects.filter(
                content_type=content_type,
                object_id=instance.pk,
                field=target.field,
                deleted_at__isnull=True,
            )
            for row in previous:
                row.delete(user=user)

        obj = FileObject(
            filename=filename,
            media_type=media_type,
            size=size,
            content_hash=content_hash,
            driver=driver,
            resource=target.resource,
            field=target.field,
            content_type=content_type,
            object_id=instance.pk,
            created_by=user,
        )
        if file_id is not None:
            obj.id = file_id
        if prewritten:
            if not storage_name:
                raise ValidationError({"file": "Prewritten storage name is required."})
            obj.file.name = storage_name
        else:
            obj.file = upload
        obj.full_clean()
        obj.save()
        return obj
