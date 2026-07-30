"""
DRF permission classes for cross-cutting API access controls.
"""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class MustChangePasswordPermission(BasePermission):
    """
    Blocks all authorized API endpoints for users who have ``must_change_password=True``.

    Set automatically when an account is provisioned with a temporary
    password. Cleared by ``_apply_password_change`` once the user sets a permanent
    password — either via the token-based reset email link
    (POST /api/v1/authentication/password-reset/confirm/) or the authenticated
    change-password endpoint (POST /api/v1/authentication/me/password/).

    Views that must remain accessible during forced-reset state (e.g. ``MeApi``,
    ``CurrentUserPasswordChangeApi``) should set:
        skip_must_change_password_check = True

    The 403 response carries ``"code": "password_reset_required"`` so the frontend
    can reliably detect this state and redirect to the set-password page without
    inspecting the human-readable message.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not request.user or not request.user.is_authenticated:
            return True

        if getattr(view, "skip_must_change_password_check", False):
            return True

        if getattr(request.user, "must_change_password", False):
            raise PermissionDenied(
                detail={
                    "detail": "You must set a new password before accessing this resource.",
                    "code": "password_reset_required",
                }
            )

        return True
