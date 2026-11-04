"""DRF permission classes for the users app."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


def _first_held(*, user, codes: tuple[str, ...]) -> str:
    from core.security.services import user_has_permission

    for code in codes:
        if user_has_permission(user=user, action=code):
            return code
    return codes[-1]


def authorization_action_for(*, view: APIView, request: Request) -> str | None:
    mapping = getattr(view, "authorization_actions", None)
    if mapping:
        action = mapping.get(request.method)
        if action is None and request.method == "HEAD":
            action = mapping.get("GET")
        if isinstance(action, (tuple, list)):
            return _first_held(user=request.user, codes=tuple(action))
        return action
    any_of = getattr(view, "authorization_action_any", None)
    if any_of:
        return _first_held(user=request.user, codes=tuple(any_of))
    getter = getattr(view, "get_authorization_action", None)
    if callable(getter):
        return getter(request)
    return getattr(view, "authorization_action", None)


class PolicyPermission(BasePermission):
    """
    Gate tagged views on catalog permission codes.

    Views declare ``authorization_action``, ``authorization_action_any`` (first held code wins),
    or ``authorization_actions`` (method → code, or a tuple of codes).
    Untagged views pass through (authenticated-only). Superuser bypasses in the checker.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        action = authorization_action_for(view=view, request=request)
        if not action:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        from core.security.services import user_has_permission

        return user_has_permission(user=user, action=action)
