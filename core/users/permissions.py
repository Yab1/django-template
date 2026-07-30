"""DRF permission classes for the users app."""

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class PolicyPermission(BasePermission):
    """
    Gate policy-tagged views to staff/superuser until ``core.security`` is available.

    Views without ``authorization_resource_code`` / ``authorization_action`` pass through.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not getattr(view, "authorization_resource_code", None):
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
