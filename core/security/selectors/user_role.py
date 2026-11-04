from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from core.security.models import UserRole
from core.users.models import User


def user_role_list(*, user_id: UUID) -> QuerySet[UserRole]:
    get_object_or_404(User, pk=user_id)
    return (
        UserRole.objects.filter(user_id=user_id, role__deleted_at__isnull=True)
        .select_related("role")
        .prefetch_related("role__permissions")
        .order_by("role__code")
    )
