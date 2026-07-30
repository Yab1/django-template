"""Assemble Postman collection documents from discovered routes."""

import json
import uuid
from typing import Any

from core.common.management.postman.classification import (
    id_variable_from_resource_key,
    normalize_resource_filter,
    request_title_from_url_name,
    route_matches_resource_filter,
)
from core.common.management.postman.introspection import (
    auth_token_variable,
    collect_named_postman_vars,
    concept_id_fields_from_view,
    example_body_for_view_method,
    query_params_for_view,
)
from core.common.management.postman.responses import build_saved_responses, build_test_script
from core.common.management.postman.terminology import TerminologyResolver
from core.common.management.postman.types import (
    CATEGORY_ORDER,
    DiscoveredRoute,
    EndpointCategory,
    GenerationOptions,
    GenerationResult,
    GenerationWarning,
)


def _default_variables(
    extra_param_names: set[str],
    terminology_defaults: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    vars_: list[dict[str, Any]] = [
        {"key": "base_url", "value": "http://localhost:6000/api/v1", "type": "string"},
        {"key": "user_access_token", "value": "", "type": "string"},
        {"key": "admin_access_token", "value": "", "type": "string"},
    ]
    seen = {item["key"] for item in vars_}
    for name in sorted(extra_param_names):
        if name in seen:
            continue
        entry: dict[str, Any] = {
            "key": name,
            "value": "",
            "type": "string",
            "description": f"Path parameter `{name}`",
        }
        if name in terminology_defaults:
            entry["value"] = terminology_defaults[name]["value"]
            entry["description"] = terminology_defaults[name]["description"]
        vars_.append(entry)
        seen.add(name)
    return vars_


def _bearer_auth(token_var: str) -> dict[str, Any]:
    return {
        "type": "bearer",
        "bearer": [{"key": "token", "value": f"{{{{{token_var}}}}}", "type": "string"}],
    }


def _path_segments(postman_path: str) -> list[str]:
    stripped = postman_path.strip("/")
    if not stripped:
        return [""]
    parts = stripped.split("/")
    return parts + [""]


def _build_request_item(
    *,
    title: str,
    method: str,
    postman_path: str,
    description: str,
    include_json_body: bool,
    query: list[dict[str, Any]] | None = None,
    post_create_id_var: str | None = None,
    json_body: dict[str, Any] | None = None,
    token_var: str = "user_access_token",
    skip_scripts: bool = False,
    url_name: str | None = None,
) -> dict[str, Any]:
    segments = _path_segments(postman_path)
    path_for_raw = "/".join(part for part in segments[:-1]) + "/"
    raw = f"{{{{base_url}}}}/{path_for_raw}"
    if query:
        query_string = "&".join(f"{row['key']}={row.get('value', '')}" for row in query if not row.get("disabled"))
        if query_string:
            raw = raw.rstrip("/") + "/?" + query_string

    item: dict[str, Any] = {
        "name": title,
        "request": {
            "auth": _bearer_auth(token_var),
            "method": method.upper(),
            "header": [],
            "url": {
                "raw": raw,
                "host": ["{{base_url}}"],
                "path": segments,
            },
            "description": description,
        },
        "_postman_meta": {"url_name": url_name, "method": method.upper()},
    }
    if query:
        item["request"]["url"]["query"] = query
    if method.upper() in ("POST", "PUT", "PATCH", "DELETE") and include_json_body and json_body is not None:
        body = json.dumps(json_body, indent=2)
        item["request"]["header"] = [
            {"key": "Content-Type", "value": "application/json", "type": "text"},
        ]
        item["request"]["body"] = {
            "mode": "raw",
            "raw": body,
            "options": {"raw": {"language": "json"}},
        }

    events: list[dict[str, Any]] = []
    if method.upper() == "POST" and post_create_id_var and not skip_scripts:
        events.append({
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "if (pm.response.code === 201) {",
                    "    const parsed = pm.response.json();",
                    "    const id = parsed.result?.id ?? parsed.id;",
                    "    if (id) {",
                    f'        pm.collectionVariables.set("{post_create_id_var}", id);',
                    f'        pm.environment.set("{post_create_id_var}", id);',
                    "    }",
                    "}",
                ],
            },
        })
    if not skip_scripts:
        events.append({
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": build_test_script(expect_envelope=method.upper() != "DELETE"),
            },
        })
    if events:
        item["event"] = events
    return item


def _filter_routes(routes: list[DiscoveredRoute], options: GenerationOptions) -> list[DiscoveredRoute]:
    filtered: list[DiscoveredRoute] = []
    resource_filters = None
    if options.resources:
        resource_filters = {normalize_resource_filter(value) for value in options.resources}

    category_filters = None
    if options.categories:
        category_filters = {value.strip().lower() for value in options.categories}

    exclude = set()
    if options.exclude_categories:
        exclude = {value.strip().lower() for value in options.exclude_categories}

    for route in routes:
        if resource_filters and not any(
            route_matches_resource_filter(route, resource_name) for resource_name in resource_filters
        ):
            continue
        category_value = route.category.value
        if category_filters and category_value not in category_filters:
            continue
        if category_value in exclude:
            continue
        filtered.append(route)
    return filtered


def _category_sort_key(category: EndpointCategory) -> int:
    try:
        return CATEGORY_ORDER.index(category)
    except ValueError:
        return len(CATEGORY_ORDER)


def _build_nested_folders(
    grouped: dict[str, dict[EndpointCategory, list[dict[str, Any]]]],
    *,
    include_resource_level: bool,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for resource_name in sorted(grouped):
        category_map = grouped[resource_name]
        category_folders: list[dict[str, Any]] = []
        for category in sorted(category_map, key=_category_sort_key):
            requests = category_map[category]
            requests.sort(key=lambda row: (row["request"]["url"]["raw"], row["request"]["method"]))
            category_folders.append({"name": category.value, "item": requests})
        if include_resource_level:
            items.append({"name": resource_name, "item": category_folders})
        else:
            items.extend(category_folders)
    return items


def build_collection(
    *,
    routes: list[DiscoveredRoute],
    options: GenerationOptions,
) -> GenerationResult:
    warnings: list[GenerationWarning] = []
    filtered = _filter_routes(routes, options)
    if not filtered:
        warnings.append(GenerationWarning(message="No routes matched the selected filters."))

    param_names: set[str] = set()
    create_id_vars: set[str] = set()
    terminology_field_names: set[str] = set()
    grouped: dict[str, dict[EndpointCategory, list[dict[str, Any]]]] = {}

    single_resource = bool(options.resources and len(options.resources) == 1)
    include_resource_level = not (single_resource or options.per_resource_file)

    resolver: TerminologyResolver | None = None
    if not options.skip_terminology:
        resolver = TerminologyResolver.for_app(options.app_label)

    from core.common.management.postman.model_fields import (
        filter_path_param_names,
        filter_terminology_concept_fields,
    )

    resource_concept_fields: dict[str, set[str]] = {}
    for route in filtered:
        bucket = resource_concept_fields.setdefault(route.resource_folder, set())
        path_candidates = filter_terminology_concept_fields(
            set(filter_path_param_names(route.path_param_names)),
            app_label=options.app_label,
            resource_folder=route.resource_folder,
        )
        bucket.update(path_candidates)
        if route.view_class is not None:
            bucket.update(
                concept_id_fields_from_view(
                    route.view_class,
                    app_label=options.app_label,
                    resource_folder=route.resource_folder,
                )
            )

    resource_unbound: dict[str, set[str]] = {}

    for route in filtered:
        token_var = auth_token_variable(route.view_class)
        if options.auth_default == "admin":
            token_var = "admin_access_token"

        concept_fields = resource_concept_fields.get(route.resource_folder, set())
        term_body_vars: dict[str, str] = {}
        term_response_values: dict[str, str] = {}
        if resolver is not None:
            term_body_vars = resolver.body_var_refs(concept_fields, resource_folder=route.resource_folder)
            term_response_values = resolver.response_fixture_values(
                concept_fields,
                resource_folder=route.resource_folder,
            )
            unbound = resolver.unbound_concept_id_fields(concept_fields, resource_folder=route.resource_folder)
            resource_unbound.setdefault(route.resource_folder, set()).update(unbound)

        title_base = request_title_from_url_name(
            route.url_name, method=route.methods[0], resource_key=route.resource_key
        )
        effective_methods = [method for method in route.methods if method not in ("HEAD", "OPTIONS")]

        for method in effective_methods:
            title = title_base
            if len(effective_methods) > 1:
                title = request_title_from_url_name(route.url_name, method=method, resource_key=route.resource_key)

            desc_parts = [
                f"Generated from Django route `{route.url_name or 'unnamed'}` ({method}).",
                f"Category: `{route.category.value}`. Resource: `{route.resource_folder}`.",
                f"Path (under base_url): `{route.postman_path}`.",
            ]
            if route.view_class is not None:
                action = getattr(route.view_class, "authorization_action", None)
                if action:
                    desc_parts.append(f"Authorization action: `{action}`.")

            json_body: dict[str, Any] | None = None
            if method in ("POST", "PUT", "PATCH", "DELETE"):
                skip_body = method == "POST" and route.postman_path.rstrip("/").endswith("restore")
                if not skip_body:
                    json_body = example_body_for_view_method(
                        route.view_class,
                        method,
                        resource_key=route.resource_key,
                        terminology_body_vars=term_body_vars,
                    )
            include_body = json_body is not None
            if json_body is not None:
                param_names.update(collect_named_postman_vars(json_body))
                terminology_field_names.update(json_body.keys())
                desc_parts.extend([
                    "",
                    "Example JSON body is derived from the view's input serializer.",
                ])
            elif method in ("POST", "PUT", "PATCH", "DELETE") and not (
                method == "POST" and route.postman_path.rstrip("/").endswith("restore")
            ):
                desc_parts.extend([
                    "",
                    "No request body (view defines no InputSerializer for this method).",
                ])

            post_create_id_var = None
            if (
                method == "POST"
                and route.url_name
                and (route.url_name.endswith("-create") or route.url_name.endswith("_create"))
            ):
                post_create_id_var = id_variable_from_resource_key(route.resource_key)
                create_id_vars.add(post_create_id_var)

            query = query_params_for_view(route.view_class)
            if query is None and method == "GET" and route.url_name and route.url_name.endswith("-list"):
                query = [
                    {"key": "limit", "value": "10", "description": "Page size"},
                    {"key": "offset", "value": "0", "description": "Offset"},
                ]

            request_item = _build_request_item(
                title=title,
                method=method,
                postman_path=route.postman_path,
                description="\n".join(desc_parts),
                include_json_body=include_body,
                query=query,
                post_create_id_var=post_create_id_var,
                json_body=json_body,
                token_var=token_var,
                skip_scripts=options.skip_scripts,
                url_name=route.url_name,
            )

            if not options.skip_responses:
                request_item["response"] = build_saved_responses(
                    view_class=route.view_class,
                    method=method,
                    resource_key=route.resource_key,
                    url_name=route.url_name,
                    postman_path=route.postman_path,
                    request_item=request_item,
                    terminology_values=term_response_values,
                )
            elif route.view_class is None:
                warnings.append(
                    GenerationWarning(
                        message="Missing view class; skipped response example generation.",
                        url_name=route.url_name,
                    )
                )

            param_names.update(route.path_param_names)
            grouped.setdefault(route.resource_folder, {}).setdefault(route.category, []).append(request_item)

    for resource_folder, unbound_fields in sorted(resource_unbound.items()):
        for field_name in sorted(unbound_fields):
            warnings.append(
                GenerationWarning(
                    message=(
                        f"[{resource_folder}] No fixture Concept found for `{field_name}` "
                        f"(check constants + core/terminology/fixtures)."
                    ),
                )
            )

    param_names.update(create_id_vars)
    terminology_defaults: dict[str, dict[str, str]] = {}
    if resolver is not None:
        for resource_folder, field_names in resource_concept_fields.items():
            terminology_defaults.update(
                resolver.collection_defaults(
                    field_names | terminology_field_names,
                    resource_folder=resource_folder,
                )
            )

    collection_name = options.collection_name
    if options.pr_prefix:
        collection_name = f"PR-{options.pr_prefix} - {collection_name}"

    postman_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"{options.app_label}:{collection_name}").hex[:24]
    if not options.stable_id:
        postman_id = uuid.uuid4().hex[:24]

    collection: dict[str, Any] = {
        "info": {
            "_postman_id": postman_id,
            "name": collection_name,
            "description": (
                f"Auto-generated collection for Django app `{options.app_label}`. "
                "Uses bearer auth via collection variables. "
                "Request bodies and saved examples are derived from DRF serializers when available. "
                "Load terminology fixtures before calling endpoints that reference Concept IDs."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": _default_variables(param_names, terminology_defaults),
        "item": _build_nested_folders(grouped, include_resource_level=include_resource_level),
    }

    request_count = sum(len(requests) for category_map in grouped.values() for requests in category_map.values())

    environment = None
    if options.generate_environment:
        environment = build_environment(collection["variable"], name=f"{options.app_label} local")

    return GenerationResult(
        collection=collection,
        request_count=request_count,
        warnings=warnings,
        environment=environment,
    )


def build_environment(variables: list[dict[str, Any]], *, name: str) -> dict[str, Any]:
    return {
        "id": uuid.uuid4().hex[:24],
        "name": name,
        "values": [
            {
                "key": item["key"],
                "value": item.get("value", ""),
                "type": "default",
                "enabled": True,
            }
            for item in variables
            if "key" in item
        ],
        "_postman_variable_scope": "environment",
    }


def build_manifest(
    *,
    app_label: str,
    outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "app_label": app_label,
        "collections": outputs,
    }


def collection_to_json(collection: dict[str, Any]) -> str:
    return json.dumps(collection, indent=2) + "\n"


def default_output_path(
    *,
    app_label: str,
    resource: str | None = None,
) -> str:
    if resource:
        resource_snake = normalize_resource_filter(resource)
        return f"postman/{app_label}/{resource_snake}_viewset.postman_collection.json"
    return f"postman/{app_label}/{app_label}_api.postman_collection.json"
