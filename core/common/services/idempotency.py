from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from core.common.exceptions import IdempotencyConflictError
from core.common.models.idempotency import IdempotencyRecord
from core.users.models import User


def canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: freeze(item) for key, item in value.items()}
    if isinstance(value, list):
        return [freeze(item) for item in value]
    if isinstance(value, tuple):
        return [freeze(item) for item in value]
    if isinstance(value, User):
        return str(value.pk)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def idempotency_hash(*, body: Any, url_kwargs: dict[str, Any]) -> str:
    payload = body
    if hasattr(body, "lists"):
        payload = {key: values if len(values) > 1 else values[0] for key, values in body.lists()}
    return canonical_hash({
        "body": freeze(payload),
        "kwargs": {key: str(item) for key, item in url_kwargs.items()},
    })


def require_idempotency_key(key: str | None) -> str:
    cleaned = (key or "").strip()
    if not cleaned:
        raise ValidationError({"Idempotency-Key": "This header is required."})
    if len(cleaned) > 128:
        raise ValidationError({"Idempotency-Key": "Must be at most 128 characters."})
    return cleaned


def idempotency_lookup(*, user: User, operation: str, key: str) -> IdempotencyRecord | None:
    return IdempotencyRecord.objects.filter(user=user, operation=operation, key=key).first()


def assert_same_request(row: IdempotencyRecord, request_hash: str) -> None:
    if row.request_hash != request_hash:
        raise IdempotencyConflictError(
            "Idempotency key was already used with a different request.",
            "idempotency_key_reused",
        )


def record_idempotency(
    *,
    user: User,
    operation: str,
    key: str,
    request_hash: str,
    status: int,
    body: dict,
    resource_id: UUID | None,
) -> IdempotencyRecord:
    return IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        key=key,
        request_hash=request_hash,
        response_status=status,
        response_body=body,
        resource_id=resource_id,
        state=IdempotencyRecord.State.COMPLETED,
    )


def _replay_or_raise(exc: IntegrityError, *, user: User, operation: str, key: str, request_hash: str):
    existing = idempotency_lookup(user=user, operation=operation, key=key)
    if existing is None:
        raise exc
    assert_same_request(existing, request_hash)
    return existing.response_status, existing.response_body


def run_idempotent(
    *,
    user: User,
    operation: str,
    key: str | None,
    request_hash: str,
    write: Callable[[dict[str, Any]], None],
) -> tuple[int, dict]:
    """Insert the completed replay row in the same transaction as the business write."""
    cleaned = require_idempotency_key(key)
    try:
        with transaction.atomic():
            existing = idempotency_lookup(user=user, operation=operation, key=cleaned)
            if existing is not None:
                assert_same_request(existing, request_hash)
                return existing.response_status, existing.response_body
            slot: dict[str, Any] = {}
            write(slot)
            record_idempotency(
                user=user,
                operation=operation,
                key=cleaned,
                request_hash=request_hash,
                status=slot["status"],
                body=slot["body"],
                resource_id=slot.get("resource_id"),
            )
            return slot["status"], slot["body"]
    except IntegrityError as exc:
        return _replay_or_raise(exc, user=user, operation=operation, key=cleaned, request_hash=request_hash)


def run_optional_idempotent(
    *,
    user: User,
    operation: str,
    key: str | None,
    request_hash: str,
    write: Callable[[dict[str, Any]], None],
) -> tuple[int, dict]:
    if not (key or "").strip():
        slot: dict[str, Any] = {}
        with transaction.atomic():
            write(slot)
        return slot["status"], slot["body"]
    return run_idempotent(
        user=user,
        operation=operation,
        key=key,
        request_hash=request_hash,
        write=write,
    )
