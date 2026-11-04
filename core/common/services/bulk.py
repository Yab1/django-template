from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

from django.core.exceptions import ValidationError
from django.db import transaction

_T = TypeVar("_T")


@transaction.atomic
def bulk_run_via_service(
    *,
    items: Sequence[Mapping[str, Any]],
    run_one: Callable[..., _T],
    shared_kwargs: Mapping[str, Any] | None = None,
) -> list[_T]:
    """
    Run ``run_one(**item, **shared_kwargs)`` for each item in one transaction.

    Collects per-item ``ValidationError`` messages and re-raises a single
    ``ValidationError`` keyed by item index if any fail (entire batch rolls back).
    """
    shared = dict(shared_kwargs or {})
    results: list[_T] = []
    errors: dict[str, Any] = {}

    for index, item in enumerate(items):
        try:
            results.append(run_one(**dict(item), **shared))
        except ValidationError as exc:
            if getattr(exc, "error_dict", None) is not None:
                for field, err_list in exc.error_dict.items():
                    errors[f"{index}.{field}"] = [str(err) for err in err_list]
            else:
                errors[str(index)] = [str(message) for message in exc.messages]

    if errors:
        # Django ValidationError dict values must be message lists (not nested dicts).
        raise ValidationError(errors)

    return results
