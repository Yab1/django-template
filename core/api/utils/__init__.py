from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from django.core.cache import cache
from rest_framework.response import Response

from core.api.utils.idempotency import idempotent
from core.api.utils.serializers import inline_serializer
from core.common.utils.cache import LIST_CACHE_TIMEOUT

_P = ParamSpec("_P")
_R = TypeVar("_R")


def cache_api_response(*, namespace: str, resource_id_kwarg: str | None = None):
    """Cache a successful read for the caller, path, and query string.

    ``invalidate_list_cache(namespace)`` drops every key in that namespace.
    The test cache ignores pattern deletes, so tests always hit the view.
    """

    def decorator(view_method: Callable[_P, _R]) -> Callable[_P, _R]:
        @wraps(view_method)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            request = args[1] if len(args) > 1 else kwargs.get("request")
            user_id = getattr(getattr(request, "user", None), "pk", None)
            resource = "" if resource_id_kwarg is None else str(kwargs.get(resource_id_kwarg, ""))
            query = request.META.get("QUERY_STRING", "") if request is not None else ""
            path = getattr(request, "path", "")
            key = f"{namespace}:{user_id}:{path}:{resource}:{query}"
            cached = cache.get(key)
            if isinstance(cached, dict) and "data" in cached and "status" in cached:
                return Response(cached["data"], status=cached["status"])
            response = view_method(*args, **kwargs)
            if isinstance(response, Response) and 200 <= response.status_code < 300:
                cache.set(
                    key,
                    {"data": response.data, "status": response.status_code},
                    timeout=LIST_CACHE_TIMEOUT,
                )
            return response

        return wrapper

    return decorator


__all__ = ["cache_api_response", "idempotent", "inline_serializer"]
