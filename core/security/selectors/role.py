from uuid import UUID

from django.db.models import QuerySet
from django.http import Http404

from core.security.filters import RoleFilter
from core.security.models import Role

_LIST_FILTER_KEYS = frozenset({"code", "name", "is_visible", "order_by"})


def role_get(*, role_id: UUID) -> Role:
    try:
        return Role.objects.filter(deleted_at__isnull=True).prefetch_related("permissions").get(pk=role_id)
    except Role.DoesNotExist as exc:
        raise Http404("Role not found.") from exc


def role_list(*, filters: dict | None = None) -> QuerySet[Role]:
    raw = dict(filters or {})
    cleaned = {key: value for key, value in raw.items() if key in _LIST_FILTER_KEYS and value not in (None, "")}
    qs = Role.objects.filter(deleted_at__isnull=True).prefetch_related("permissions")
    return RoleFilter(cleaned, qs).qs
