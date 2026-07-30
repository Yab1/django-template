"""Introspect DRF serializers for Postman request/response examples."""

import re
import uuid
from enum import Enum
from typing import Any

from rest_framework import serializers as drf_serializers
from rest_framework.relations import HyperlinkedRelatedField, PrimaryKeyRelatedField

_SKIP_FIELD = object()
_POSTMAN_VAR_RE = re.compile(r"^\{\{(?P<name>[^}]+)\}\}$")

PLACEHOLDER_BODY_OBJECT = {
    "name": "{{$randomLoremSlug}}",
    "title": "{{$randomLoremWords}}",
    "description": "{{$randomLoremSentence}}",
    "url": "{{$randomUrl}}",
    "version": "{{$randomSemver}}",
    "email": "{{$randomExampleEmail}}",
    "reference_id": "{{$guid}}",
}

FIXED_ISO_TIMESTAMP = "2026-01-15T12:00:00.000Z"


def _coerce_choice_raw_to_api_value(raw: Any) -> Any:
    if isinstance(raw, Enum):
        return raw.value
    return raw


def _first_choice_api_value(choices: Any) -> Any | None:
    if choices is None:
        return None
    try:
        iterator = iter(choices)
    except TypeError:
        return None
    try:
        first = next(iterator)
    except StopIteration:
        return None
    if isinstance(first, (list, tuple)) and len(first) >= 1:
        return _coerce_choice_raw_to_api_value(first[0])
    return _coerce_choice_raw_to_api_value(first)


def _uuid_body_variable_name(*, resource_key: str, field_name: str) -> str:
    clean_name = field_name.replace("-", "_")
    if clean_name.endswith("_id"):
        return clean_name
    prefix = resource_key.replace("-", "_")
    if resource_key.endswith("-history"):
        prefix = resource_key[: -len("-history")].replace("-", "_")
    if clean_name.startswith(f"{prefix}_"):
        return clean_name
    return f"{prefix}_{clean_name}"


def _deterministic_uuid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def _example_for_drf_field(
    field: Any,
    *,
    field_name: str = "",
    resource_key: str = "",
    for_response: bool = False,
    terminology_values: dict[str, str] | None = None,
    terminology_body_vars: dict[str, str] | None = None,
) -> Any:
    terminology_values = terminology_values or {}
    terminology_body_vars = terminology_body_vars or {}
    if not for_response and field_name and field_name in terminology_body_vars:
        return terminology_body_vars[field_name]

    if for_response and getattr(field, "write_only", False):
        return _SKIP_FIELD
    if not for_response and getattr(field, "read_only", False):
        return _SKIP_FIELD

    if isinstance(field, drf_serializers.ListSerializer):
        child_body = serializer_to_example_json(
            field.child.__class__,
            resource_key=resource_key,
            for_response=for_response,
            terminology_values=terminology_values,
            terminology_body_vars=terminology_body_vars,
        )
        return [child_body] if child_body is not None else [{}]

    if isinstance(field, drf_serializers.ListField):
        inner = _example_for_drf_field(
            field.child,
            field_name="",
            resource_key=resource_key,
            for_response=for_response,
            terminology_values=terminology_values,
            terminology_body_vars=terminology_body_vars,
        )
        if inner is _SKIP_FIELD:
            return []
        return [inner]

    if isinstance(field, drf_serializers.Serializer):
        nested = serializer_to_example_json(
            field.__class__,
            resource_key=resource_key,
            for_response=for_response,
            terminology_values=terminology_values,
            terminology_body_vars=terminology_body_vars,
        )
        return nested if nested is not None else {}

    if isinstance(field, drf_serializers.JSONField):
        return {}
    if isinstance(field, drf_serializers.DictField):
        return {}

    if isinstance(field, drf_serializers.BooleanField):
        return True if for_response else "{{$randomBoolean}}"

    if isinstance(field, drf_serializers.UUIDField):
        if field_name in terminology_values:
            return terminology_values[field_name]
        if for_response:
            return _deterministic_uuid(f"{resource_key}:{field_name}")
        if resource_key and field_name:
            return f"{{{{{_uuid_body_variable_name(resource_key=resource_key, field_name=field_name)}}}}}"
        return "{{$guid}}"

    if isinstance(field, drf_serializers.URLField):
        return "https://example.org/resource" if for_response else "{{$randomUrl}}"

    if isinstance(field, drf_serializers.EmailField):
        return "user@example.org" if for_response else "{{$randomExampleEmail}}"

    if isinstance(field, drf_serializers.IPAddressField):
        return "192.0.2.1" if for_response else "{{$randomIP}}"

    if isinstance(field, drf_serializers.SlugField):
        return "sample-slug" if for_response else "{{$randomLoremSlug}}"

    if isinstance(field, (drf_serializers.IntegerField, drf_serializers.DurationField)):
        choices = getattr(field, "choices", None)
        if choices:
            api_val = _first_choice_api_value(choices)
            if api_val is not None:
                return api_val
        return 1 if for_response else "{{$randomInt}}"

    if isinstance(field, (drf_serializers.FloatField, drf_serializers.DecimalField)):
        choices = getattr(field, "choices", None)
        if choices:
            api_val = _first_choice_api_value(choices)
            if api_val is not None:
                return api_val
        return 1.0 if for_response else 0.0

    if isinstance(field, drf_serializers.DateTimeField):
        return FIXED_ISO_TIMESTAMP if for_response else "{{$isoTimestamp}}"
    if isinstance(field, drf_serializers.DateField):
        return "2026-01-15" if for_response else "{{$isoTimestamp}}"
    if isinstance(field, drf_serializers.TimeField):
        return "12:00:00" if for_response else "{{$isoTimestamp}}"

    if isinstance(field, drf_serializers.MultipleChoiceField):
        choices = getattr(field, "choices", None)
        if choices:
            api_val = _first_choice_api_value(choices)
            if api_val is not None:
                return [api_val]
        return []

    if isinstance(field, drf_serializers.ChoiceField):
        choices = getattr(field, "choices", None)
        if choices:
            api_val = _first_choice_api_value(choices)
            if api_val is not None:
                return api_val
        return ""

    if isinstance(field, HyperlinkedRelatedField):
        return "https://example.org/resource" if for_response else "{{$randomUrl}}"

    if isinstance(field, PrimaryKeyRelatedField):
        pk_field = getattr(field, "pk_field", None)
        if pk_field is not None:
            return _example_for_drf_field(
                pk_field,
                field_name=field_name,
                resource_key=resource_key,
                for_response=for_response,
                terminology_values=terminology_values,
            )
        if field_name in terminology_values:
            return terminology_values[field_name]
        if for_response:
            return _deterministic_uuid(f"{resource_key}:{field_name}")
        if resource_key and field_name:
            return f"{{{{{_uuid_body_variable_name(resource_key=resource_key, field_name=field_name)}}}}}"
        return "{{$guid}}"

    if isinstance(field, drf_serializers.CharField):
        choices = getattr(field, "choices", None)
        if choices:
            api_val = _first_choice_api_value(choices)
            if api_val is not None:
                return api_val
        if field_name == "version":
            return "1.0.0" if for_response else "{{$randomSemver}}"
        if field_name == "description":
            return "Sample description." if for_response else "{{$randomLoremSentence}}"
        if field_name == "name":
            return "sample-name" if for_response else "{{$randomLoremSlug}}"
        return "sample text" if for_response else "{{$randomLoremWords}}"

    return "sample text" if for_response else "{{$randomLoremWords}}"


def serializer_to_example_json(
    serializer_class: type,
    *,
    resource_key: str = "",
    for_response: bool = False,
    terminology_values: dict[str, str] | None = None,
    terminology_body_vars: dict[str, str] | None = None,
) -> dict[str, Any] | list[Any] | None:
    try:
        serializer = serializer_class()
    except Exception:
        return None

    if isinstance(serializer, drf_serializers.ListSerializer):
        item = serializer_to_example_json(
            serializer.child.__class__,
            resource_key=resource_key,
            for_response=for_response,
            terminology_values=terminology_values,
            terminology_body_vars=terminology_body_vars,
        )
        return [item] if item is not None else []

    if not isinstance(serializer, drf_serializers.Serializer):
        return None

    try:
        fields = serializer.fields
    except Exception:
        return None

    body: dict[str, Any] = {}
    for name, field in fields.items():
        value = _example_for_drf_field(
            field,
            field_name=name,
            resource_key=resource_key,
            for_response=for_response,
            terminology_values=terminology_values,
            terminology_body_vars=terminology_body_vars,
        )
        if value is _SKIP_FIELD:
            continue
        body[name] = value

    return body or None


def _serializer_classes_on_view(view_class: type | None) -> list[type]:
    if view_class is None:
        return []
    classes: list[type] = []
    for attr in (
        "InputSerializer",
        "BodySerializer",
        "UpdateSerializer",
        "QuerySerializer",
        "OutputSerializer",
        "SuccessResponseSerializer",
        "PaginatedResultSerializer",
    ):
        ser = getattr(view_class, attr, None)
        if ser is not None and isinstance(ser, type) and issubclass(ser, drf_serializers.BaseSerializer):
            classes.append(ser)
    return classes


def concept_id_fields_from_serializer_class(
    serializer_class: type,
    *,
    allowed_names: set[str] | frozenset[str] | None = None,
) -> set[str]:
    """Collect Concept ``*_id`` / ``*_ids`` fields from a DRF serializer tree."""
    names: set[str] = set()
    try:
        serializer = serializer_class()
    except Exception:
        return names

    if isinstance(serializer, drf_serializers.ListSerializer):
        return concept_id_fields_from_serializer_class(serializer.child.__class__)

    if not isinstance(serializer, drf_serializers.Serializer):
        return names

    try:
        fields = serializer.fields
    except Exception:
        return names

    for name, field in fields.items():
        if allowed_names is not None and name not in allowed_names:
            if isinstance(field, drf_serializers.Serializer):
                names.update(
                    concept_id_fields_from_serializer_class(
                        field.__class__,
                        allowed_names=allowed_names,
                    )
                )
            if isinstance(field, drf_serializers.ListSerializer):
                names.update(
                    concept_id_fields_from_serializer_class(
                        field.child.__class__,
                        allowed_names=allowed_names,
                    )
                )
            continue
        if (name.endswith(("_id", "_ids"))) and isinstance(
            field,
            drf_serializers.UUIDField,
        ):
            names.add(name)
        if isinstance(field, drf_serializers.Serializer):
            names.update(
                concept_id_fields_from_serializer_class(
                    field.__class__,
                    allowed_names=allowed_names,
                )
            )
        if isinstance(field, drf_serializers.ListSerializer):
            names.update(
                concept_id_fields_from_serializer_class(
                    field.child.__class__,
                    allowed_names=allowed_names,
                )
            )
    return names


def concept_id_fields_from_view(
    view_class: type | None,
    *,
    app_label: str,
    resource_folder: str,
) -> set[str]:
    from core.common.management.postman.model_fields import (
        concept_id_field_names_for_model,
        filter_terminology_concept_fields,
        resolve_model_for_resource,
    )

    model = resolve_model_for_resource(app_label, resource_folder)
    allowed = concept_id_field_names_for_model(model) if model is not None else frozenset()

    names: set[str] = set()
    for ser_cls in _serializer_classes_on_view(view_class):
        names.update(concept_id_fields_from_serializer_class(ser_cls, allowed_names=allowed))
        if ser_cls.__name__.endswith("SuccessResponse") or "SuccessResponse" in ser_cls.__name__:
            try:
                success = ser_cls()
                if "result" in success.fields:
                    result_field = success.fields["result"]
                    if isinstance(result_field, drf_serializers.Serializer):
                        names.update(
                            concept_id_fields_from_serializer_class(
                                result_field.__class__,
                                allowed_names=allowed,
                            )
                        )
            except Exception:
                pass
    return filter_terminology_concept_fields(names, app_label=app_label, resource_folder=resource_folder)


def _input_serializer_class(view_class: type | None) -> type | None:
    if view_class is None:
        return None
    for attr in ("InputSerializer", "BodySerializer", "UpdateSerializer"):
        ser = getattr(view_class, attr, None)
        if ser is not None and isinstance(ser, type) and issubclass(ser, drf_serializers.BaseSerializer):
            return ser
    return None


def _query_serializer_class(view_class: type | None) -> type | None:
    if view_class is None:
        return None
    ser = getattr(view_class, "QuerySerializer", None)
    if ser is not None and isinstance(ser, type) and issubclass(ser, drf_serializers.BaseSerializer):
        return ser
    return None


def _unwrap_result_field(serializer_instance: drf_serializers.BaseSerializer) -> drf_serializers.Field | None:
    try:
        fields = serializer_instance.fields
    except Exception:
        return None
    if "result" in fields:
        return fields["result"]
    return None


def resolve_response_payload(view_class: type | None, *, method: str) -> Any | None:
    """Return serializer class for response `result` payload."""
    if view_class is None:
        return None

    success_cls = getattr(view_class, "SuccessResponseSerializer", None)
    if success_cls is not None and isinstance(success_cls, type):
        try:
            success = success_cls()
            result_field = _unwrap_result_field(success)
            if result_field is not None:
                if isinstance(result_field, drf_serializers.ListSerializer):
                    return result_field.child.__class__
                if isinstance(result_field, drf_serializers.Serializer):
                    return result_field.__class__
                inner = getattr(result_field, "child", None)
                if inner is not None and hasattr(inner, "__class__"):
                    return inner.__class__
                return result_field.__class__
        except Exception:
            pass

    paginated = getattr(view_class, "PaginatedResultSerializer", None)
    if paginated is not None and method.upper() == "GET":
        return paginated

    output = getattr(view_class, "OutputSerializer", None)
    if output is not None:
        return output

    return None


def example_body_for_view_method(
    view_class: type | None,
    method: str,
    *,
    resource_key: str,
    terminology_values: dict[str, str] | None = None,
    terminology_body_vars: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    if method.upper() not in ("POST", "PUT", "PATCH", "DELETE"):
        return None
    ser_cls = _input_serializer_class(view_class)
    if ser_cls is None:
        return None
    body = serializer_to_example_json(
        ser_cls,
        resource_key=resource_key,
        for_response=False,
        terminology_values=terminology_values,
        terminology_body_vars=terminology_body_vars,
    )
    return body if isinstance(body, dict) else None


def query_params_for_view(view_class: type | None) -> list[dict[str, Any]] | None:
    ser_cls = _query_serializer_class(view_class)
    if ser_cls is None:
        return None
    try:
        serializer = ser_cls()
    except Exception:
        return None

    query: list[dict[str, Any]] = []
    for name, field in serializer.fields.items():
        required = getattr(field, "required", False)
        default = getattr(field, "default", drf_serializers.empty)
        value = ""
        disabled = not required
        if default is not drf_serializers.empty and default is not None:
            value = str(default)
        example = _example_for_drf_field(field, field_name=name, for_response=False)
        if example is not _SKIP_FIELD and example != "":
            value = str(example)
        query.append({
            "key": name,
            "value": value,
            "description": getattr(field, "help_text", "") or f"Query parameter `{name}`",
            "disabled": disabled,
        })
    return query or None


def collect_named_postman_vars(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        for item in value.values():
            names.update(collect_named_postman_vars(item))
        return names
    if isinstance(value, list):
        for item in value:
            names.update(collect_named_postman_vars(item))
        return names
    if isinstance(value, str):
        match = _POSTMAN_VAR_RE.match(value)
        if match:
            name = match.group("name")
            if not name.startswith("$"):
                names.add(name)
    return names


def auth_token_variable(view_class: type | None) -> str:
    if view_class is None:
        return "user_access_token"
    action = getattr(view_class, "authorization_action", "") or ""
    if "admin" in action.lower():
        return "admin_access_token"
    if any(token in action.lower() for token in ("audit", "hard_delete")):
        return "admin_access_token"
    return "user_access_token"
