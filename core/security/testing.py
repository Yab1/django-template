"""Test helpers. Do not import from product APIs."""

from __future__ import annotations

import uuid
from collections.abc import Iterable

from core.security.services import permission_sync_from_registry, role_create, user_role_assign
from core.users.models import User


def grant_permissions(*, user: User, codes: Iterable[str]) -> None:
    """Give ``user`` a throwaway role that holds the given catalog codes."""
    permission_sync_from_registry()
    role = role_create(
        code=f"grant_{user.username}_{uuid.uuid4().hex[:8]}",
        name="test grant",
        permission_codes=list(codes),
    )
    user_role_assign(user=user, role=role)
