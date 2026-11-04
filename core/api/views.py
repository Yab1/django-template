"""
Base API view with policy-based authorization wired in.

Usage:

    from core.api.views import AuthorizedAPIView

    class CodeSystemCreateApi(AuthorizedAPIView):
        authorization_resource_code = "CodeSystem"
        authorization_action = "terminology:codesystem:create"

        def post(self, request) -> Response:
            ...

``authorization_action`` (or ``authorization_actions``) activates the catalog check.
If absent the view is authenticated-only.
"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.api.permissions import MustChangePasswordPermission
from core.users.permissions import PolicyPermission


class AuthorizedAPIView(APIView):
    """
    Drop-in replacement for ``APIView`` that adds ``PolicyPermission``
    to the default permission classes.

    Subclasses declare:
        authorization_resource_code: str  — optional label (docs / OpenAPI)
        authorization_action: str         — catalog permission code
        authorization_action_any: tuple   — first code the user holds wins (directory vs own)
        authorization_actions: dict       — HTTP method → code, or a tuple of codes
                                           (first code the caller holds wins)

    To keep a view accessible while ``must_change_password=True`` (e.g. profile
    reads, password-change itself), set on the subclass:
        skip_must_change_password_check = True
    """

    authorization_resource_code: str | None = None
    authorization_action: str | None = None
    authorization_action_any: tuple[str, ...] | None = None
    authorization_actions: dict[str, str | tuple[str, ...]] | None = None
    skip_must_change_password_check: bool = False

    permission_classes = [IsAuthenticated, MustChangePasswordPermission, PolicyPermission]
