"""Sweep unclaimed identity-document objects. Leaves anything that is not an expired claim."""

from __future__ import annotations

import re
from datetime import timedelta
from uuid import UUID

from django.core.files.storage import default_storage
from django.utils import timezone

from core.files.models import FileObject, PendingStorageObject

_KEY = re.compile(r"^id_document/[0-9a-f-]{36}/scan/[0-9]{4}/[0-9]{2}/([0-9a-f-]{36})(\.[a-z0-9]{1,8})?$")
_BATCH = 100


def _walk(prefix: str):
    try:
        dirs, files = default_storage.listdir(prefix)
    except (FileNotFoundError, OSError):
        return
    for name in files:
        yield f"{prefix}/{name}" if prefix else name
    for directory in dirs:
        child = f"{prefix}/{directory}" if prefix else directory
        yield from _walk(child)


def id_document_orphan_sweep(*, limit: int = _BATCH) -> int:
    """Delete objects that have an expired pending claim and no FileObject row."""
    cutoff = timezone.now() - timedelta(hours=1)
    removed = 0
    for raw_key in _walk("id_document"):
        if removed >= limit:
            break
        key = raw_key.lstrip("/")
        match = _KEY.match(key.lower())
        if match is None:
            continue
        try:
            file_id = UUID(match.group(1))
        except ValueError:
            continue
        if FileObject.objects.filter(pk=file_id).exists():
            continue
        pending = PendingStorageObject.objects.filter(storage_key=key).first()
        if pending is None:
            continue
        if pending.created_at > cutoff:
            continue
        try:
            default_storage.delete(key)
        except FileNotFoundError:
            pass
        pending.delete()
        removed += 1
    return removed
