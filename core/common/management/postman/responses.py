"""Build saved Postman response examples."""

import json
from typing import Any

from core.api.renderers import DEFAULT_META, DEFAULT_SUCCESS_MESSAGE
from core.common.management.postman.introspection import (
    resolve_response_payload,
    serializer_to_example_json,
)

DEFAULT_ERROR_META = {"version": "v1"}


def _is_paginated_serializer(serializer_class: type) -> bool:
    try:
        serializer = serializer_class()
        fields = serializer.fields
    except Exception:
        return False
    return {"limit", "offset", "count", "results"}.issubset(set(fields.keys()))


def _success_envelope(result: Any) -> dict[str, Any]:
    return {
        "status": "success",
        "result": result,
        "meta": DEFAULT_META,
        "message": DEFAULT_SUCCESS_MESSAGE,
    }


def _error_envelope(*, status_code: int, message: str, problem: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "error",
        "result": problem,
        "meta": DEFAULT_ERROR_META,
        "message": message,
    }


def expected_status_code(method: str, *, url_name: str | None) -> int:
    method = method.upper()
    if method == "POST" and url_name and url_name.endswith("-create"):
        return 201
    if method == "DELETE":
        return 204
    return 200


def build_success_response_body(
    view_class: type | None,
    *,
    method: str,
    resource_key: str,
    terminology_values: dict[str, str] | None = None,
    empty_list: bool = False,
) -> dict[str, Any] | None:
    payload_ser = resolve_response_payload(view_class, method=method)
    if payload_ser is None:
        return None

    if empty_list and _is_paginated_serializer(payload_ser):
        return _success_envelope({
            "limit": 10,
            "offset": 0,
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        })

    result = serializer_to_example_json(
        payload_ser,
        resource_key=resource_key,
        for_response=True,
        terminology_values=terminology_values,
    )
    if result is None:
        return None

    if _is_paginated_serializer(payload_ser) and isinstance(result, dict):
        result.setdefault("limit", 10)
        result.setdefault("offset", 0)
        result.setdefault("count", 1)
        result.setdefault("next", None)
        result.setdefault("previous", None)
        if "results" in result and isinstance(result["results"], list) and not result["results"]:
            item_ser = payload_ser().fields["results"].child.__class__
            item = serializer_to_example_json(
                item_ser,
                resource_key=resource_key,
                for_response=True,
                terminology_values=terminology_values,
            )
            result["results"] = [item] if item else []

    return _success_envelope(result)


def build_error_response_examples(*, postman_path: str) -> list[dict[str, Any]]:
    instance = f"/api/v1/{postman_path.strip('/')}/"
    examples: list[tuple[str, int, str, dict[str, Any]]] = [
        (
            "400 validation error",
            400,
            "One or more fields are invalid.",
            {
                "type": "validation-error",
                "title": "Validation Error",
                "status": 400,
                "detail": "One or more fields are invalid.",
                "instance": instance,
                "errors": {"field": ["This field is required."]},
            },
        ),
        (
            "403 forbidden",
            403,
            "You do not have permission to perform this action.",
            {
                "type": "forbidden",
                "title": "Forbidden",
                "status": 403,
                "detail": "You do not have permission to perform this action.",
                "instance": instance,
            },
        ),
        (
            "404 not found",
            404,
            "Not found.",
            {
                "type": "not-found",
                "title": "Not Found",
                "status": 404,
                "detail": "Not found.",
                "instance": instance,
            },
        ),
    ]
    saved: list[dict[str, Any]] = []
    for name, code, message, problem in examples:
        body = _error_envelope(status_code=code, message=message, problem=problem)
        saved.append({
            "name": name,
            "status": f"{code} {'OK' if code == 200 else 'Error'}",
            "code": code,
            "_postman_previewlanguage": "json",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "cookie": [],
            "body": json.dumps(body, indent=2),
        })
    return saved


def build_saved_responses(
    *,
    view_class: type | None,
    method: str,
    resource_key: str,
    url_name: str | None,
    postman_path: str,
    request_item: dict[str, Any],
    terminology_values: dict[str, str] | None = None,
    include_errors: bool = True,
) -> list[dict[str, Any]]:
    status_code = expected_status_code(method, url_name=url_name)
    if status_code == 204:
        return [
            {
                "name": "204 no content",
                "status": "No Content",
                "code": 204,
                "_postman_previewlanguage": "plain",
                "header": [],
                "cookie": [],
                "body": "",
                "originalRequest": request_item.get("request"),
            }
        ]

    responses: list[dict[str, Any]] = []
    success = build_success_response_body(
        view_class,
        method=method,
        resource_key=resource_key,
        terminology_values=terminology_values,
    )
    if success is not None:
        responses.append({
            "name": f"{status_code} success",
            "status": "Created" if status_code == 201 else "OK",
            "code": status_code,
            "_postman_previewlanguage": "json",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "cookie": [],
            "body": json.dumps(success, indent=2),
            "originalRequest": request_item.get("request"),
        })

    if method.upper() == "GET" and url_name and url_name.endswith("-list"):
        empty = build_success_response_body(
            view_class,
            method=method,
            resource_key=resource_key,
            terminology_values=terminology_values,
            empty_list=True,
        )
        if empty is not None:
            responses.append({
                "name": "200 empty list",
                "status": "OK",
                "code": 200,
                "_postman_previewlanguage": "json",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "cookie": [],
                "body": json.dumps(empty, indent=2),
                "originalRequest": request_item.get("request"),
            })

    if include_errors and method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
        for error_example in build_error_response_examples(postman_path=postman_path):
            error_example["originalRequest"] = request_item.get("request")
            responses.append(error_example)

    return responses


def build_test_script(*, expect_envelope: bool = True) -> list[str]:
    lines = [
        "pm.test('Status code is acceptable', function () {",
        "    pm.expect(pm.response.code).to.be.oneOf([200, 201, 204]);",
        "});",
    ]
    if expect_envelope:
        lines.extend([
            "if (pm.response.code !== 204) {",
            "    pm.test('Response uses API envelope', function () {",
            "        const data = pm.response.json();",
            "        pm.expect(data).to.have.property('status');",
            "        pm.expect(data).to.have.property('result');",
            "        pm.expect(data).to.have.property('meta');",
            "        pm.expect(data.meta).to.have.property('version');",
            "    });",
            "}",
        ])
    return lines
