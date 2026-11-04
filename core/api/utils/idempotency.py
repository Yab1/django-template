from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any
from uuid import UUID

from django.db import IntegrityError
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from core.common.exceptions import IdempotencyConflictError
from core.common.services.idempotency import idempotency_hash, run_idempotent, run_optional_idempotent


def _json_body(data: Any) -> dict:
    return json.loads(json.dumps(data, default=str))


def _resource_id(body: dict) -> UUID | None:
    raw = body.get("id") if isinstance(body, dict) else None
    if raw in (None, ""):
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def _as_conflict(exc: BaseException) -> None:
    message = getattr(exc, "message", None)
    code = getattr(exc, "code", None)
    if not isinstance(message, str) or not isinstance(code, str):
        raise exc
    error = APIException(detail={"detail": message, "code": code})
    error.status_code = 409
    raise error from exc


def idempotent(
    *,
    operation: str,
    required: bool = True,
    map_integrity: Callable[[IntegrityError], BaseException | None] | None = None,
):
    """Replay a JSON write when the same Idempotency-Key and body arrive again.

    The replay row commits in the same transaction as the view's writes.
    File uploads do not use this decorator. Those services record the key
    themselves so a failed replay can delete the object they already stored.
    """

    def decorator(view_method: Callable) -> Callable:
        def wrapper(self, request, *args, **kwargs):
            key = request.headers.get("Idempotency-Key")
            if not required and not (key or "").strip():
                return view_method(self, request, *args, **kwargs)
            request_hash = idempotency_hash(body=request.data, url_kwargs=kwargs)
            runner = run_idempotent if required else run_optional_idempotent

            def write(slot: dict) -> None:
                response = view_method(self, request, *args, **kwargs)
                body = _json_body(response.data)
                slot["status"] = response.status_code
                slot["body"] = body
                slot["resource_id"] = _resource_id(body)

            try:
                code, body = runner(
                    user=request.user,
                    operation=operation,
                    key=key,
                    request_hash=request_hash,
                    write=write,
                )
            except IdempotencyConflictError as exc:
                _as_conflict(exc)
            except IntegrityError as exc:
                mapped = map_integrity(exc) if map_integrity is not None else None
                if mapped is None:
                    raise
                _as_conflict(mapped)
            return Response(body, status=code)

        wrapper.__name__ = view_method.__name__
        wrapper.__doc__ = view_method.__doc__
        return wrapper

    return decorator
