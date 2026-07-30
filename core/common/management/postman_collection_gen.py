"""
Build Postman Collection v2.1 JSON from Django URL patterns.

Backward-compatible facade over ``core.common.management.postman``.
"""

from core.common.management.postman import (
    DiscoveredRoute,
    GenerationOptions,
    collection_to_json,
    discover_routes,
    example_body_for_view_method,
    serializer_to_example_json,
)
from core.common.management.postman import (
    build_collection as _build_collection,
)
from core.common.management.postman.classification import (
    _domain_folder_name,
    _resource_key_from_url_name,
)
from core.common.management.postman.introspection import (
    _example_for_drf_field,
    _first_choice_api_value,
    _uuid_body_variable_name,
)


def build_collection(
    *,
    app_label: str,
    collection_name: str,
    routes: list[DiscoveredRoute],
    **kwargs,
) -> dict:
    """Backward-compatible wrapper returning only the collection document."""
    options = GenerationOptions(
        app_label=app_label,
        collection_name=collection_name,
        **kwargs,
    )
    return _build_collection(routes=routes, options=options).collection


__all__ = [
    "DiscoveredRoute",
    "PLACEHOLDER_BODY_OBJECT",
    "_domain_folder_name",
    "_example_for_drf_field",
    "_first_choice_api_value",
    "_resource_key_from_url_name",
    "_uuid_body_variable_name",
    "build_collection",
    "collection_to_json",
    "discover_routes",
    "example_body_for_view_method",
    "serializer_to_example_json",
]

PLACEHOLDER_BODY_OBJECT = __import__(
    "core.common.management.postman.introspection",
    fromlist=["PLACEHOLDER_BODY_OBJECT"],
).PLACEHOLDER_BODY_OBJECT
