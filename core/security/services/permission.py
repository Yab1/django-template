from django.db.utils import OperationalError, ProgrammingError

from core.security.models import Permission
from core.security.registry import all_permission_specs

_SYNCED = False


def permission_sync_from_registry() -> int:
    """Upsert registered codes into ``Permission``. Does not delete rows."""
    global _SYNCED
    changed = 0
    try:
        for spec in all_permission_specs():
            obj, created = Permission.objects.get_or_create(
                code=spec.code,
                defaults={"name": spec.name, "description": spec.description},
            )
            if created:
                changed += 1
                continue
            if obj.name != spec.name or obj.description != spec.description:
                obj.name = spec.name
                obj.description = spec.description
                obj.full_clean()
                obj.save(update_fields=["name", "description", "updated_at"])
                changed += 1
    except (OperationalError, ProgrammingError):
        return 0
    _SYNCED = True
    return changed


def ensure_permissions_synced() -> None:
    if _SYNCED:
        return
    permission_sync_from_registry()
