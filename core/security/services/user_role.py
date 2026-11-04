from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

from core.security.models import Role, UserRole
from core.security.selectors.role import role_get
from core.security.services.check import clear_user_permission_cache
from core.users.models import User


@transaction.atomic
def user_role_assign(*, user: User, role: Role, assigned_by: User | None = None) -> UserRole:
    if role.deleted_at is not None:
        raise ValidationError({"role_id": "Cannot assign a deleted role."})
    link, _created = UserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={"assigned_by": assigned_by},
    )
    clear_user_permission_cache(user=user)
    return link


def user_role_assign_by_ids(
    *,
    user_id: UUID,
    role_id: UUID,
    assigned_by: User | None = None,
) -> UserRole:
    user = get_object_or_404(User, pk=user_id)
    role = role_get(role_id=role_id)
    return user_role_assign(user=user, role=role, assigned_by=assigned_by)


def user_role_revoke(*, user_id: UUID, role_id: UUID) -> None:
    user = get_object_or_404(User, pk=user_id)
    deleted, _ = UserRole.objects.filter(user_id=user_id, role_id=role_id).delete()
    if not deleted:
        raise ValidationError({"role_id": "Role is not assigned to this user."})
    clear_user_permission_cache(user=user)
