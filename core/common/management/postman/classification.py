import re

from core.common.management.postman.types import DiscoveredRoute, EndpointCategory

_PARAM_RE = re.compile(r"<(?P<converter>[^:]+):(?P<name>[^>]+)>")

_CATEGORY_SUFFIXES: dict[EndpointCategory, tuple[str, ...]] = {
    EndpointCategory.BULK: (
        "-bulk-create",
        "-bulk-update",
        "-bulk-delete",
        "_bulk_create",
        "_bulk_update",
        "_bulk_delete",
    ),
    EndpointCategory.HISTORY: (
        "-history-previous",
        "-history-next",
        "-history-diff",
        "-history-revert",
        "-history-detail",
        "-history-list",
        "_history_previous",
        "_history_next",
        "_history_diff",
        "_history_revert",
        "_history_detail",
        "_history_list",
    ),
    EndpointCategory.AUDIT: (
        "-object-crud-audit-list",
        "-model-crud-audit-list",
        "_object_crud_audit_list",
        "_model_crud_audit_list",
    ),
    EndpointCategory.CRUD: (
        "-hard-delete",
        "-partial-update",
        "-create",
        "-list",
        "-retrieve",
        "-detail",
        "-update",
        "-delete",
        "-restore",
        "_hard_delete",
        "_partial_update",
        "_create",
        "_list",
        "_retrieve",
        "_detail",
        "_update",
        "_delete",
        "_restore",
    ),
}

_ACTION_URL_FRAGMENTS: tuple[str, ...] = (
    "-status-transition",
    "-status",
    "-finalize",
    "-cancel",
    "-merge",
    "-receive",
    "-issue",
    "-post",
    "-approve",
    "-reject",
    "-complete",
    "-assign",
    "-release",
    "-hold",
    "-void",
    "-refund",
    "-capture",
    "-evaluate",
    "-request-recollection",
)

_ALL_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        (suffix for suffixes in _CATEGORY_SUFFIXES.values() for suffix in suffixes),
        key=len,
        reverse=True,
    )
)


def _resource_key_from_url_name(url_name: str | None) -> str:
    if not url_name:
        return "misc"
    for suffix in _ALL_SUFFIXES:
        if url_name.endswith(suffix):
            return url_name[: -len(suffix)]
    for fragment in _ACTION_URL_FRAGMENTS:
        if url_name.endswith(fragment):
            return url_name[: -len(fragment)]
    return url_name


def _domain_folder_name(resource_key: str) -> str:
    if resource_key.endswith("-history"):
        resource_key = resource_key[: -len("-history")]
    return resource_key.replace("-", "_")


def _singularize_resource_segment(segment: str) -> str:
    resource = segment.replace("_", "-")
    if resource.endswith("ies"):
        return f"{resource[:-3]}y"
    if resource.endswith("ses"):
        return resource[:-2]
    if resource.endswith("s") and len(resource) > 1:
        return resource[:-1]
    return resource


def _mount_resource_folder_from_path(postman_path: str) -> str | None:
    """
    Infer collection mount resource from API path (snake_case folder name).

    Example: lab/worklists/items/... -> worklist
    """
    parts = [part for part in postman_path.strip("/").split("/") if part]
    if len(parts) < 2:
        return None

    resource_segment = parts[1]
    if resource_segment.startswith("{{") and resource_segment.endswith("}}"):
        return None
    if resource_segment in {"query", "evaluate", "context"}:
        return None

    return _domain_folder_name(_singularize_resource_segment(resource_segment))


def _resource_key_from_postman_path(postman_path: str) -> str | None:
    """
    Infer base resource from API path segments.

    Example:
    - lab/operational-specimens/{{id}}/status/ -> operational-specimen
    - billing/invoices/{{id}}/finalize/ -> invoice
    """
    mount_folder = _mount_resource_folder_from_path(postman_path)
    if mount_folder is None:
        return None
    return mount_folder.replace("_", "-")


def classify_route(
    *,
    url_name: str | None,
    view_module: str,
    postman_path: str,
) -> tuple[str, str, EndpointCategory]:
    """Return (resource_key kebab, resource_folder snake, category)."""
    module_lower = view_module.lower()
    path_lower = postman_path.lower()

    if ".apis." in module_lower:
        apis_segment = module_lower.split(".apis.", 1)[1]
        parts = apis_segment.split(".")
        if len(parts) >= 2 and parts[1] in {"evaluate", "query", "context"}:
            capability = parts[0].replace("_", "-")
            return capability, parts[0], EndpointCategory.CAPABILITY
        if "billing_gate" in module_lower or "billing-gates" in path_lower:
            return "billing-gate", "billing_gate", EndpointCategory.CAPABILITY
        if "accounting" in module_lower and "context" in module_lower:
            return "accounting-context", "accounting_context", EndpointCategory.CAPABILITY

    category = EndpointCategory.MISC
    if url_name:
        for cat, suffixes in _CATEGORY_SUFFIXES.items():
            if any(url_name.endswith(suffix) for suffix in suffixes):
                category = cat
                break
        if category is EndpointCategory.MISC:
            if any(url_name.endswith(fragment) for fragment in _ACTION_URL_FRAGMENTS):
                category = EndpointCategory.ACTION
            elif "/action." in module_lower or ".action" in module_lower:
                category = EndpointCategory.ACTION
            elif ".bulk." in module_lower:
                category = EndpointCategory.BULK
            elif ".history." in module_lower:
                category = EndpointCategory.HISTORY
            elif ".audit." in module_lower:
                category = EndpointCategory.AUDIT
            elif ".crud." in module_lower:
                category = EndpointCategory.CRUD

    resource_key = _resource_key_from_url_name(url_name)
    inferred_resource = _resource_key_from_postman_path(postman_path)
    if inferred_resource and (
        resource_key == (url_name or "") or category in {EndpointCategory.ACTION, EndpointCategory.MISC}
    ):
        resource_key = inferred_resource
    if category is EndpointCategory.CAPABILITY and resource_key == url_name:
        segment = postman_path.strip("/").split("/")
        if len(segment) >= 2:
            resource_key = segment[-2].replace("_", "-")
            if resource_key.endswith("s"):
                resource_key = resource_key[:-1]
    resource_folder = _domain_folder_name(resource_key)
    return resource_key, resource_folder, category


def enrich_route(route: DiscoveredRoute) -> DiscoveredRoute:
    view_module = route.view_module
    if not view_module and route.view_class is not None:
        view_module = route.view_class.__module__
    resource_key, resource_folder, category = classify_route(
        url_name=route.url_name,
        view_module=view_module,
        postman_path=route.postman_path,
    )
    route.view_module = view_module
    route.resource_key = resource_key
    route.resource_folder = resource_folder
    route.category = category
    return route


def request_title_from_url_name(
    url_name: str | None,
    *,
    method: str,
    resource_key: str = "",
) -> str:
    resource_prefix = resource_key.replace("-", " ").replace("_", " ").strip()

    def _with_resource(action: str) -> str:
        return f"{resource_prefix} {action}" if resource_prefix else action

    if not url_name:
        return _with_resource("request")
    for suffix in _ALL_SUFFIXES:
        if url_name.endswith(suffix):
            action = suffix.lstrip("-_").replace("-", " ").replace("_", " ")
            if suffix.endswith(("-detail", "_detail")):
                return _with_resource("retrieve")
            if suffix.endswith(("-partial-update", "_partial_update")):
                return _with_resource("partial update")
            if suffix.endswith(("-hard-delete", "_hard_delete")):
                return _with_resource("hard delete")
            if suffix.endswith(("-bulk-create", "_bulk_create")):
                return _with_resource("bulk create")
            if suffix.endswith(("-bulk-update", "_bulk_update")):
                return _with_resource("bulk update")
            if suffix.endswith(("-bulk-delete", "_bulk_delete")):
                return _with_resource("bulk delete")
            if suffix.endswith(("-model-crud-audit-list", "_model_crud_audit_list")):
                return _with_resource("model audit list")
            if suffix.endswith(("-object-crud-audit-list", "_object_crud_audit_list")):
                return _with_resource("object audit list")
            if "history" in suffix:
                return _with_resource(action)
            return _with_resource(action.split()[0] if action else "request")
    for fragment in _ACTION_URL_FRAGMENTS:
        if url_name.endswith(fragment):
            return _with_resource(fragment.lstrip("-").replace("-", " "))
    title = url_name.replace("-", " ").replace("_", " ").lower()
    if method.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
        return _with_resource(f"{title} ({method.lower()})")
    return _with_resource(title)


def map_path_param_names(url_name: str | None, django_names: list[str]) -> list[str]:
    if not url_name:
        return list(django_names)
    resource_key = _resource_key_from_url_name(url_name)
    base_key = resource_key[: -len("-history")] if resource_key.endswith("-history") else resource_key
    base_snake = base_key.replace("-", "_")
    mapped: list[str] = []
    for name in django_names:
        if name in ("id", "pk"):
            mapped.append(f"{base_snake}_id")
        elif name == "history_id":
            mapped.append(f"{base_snake}_history_id")
        else:
            mapped.append(name)
    return mapped


def django_route_to_postman_path(route: str, url_name: str | None) -> tuple[str, list[str]]:
    matches = list(_PARAM_RE.finditer(route))
    django_names = [m.group("name") for m in matches]
    mapped_names = map_path_param_names(url_name, django_names)
    parts: list[str] = []
    last_end = 0
    for match, new_name in zip(matches, mapped_names, strict=True):
        parts.append(route[last_end : match.start()])
        parts.append(f"{{{{{new_name}}}}}")
        last_end = match.end()
    parts.append(route[last_end:])
    return "".join(parts), mapped_names


def id_variable_from_resource_key(resource_key: str) -> str:
    return f"{resource_key.replace('-', '_')}_id"


def resource_prefix(resource_key: str) -> str:
    return _domain_folder_name(resource_key)


def normalize_resource_filter(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def route_matches_resource_filter(route: DiscoveredRoute, filter_snake: str) -> bool:
    """
    Match a CLI ``--resource`` filter to discovered routes.

    ``worklist`` must include ``worklist-item-*`` CRUD (folder ``worklist_item``)
    and action routes grouped under path mount ``lab/worklists/``.
    """
    if route.resource_folder == filter_snake:
        return True
    if route.resource_folder.startswith(f"{filter_snake}_"):
        return True

    filter_kebab = filter_snake.replace("_", "-")
    if route.resource_key == filter_kebab:
        return True
    if route.resource_key.startswith(f"{filter_kebab}-"):
        return True

    mount_folder = _mount_resource_folder_from_path(route.postman_path)
    return mount_folder == filter_snake
