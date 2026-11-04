from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction

from core.security.models import Permission, Role
from core.security.selectors.role import role_get
from core.security.services.permission import ensure_permissions_synced
from core.users.models import User

_ROLE_UPDATE_FIELDS = frozenset({"name", "description", "is_visible", "metadata"})


def _permissions_for_codes(*, permission_codes: list[str]) -> list[Permission]:
    ensure_permissions_synced()
    codes = [code.strip() for code in permission_codes if code and code.strip()]
    if not codes:
        return []
    rows = list(Permission.objects.filter(code__in=codes))
    found = {row.code for row in rows}
    missing = [code for code in codes if code not in found]
    if missing:
        raise ValidationError({"permission_codes": f"Unknown permission codes: {', '.join(missing)}."})
    return rows


@transaction.atomic
def role_create(
    *,
    code: str,
    name: str,
    description: str = "",
    permission_codes: list[str] | None = None,
) -> Role:
    obj = Role(code=code.strip(), name=name.strip(), description=description or "")
    obj.full_clean()
    obj.save()
    perms = _permissions_for_codes(permission_codes=permission_codes or [])
    if perms:
        obj.permissions.set(perms)
    return obj


@transaction.atomic
def role_update(*, role_id: UUID, data: dict[str, Any]) -> Role:
    obj = role_get(role_id=role_id)
    permission_codes = data.get("permission_codes")
    for field, value in data.items():
        if field in _ROLE_UPDATE_FIELDS:
            setattr(obj, field, value)
    obj.full_clean()
    obj.save()
    if permission_codes is not None:
        obj.permissions.set(_permissions_for_codes(permission_codes=permission_codes))
    return obj


def role_delete(*, role_id: UUID, requesting_user: User) -> Role:
    obj = role_get(role_id=role_id)
    obj.delete(user=requesting_user)
    return obj
