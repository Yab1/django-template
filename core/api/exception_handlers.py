from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler

from core.api.exceptions import ApplicationError

# Same envelope shape as success responses (status, result, meta, message)
ERROR_META = {"version": "v1"}

# RFC 7807 problem type identifiers (no sensitive data)
PROBLEM_TYPES = {
    400: "validation-error",
    401: "unauthorized",
    403: "forbidden",
    404: "not-found",
    409: "conflict",
    429: "throttled",
    500: "internal-server-error",
}


def _problem_details(
    *,
    request,
    status_code: int,
    detail: str,
    errors: dict | list | None = None,
) -> dict:
    """Build RFC 7807 Problem Details object. Do not expose ids or internal data in detail."""
    problem = {
        "type": PROBLEM_TYPES.get(status_code, "error"),
        "title": _title_for_status(status_code),
        "status": status_code,
        "detail": detail,
    }
    if request and getattr(request, "path", None):
        problem["instance"] = request.path
    if errors is not None:
        problem["errors"] = errors
    return problem


def _title_for_status(status_code: int) -> str:
    titles = {
        400: "Validation Error",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        409: "Conflict",
        429: "Too Many Requests",
        500: "Internal Server Error",
    }
    return titles.get(status_code, "Error")


def _error_envelope(*, message: str, result: dict | list | None = None) -> dict:
    return {
        "status": "error",
        "result": result,
        "meta": ERROR_META,
        "message": message,
    }


def _compact_errors(errors):
    """
    Recursively remove empty dicts/lists from DRF validation error payloads.

    DRF list serializers include an empty ``{}`` entry for every valid item in a
    list, making it hard to locate the actual failures.  This function prunes
    those empty entries so only items with real errors survive.

    Rules applied at each level:
    - dict  → recurse into values; drop keys whose value compacts to empty.
    - list  → compact each element; replace all-empty positions with a sparse
              dict ``{"_index": i}`` so the caller still knows *which* index
              failed, then drop trailing/leading empty entries.
    - other → return as-is.
    """
    if isinstance(errors, dict):
        result: dict = {}
        for k, v in errors.items():
            compacted = _compact_errors(v)
            if compacted:
                result[k] = compacted
        return result

    if isinstance(errors, list):
        compacted_list = []
        has_real_error = False
        for i, item in enumerate(errors):
            compacted_item = _compact_errors(item)
            if compacted_item:
                has_real_error = True
                # Preserve the original position so the caller can locate the
                # failing item by index (1-based in error messages).
                if isinstance(compacted_item, dict):
                    compacted_item = {"_index": i, **compacted_item}
                compacted_list.append(compacted_item)
        return compacted_list if has_real_error else []

    return errors


def drf_default_with_modifications_exception_handler(exc, ctx):
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, Http404):
        exc = exceptions.NotFound(detail=str(exc) if str(exc) else None)

    if isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, ctx)

    if response is None:
        return response

    request = ctx.get("request") if ctx else None
    status_code = response.status_code
    detail_payload = response.data

    if isinstance(exc, exceptions.ValidationError):
        detail_msg = "One or more fields are invalid."
        errors = _compact_errors(detail_payload if isinstance(detail_payload, dict) else detail_payload)
        problem = _problem_details(
            request=request,
            status_code=status_code,
            detail=detail_msg,
            errors=errors,
        )
        response.data = _error_envelope(message=detail_msg, result=problem)
    elif isinstance(detail_payload, dict):
        detail_msg = detail_payload.get("detail", "An error occurred.")
        if isinstance(detail_msg, (list, dict)):
            detail_msg = "An error occurred."
        problem = _problem_details(
            request=request,
            status_code=status_code,
            detail=str(detail_msg),
            errors=None,
        )
        extra_code = detail_payload.get("code")
        if extra_code and isinstance(extra_code, str):
            problem["code"] = extra_code
        response.data = _error_envelope(message=str(detail_msg), result=problem)
    elif isinstance(detail_payload, list):
        detail_msg = detail_payload[0] if detail_payload else "An error occurred."
        problem = _problem_details(
            request=request,
            status_code=status_code,
            detail=str(detail_msg),
            errors=detail_payload,
        )
        response.data = _error_envelope(message=str(detail_msg), result=problem)
    else:
        detail_msg = str(detail_payload) if detail_payload else "An error occurred."
        problem = _problem_details(
            request=request,
            status_code=status_code,
            detail=detail_msg,
            errors=None,
        )
        response.data = _error_envelope(message=detail_msg, result=problem)

    return response


def proposed_exception_handler(exc, ctx):
    """
    {
        "message": "Error message",
        "extra": {}
    }
    """
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    if isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = exception_handler(exc, ctx)

    # If unexpected error occurs (server error, etc.)
    if response is None:
        if isinstance(exc, ApplicationError):
            data = {"message": exc.message, "extra": exc.extra}
            return Response(data, status=400)

        return response

    if isinstance(exc.detail, (list, dict)):
        response.data = {"detail": response.data}

    # Type narrow: we just set response.data or exception_handler set it
    assert response.data is not None
    data = response.data

    if isinstance(exc, exceptions.ValidationError):
        data["message"] = "Validation error"
        data["extra"] = {"fields": data["detail"]}
    else:
        data["message"] = data["detail"]
        data["extra"] = {}

    del data["detail"]

    return response
