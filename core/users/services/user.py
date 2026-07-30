from typing import Any
from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404

from core.users.authz import authorize
from core.users.models import User

_USER_UPDATE_FIELDS = frozenset({
    "username",
    "email",
    "phone_number",
    "is_active",
    "is_staff",
    "is_admin",
    "is_superuser",
    "is_visible",
    "metadata",
})


def user_create(
    *,
    username: str,
    email: str,
    phone_number: int,
    is_active: bool = True,
    is_staff: bool = False,
    is_superuser: bool = False,
    password: str | None = None,
    must_change_password: bool = False,
) -> User:
    return User.objects.create_user(  # pyright: ignore[reportCallIssue]
        username,
        email,
        password=password,
        phone_number=phone_number,
        is_active=is_active,
        is_staff=is_staff,
        is_superuser=is_superuser,
        must_change_password=must_change_password,
    )


@transaction.atomic
def user_update(
    *,
    id: UUID,
    data: dict[str, Any],
    requesting_user: User,
) -> User:
    target = get_object_or_404(User, pk=id)
    authorize(
        user=requesting_user,
        action="users:user:update",
        resource_code="User",
        resource_identifier=str(target.id),
    )

    update_data = {**data}
    if "username" in update_data and update_data["username"] is not None:
        update_data["username"] = User.normalize_username(str(update_data["username"]))
    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = User.objects.normalize_email(str(update_data["email"]))

    for field, value in update_data.items():
        if field in _USER_UPDATE_FIELDS:
            setattr(target, field, value)

    target.full_clean()
    target.save()
    return target
