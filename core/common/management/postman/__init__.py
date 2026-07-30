"""Enterprise Postman collection generator package."""

from core.common.management.postman.builder import (
    build_collection,
    build_environment,
    build_manifest,
    collection_to_json,
    default_output_path,
)
from core.common.management.postman.classification import (
    _domain_folder_name,
    _resource_key_from_url_name,
    django_route_to_postman_path,
    enrich_route,
    id_variable_from_resource_key,
    normalize_resource_filter,
    request_title_from_url_name,
)
from core.common.management.postman.discovery import discover_routes, list_resources, list_routes_table
from core.common.management.postman.introspection import (
    PLACEHOLDER_BODY_OBJECT,
    _example_for_drf_field,
    _first_choice_api_value,
    _uuid_body_variable_name,
    collect_named_postman_vars,
    concept_id_fields_from_view,
    example_body_for_view_method,
    query_params_for_view,
    serializer_to_example_json,
)
from core.common.management.postman.merge import merge_collections
from core.common.management.postman.terminology import (
    TerminologyResolver,
    resolve_terminology_defaults,
    terminology_body_var_refs,
    terminology_values_for_fields,
)
from core.common.management.postman.types import (
    CATEGORY_ORDER,
    DiscoveredRoute,
    EndpointCategory,
    GenerationOptions,
    GenerationResult,
    GenerationWarning,
)

__all__ = [
    "CATEGORY_ORDER",
    "DiscoveredRoute",
    "EndpointCategory",
    "GenerationOptions",
    "GenerationResult",
    "GenerationWarning",
    "PLACEHOLDER_BODY_OBJECT",
    "_domain_folder_name",
    "_example_for_drf_field",
    "_first_choice_api_value",
    "_resource_key_from_url_name",
    "_uuid_body_variable_name",
    "build_collection",
    "build_environment",
    "build_manifest",
    "collect_named_postman_vars",
    "concept_id_fields_from_view",
    "collection_to_json",
    "default_output_path",
    "discover_routes",
    "django_route_to_postman_path",
    "enrich_route",
    "example_body_for_view_method",
    "id_variable_from_resource_key",
    "list_resources",
    "list_routes_table",
    "merge_collections",
    "normalize_resource_filter",
    "query_params_for_view",
    "request_title_from_url_name",
    "serializer_to_example_json",
    "TerminologyResolver",
    "terminology_body_var_refs",
    "resolve_terminology_defaults",
    "terminology_values_for_fields",
]
