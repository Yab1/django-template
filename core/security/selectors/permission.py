from uuid import UUID

from django.db.models import QuerySet
from django.http import Http404

from core.security.filters import PermissionFilter
from core.security.models import Permission
from core.security.services.permission import ensure_permissions_synced

_LIST_FILTER_KEYS = frozenset({"code", "name", "order_by"})


def permission_get(*, permission_id: UUID) -> Permission:
    ensure_permissions_synced()
    try:
        return Permission.objects.get(pk=permission_id)
    except Permission.DoesNotExist as exc:
        raise Http404("Permission not found.") from exc


def permission_list(*, filters: dict | None = None) -> QuerySet[Permission]:
    ensure_permissions_synced()
    raw = dict(filters or {})
    cleaned = {key: value for key, value in raw.items() if key in _LIST_FILTER_KEYS and value not in (None, "")}
    return PermissionFilter(cleaned, Permission.objects.all()).qs
