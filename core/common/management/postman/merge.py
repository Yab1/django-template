"""Merge generated Postman collections with existing files."""

from typing import Any


def _request_key(item: dict[str, Any]) -> str | None:
    request = item.get("request")
    if not request:
        return None
    method = request.get("method", "GET")
    url = request.get("url", {})
    raw = url.get("raw") or ""
    meta = item.get("_postman_meta", {})
    url_name = meta.get("url_name")
    if url_name:
        return f"{url_name}:{method}"
    return f"{raw}:{method}"


def _flatten_items(items: list[dict[str, Any]], prefix: str = "") -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for item in items:
        if "item" in item:
            folder_name = item.get("name", "")
            mapping.update(_flatten_items(item["item"], prefix=f"{prefix}/{folder_name}"))
            continue
        key = _request_key(item)
        if key:
            mapping[key] = item
    return mapping


def _merge_responses(existing: dict[str, Any], generated: dict[str, Any], *, refresh_responses: bool) -> None:
    if refresh_responses:
        if "response" in generated:
            existing["response"] = generated["response"]
        return
    if "response" not in existing and "response" in generated:
        existing["response"] = generated["response"]


def _merge_request(existing: dict[str, Any], generated: dict[str, Any], *, refresh_responses: bool) -> None:
    existing["request"] = generated["request"]
    if generated.get("description"):
        existing["description"] = generated.get("description")
    if "event" in generated:
        existing["event"] = generated["event"]
    _merge_responses(existing, generated, refresh_responses=refresh_responses)
    if generated.get("_postman_meta"):
        existing["_postman_meta"] = generated["_postman_meta"]


def merge_collections(
    existing: dict[str, Any],
    generated: dict[str, Any],
    *,
    refresh_responses: bool = False,
    only_missing: bool = False,
) -> dict[str, Any]:
    if not only_missing and not refresh_responses:
        return generated

    existing_map = _flatten_items(existing.get("item", []))
    generated_map = _flatten_items(generated.get("item", []))

    for key, generated_item in generated_map.items():
        if key not in existing_map:
            continue
        if only_missing:
            continue
        _merge_request(existing_map[key], generated_item, refresh_responses=refresh_responses)

    if only_missing:
        for key, generated_item in generated_map.items():
            if key in existing_map:
                continue
            existing_map[key] = generated_item

    if only_missing:
        merged = generated
        merged_items = _flatten_items(merged.get("item", []))
        for key, item in existing_map.items():
            if key not in merged_items:
                merged_items[key] = item
        merged["item"] = _rebuild_tree_from_flat(merged_items, generated.get("item", []))
        merged["variable"] = _merge_variables(existing.get("variable", []), generated.get("variable", []))
        return merged

    existing["variable"] = _merge_variables(existing.get("variable", []), generated.get("variable", []))
    return existing


def _merge_variables(existing: list[dict[str, Any]], generated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {item["key"]: item for item in existing if "key" in item}
    for item in generated:
        key = item.get("key")
        if not key:
            continue
        if key not in by_key:
            by_key[key] = item
            continue
        current = by_key[key]
        if not current.get("value") and item.get("value"):
            current["value"] = item["value"]
        if item.get("description") and not current.get("description"):
            current["description"] = item["description"]
    return sorted(by_key.values(), key=lambda row: row["key"])


def _rebuild_tree_from_flat(
    flat: dict[str, dict[str, Any]], template_tree: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Preserve generated folder structure; append only-missing requests to matching folders when possible."""
    tree = template_tree
    existing_keys = _flatten_items(tree)
    for key, item in flat.items():
        if key in existing_keys:
            continue
        tree.append(item)
    return tree
