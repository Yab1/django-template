"""Discover Django URL routes for Postman generation."""

import importlib
import types
from typing import Any, Callable

from django.urls import URLPattern, URLResolver

from core.common.management.postman.classification import (
    django_route_to_postman_path,
    enrich_route,
)
from core.common.management.postman.types import DiscoveredRoute


def _api_segment_for_app(app_label: str) -> str:
    import core.api.urls as api_urls

    expected_mod = f"core.{app_label}.urls"
    for pattern in api_urls.urlpatterns:
        if not isinstance(pattern, URLResolver):
            continue
        urlconf = pattern.urlconf_name
        if isinstance(urlconf, tuple):
            mod_name = urlconf[0] if isinstance(urlconf[0], str) else getattr(urlconf[0], "__name__", "")
        elif isinstance(urlconf, types.ModuleType):
            mod_name = urlconf.__name__
        else:
            mod_name = str(urlconf)
        if mod_name == expected_mod:
            return str(pattern.pattern).strip("/")
    raise ValueError(
        f"App {app_label!r} is not mounted in core.api.urls. Add path(..., include('core.{app_label}.urls'))."
    )


def _http_methods_for_callback(callback: Any) -> list[str]:
    cls = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
    if cls is None:
        return ["GET"]
    methods: list[str] = []
    for method in ("get", "post", "put", "patch", "delete", "head", "options"):
        if hasattr(cls, method):
            fn = getattr(cls, method, None)
            if callable(fn):
                methods.append(method.upper())
    return methods or ["GET"]


def walk_app_urlpatterns(
    patterns: list,
    prefix: str,
    on_pattern: Callable[[str, URLPattern], None],
) -> None:
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            seg = str(pattern.pattern)
            walk_app_urlpatterns(pattern.url_patterns, prefix + seg, on_pattern)
        elif isinstance(pattern, URLPattern):
            on_pattern(prefix + str(pattern.pattern), pattern)


def discover_routes(app_label: str) -> tuple[str, list[DiscoveredRoute]]:
    """Load core.<app_label>.urls and return (api_segment, enriched routes)."""
    api_segment = _api_segment_for_app(app_label)
    mod = importlib.import_module(f"core.{app_label}.urls")
    routes: list[DiscoveredRoute] = []

    def on_pattern(full_django_route: str, pat: URLPattern) -> None:
        postman_rel, _params = django_route_to_postman_path(full_django_route, pat.name)
        path_clean = postman_rel.strip("/")
        if path_clean:
            path_clean = path_clean + "/"
        full_path = f"{api_segment}/{path_clean}" if path_clean else f"{api_segment}/"
        methods = _http_methods_for_callback(pat.callback)
        view_cls = getattr(pat.callback, "cls", None) or getattr(pat.callback, "view_class", None)
        route = DiscoveredRoute(
            postman_path=full_path,
            path_param_names=django_route_to_postman_path(full_django_route, pat.name)[1],
            url_name=pat.name,
            methods=methods,
            view_class=view_cls,
            view_module=getattr(view_cls, "__module__", "") if view_cls else "",
        )
        routes.append(enrich_route(route))

    walk_app_urlpatterns(mod.urlpatterns, "", on_pattern)
    return api_segment, routes


def list_resources(routes: list[DiscoveredRoute]) -> list[str]:
    return sorted({route.resource_folder for route in routes})


def list_routes_table(routes: list[DiscoveredRoute]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for route in sorted(routes, key=lambda item: (item.resource_folder, item.category, item.postman_path)):
        for method in route.methods:
            rows.append({
                "resource": route.resource_folder,
                "category": route.category.value,
                "method": method,
                "url_name": route.url_name or "",
                "path": route.postman_path,
            })
    return rows
