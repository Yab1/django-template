"""
Base API view with policy-based authorization wired in.

Usage:

    from core.api.views import AuthorizedAPIView

    class CodeSystemCreateApi(AuthorizedAPIView):
        authorization_resource_code = "CodeSystem"
        authorization_action = "terminology:codesystem:create"

        def post(self, request) -> Response:
            ...

Both class attributes are required for the permission check to activate.
If either is absent the view behaves like a plain ``APIView``.
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
        authorization_resource_code: str  — catalog resource code (e.g. "CodeSystem")
        authorization_action: str         — action string (e.g. "terminology:codesystem:create")

    To keep a view accessible while ``must_change_password=True`` (e.g. profile
    reads, password-change itself), set on the subclass:
        skip_must_change_password_check = True
    """

    authorization_resource_code: str | None = None
    authorization_action: str | None = None
    skip_must_change_password_check: bool = False

    permission_classes = [IsAuthenticated, MustChangePasswordPermission, PolicyPermission]
