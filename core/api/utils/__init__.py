from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from core.api.utils.serializers import inline_serializer

_P = ParamSpec("_P")
_R = TypeVar("_R")


def run_service(
    service: Callable[_P, _R],
    validated_data: dict[str, Any],
    *args: _P.args,
    **kwargs: _P.kwargs,
) -> _R:
    """Call a service with validated serializer data merged into kwargs."""
    as_key = kwargs.pop("_as", None)
    if as_key:
        kwargs[str(as_key)] = validated_data
    else:
        kwargs.update(validated_data)
    return service(*args, **kwargs)


def cache_api_response(*, namespace: str):
    """No-op cache decorator until Redis list-cache helpers are wired in."""

    def decorator(view_method: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(view_method)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            return view_method(*args, **kwargs)

        return wrapper

    _ = namespace
    return decorator


__all__ = ["cache_api_response", "inline_serializer", "run_service"]
