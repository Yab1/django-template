from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EndpointCategory(StrEnum):
    CRUD = "crud"
    BULK = "bulk"
    HISTORY = "history"
    AUDIT = "audit"
    ACTION = "action"
    CAPABILITY = "capability"
    MISC = "misc"


CATEGORY_ORDER: tuple[EndpointCategory, ...] = (
    EndpointCategory.CRUD,
    EndpointCategory.BULK,
    EndpointCategory.HISTORY,
    EndpointCategory.AUDIT,
    EndpointCategory.ACTION,
    EndpointCategory.CAPABILITY,
    EndpointCategory.MISC,
)


@dataclass
class DiscoveredRoute:
    """Single routable endpoint (may expand to multiple HTTP methods)."""

    postman_path: str
    path_param_names: list[str]
    url_name: str | None
    methods: list[str]
    view_class: type | None = None
    view_module: str = ""
    resource_key: str = "misc"
    resource_folder: str = "misc"
    category: EndpointCategory = EndpointCategory.MISC


@dataclass
class GenerationOptions:
    app_label: str
    collection_name: str
    resources: set[str] | None = None
    categories: set[str] | None = None
    exclude_categories: set[str] | None = None
    skip_responses: bool = False
    skip_scripts: bool = False
    skip_terminology: bool = False
    merge: bool = False
    refresh_responses: bool = False
    only_missing: bool = False
    stable_id: bool = False
    pr_prefix: str | None = None
    per_resource_file: bool = False
    generate_environment: bool = False
    write_manifest: bool = False
    strict: bool = False
    auth_default: str = "user"


@dataclass
class GenerationWarning:
    message: str
    url_name: str | None = None


@dataclass
class GenerationResult:
    collection: dict[str, Any]
    request_count: int
    warnings: list[GenerationWarning] = field(default_factory=list)
    environment: dict[str, Any] | None = None
