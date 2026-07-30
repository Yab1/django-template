"""
Custom renderers for consistent API response shape.

EnvelopeJSONRenderer wraps successful (2xx) JSON responses in a standard envelope:
  { "status": "success", "result": <data>, "meta": { "version": "v1" }, "message": "..." }
Views keep returning Response(return_data, status=...) unchanged.
"""

from rest_framework.renderers import JSONRenderer

DEFAULT_SUCCESS_MESSAGE = "Request processed successfully"
DEFAULT_META = {"version": "v1"}


def _is_envelope(data):
    """True only if data is our API envelope (has result, meta, message, status success/error)."""
    return (
        isinstance(data, dict)
        and "result" in data
        and "meta" in data
        and "message" in data
        and data.get("status") in ("success", "error")
    )


class EnvelopeJSONRenderer(JSONRenderer):
    """
    Wraps 2xx response data in a standard envelope so the client always receives:
      { "status": "success", "result": <data>, "meta": {...}, "message": "..." }
    Does not wrap if data is already our envelope (has result, meta, message, status).
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get("response")

        if response is not None and 200 <= response.status_code < 300:
            if not _is_envelope(data):
                data = {
                    "status": "success",
                    "result": data,
                    "meta": DEFAULT_META,
                    "message": DEFAULT_SUCCESS_MESSAGE,
                }

        return super().render(data, accepted_media_type, renderer_context)
