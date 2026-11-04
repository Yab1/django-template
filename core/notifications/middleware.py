from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def _user_from_token(raw: str):
    try:
        token = AccessToken(raw)
        user_id = token.get("user_id")
        if not user_id:
            return AnonymousUser()
        return get_user_model().objects.get(pk=user_id)
    except (TokenError, get_user_model().DoesNotExist, KeyError, ValueError):
        return AnonymousUser()


class WebsocketTrailingSlashMiddleware(BaseMiddleware):
    """Channels has no APPEND_SLASH. Canonical WS routes end with ``/`` like HTTP."""

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "websocket":
            path = scope.get("path") or ""
            if path and not path.endswith("/"):
                scope = {**scope, "path": f"{path}/"}
        return await super().__call__(scope, receive, send)


class JwtAuthMiddleware(BaseMiddleware):
    """Bearer header or ``?access_token=`` query (browser WebSocket)."""

    async def __call__(self, scope, receive, send):
        token = _token_from_scope(scope)
        scope["user"] = await _user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)


def _token_from_scope(scope) -> str:
    headers = dict(scope.get("headers") or [])
    auth = headers.get(b"authorization", b"").decode()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    qs = parse_qs((scope.get("query_string") or b"").decode())
    values = qs.get("access_token") or []
    return (values[0] or "").strip()
