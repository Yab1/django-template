"""Tests for generate_postman_collection and postman package."""

import json
from io import StringIO

from django.core.management import call_command
from django.db import models
from django.test import TestCase
from rest_framework import serializers

from core.common.management import postman_collection_gen as gen
from core.common.management.postman import (
    GenerationOptions,
    build_collection,
    example_body_for_view_method,
    normalize_resource_filter,
)
from core.common.management.postman.types import EndpointCategory
from core.terminology.apis.code_system import CodeSystemCreateApi


class _SampleTextChoices(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"


class _SampleIntChoices(models.IntegerChoices):
    LOW = 1, "Low"
    HIGH = 2, "High"


class PostmanCollectionGenTests(TestCase):
    def test_example_field_uses_api_value_for_text_choices(self) -> None:
        class S(serializers.Serializer):
            choice_f = serializers.ChoiceField(choices=_SampleTextChoices.choices)
            char_enum = serializers.ChoiceField(choices=_SampleTextChoices.choices)

        ser = S()
        self.assertEqual(gen._example_for_drf_field(ser.fields["choice_f"]), "draft")
        self.assertEqual(gen._example_for_drf_field(ser.fields["char_enum"]), "draft")

    def test_example_field_uses_api_value_for_integer_choices(self) -> None:
        class S(serializers.Serializer):
            int_pairs = serializers.ChoiceField(choices=[(10, "Ten"), (20, "Twenty")])
            int_enum = serializers.ChoiceField(choices=_SampleIntChoices.choices)

        ser = S()
        self.assertEqual(gen._example_for_drf_field(ser.fields["int_pairs"]), 10)
        self.assertEqual(gen._example_for_drf_field(ser.fields["int_enum"]), 1)

    def test_example_field_multiple_choice_first_value(self) -> None:
        class S(serializers.Serializer):
            multi = serializers.MultipleChoiceField(choices=_SampleTextChoices.choices)

        ser = S()
        self.assertEqual(gen._example_for_drf_field(ser.fields["multi"]), ["draft"])

    def test_first_choice_api_value_iterates_enum_members(self) -> None:
        first = gen._first_choice_api_value(_SampleTextChoices)
        self.assertEqual(first, "draft")

    def test_uuid_body_variable_name_for_fk_field_is_not_prefixed(self) -> None:
        self.assertEqual(
            gen._uuid_body_variable_name(resource_key="identity-group-characteristic", field_name="identity_group_id"),
            "identity_group_id",
        )

    def test_discover_routes_terminology(self) -> None:
        segment, routes = gen.discover_routes("terminology")
        self.assertEqual(segment, "terminology")
        self.assertGreaterEqual(len(routes), 15)
        names = {route.url_name for route in routes}
        self.assertIn("code-system-create", names)
        self.assertIn("code-system-model-crud-audit-list", names)
        self.assertIn("code-system-history-diff", names)

    def test_build_collection_has_variables_auth_and_category_folders(self) -> None:
        _, routes = gen.discover_routes("terminology")
        options = GenerationOptions(app_label="terminology", collection_name="terminology", resources={"code_system"})
        result = build_collection(routes=routes, options=options)
        col = result.collection
        keys = {variable["key"] for variable in col["variable"]}
        status_var = next(variable for variable in col["variable"] if variable["key"] == "status_id")
        self.assertIn("base_url", keys)
        self.assertIn("user_access_token", keys)
        self.assertIn("code_system_id", keys)
        self.assertIn("code_system_history_id", keys)
        self.assertIn("status_id", keys)
        self.assertNotEqual(status_var["value"], "")
        self.assertIn("CODESYSTEM_URL", status_var["description"].upper())
        self.assertIn("publication_status", status_var["description"].lower())

        top_names = {folder["name"] for folder in col["item"]}
        self.assertIn("crud", top_names)
        self.assertIn("history", top_names)
        self.assertIn("audit", top_names)

        crud_folder = next(folder for folder in col["item"] if folder["name"] == "crud")
        first_request = crud_folder["item"][0]
        self.assertEqual(first_request["request"]["auth"]["type"], "bearer")
        self.assertIn("response", first_request)
        self.assertTrue(first_request["response"])

    def test_code_system_create_body_matches_input_serializer(self) -> None:
        body = gen.example_body_for_view_method(
            CodeSystemCreateApi,
            "POST",
            resource_key="code-system",
        )
        self.assertIsNotNone(body)
        assert body is not None
        self.assertIn("url", body)
        self.assertEqual(body["status_id"], "{{status_id}}")
        self.assertNotIn("email", body)
        self.assertNotIn("reference_id", body)

    def test_create_post_has_id_capture_script(self) -> None:
        _, routes = gen.discover_routes("terminology")
        options = GenerationOptions(app_label="terminology", collection_name="terminology")
        col = build_collection(routes=routes, options=options).collection

        create_items = []
        for folder in col["item"]:
            for category_folder in folder.get("item", []):
                for item in category_folder.get("item", []):
                    req = item["request"]
                    if req["method"] == "POST" and item["name"] == "create":
                        create_items.append(item)

        self.assertTrue(create_items)
        target = create_items[0]
        self.assertIn("event", target)
        script_exec = target["event"][0]["script"]["exec"]
        self.assertTrue(any('pm.collectionVariables.set("code_system_id"' in line for line in script_exec))

    def test_resource_key_strips_history_navigation_suffixes(self) -> None:
        self.assertEqual(gen._resource_key_from_url_name("code-system-history-diff"), "code-system")
        self.assertEqual(gen._resource_key_from_url_name("code-system-history-next"), "code-system")
        self.assertEqual(gen._domain_folder_name("code-system"), "code_system")

    def test_billing_charge_item_action_category(self) -> None:
        _, routes = gen.discover_routes("billing")
        action_routes = [route for route in routes if route.url_name == "charge-item-status-transition"]
        self.assertEqual(len(action_routes), 1)
        self.assertEqual(action_routes[0].category, EndpointCategory.ACTION)
        self.assertEqual(action_routes[0].resource_folder, "charge_item")

    def test_category_filter_limits_requests(self) -> None:
        _, routes = gen.discover_routes("billing")
        options = GenerationOptions(
            app_label="billing",
            collection_name="charge item",
            resources={"charge_item"},
            categories={"crud"},
        )
        result = build_collection(routes=routes, options=options)
        categories = {folder["name"] for folder in result.collection["item"]}
        self.assertEqual(categories, {"crud"})
        self.assertGreater(result.request_count, 0)

    def test_saved_response_has_success_envelope(self) -> None:
        _, routes = gen.discover_routes("terminology")
        options = GenerationOptions(
            app_label="terminology",
            collection_name="terminology",
            resources={"code_system"},
            categories={"crud"},
        )
        col = build_collection(routes=routes, options=options).collection
        create_item = next(
            item
            for folder in col["item"]
            if folder["name"] == "crud"
            for item in folder["item"]
            if item["name"] == "create"
        )
        success = next(row for row in create_item["response"] if row["code"] == 201)
        body = json.loads(success["body"])
        self.assertEqual(body["status"], "success")
        self.assertIn("result", body)
        self.assertEqual(body["meta"]["version"], "v1")

    def test_command_dry_run(self) -> None:
        buf = StringIO()
        call_command("generate_postman_collection", "terminology", dry_run=True, stdout=buf)
        out = buf.getvalue()
        self.assertIn("Would generate", out)

    def test_command_list_resources(self) -> None:
        buf = StringIO()
        call_command("generate_postman_collection", "billing", "--list-resources", stdout=buf)
        out = buf.getvalue()
        self.assertIn("charge_item", out)
        self.assertIn("invoice", out)

    def test_normalize_resource_filter(self) -> None:
        self.assertEqual(normalize_resource_filter("charge-item"), "charge_item")

    def test_action_without_input_serializer_has_no_request_body(self) -> None:
        from core.billing.apis.invoice.action import InvoiceFinalizeApi
        from core.common.management.postman.builder import _build_request_item

        item = _build_request_item(
            title="finalize",
            method="POST",
            postman_path="billing/invoices/{{invoice_id}}/finalize/",
            description="Finalize invoice",
            include_json_body=False,
            json_body=None,
        )
        self.assertNotIn("body", item["request"])
        self.assertNotIn("Content-Type", [header["key"] for header in item["request"].get("header", [])])

        body = example_body_for_view_method(
            InvoiceFinalizeApi,
            "POST",
            resource_key="invoice",
        )
        self.assertIsNone(body)

    def test_lab_operational_specimen_resource_includes_all_action_routes(self) -> None:
        _, routes = gen.discover_routes("lab")
        options = GenerationOptions(
            app_label="lab",
            collection_name="operational specimen",
            resources={"operational_specimen"},
        )
        result = build_collection(routes=routes, options=options)

        action_items = []
        for folder in result.collection["item"]:
            if folder["name"] != "action":
                continue
            action_items.extend(folder.get("item", []))

        action_names = {item["name"] for item in action_items}
        self.assertIn("status", action_names)
        self.assertIn("reject", action_names)
        self.assertIn("request recollection", action_names)

    def test_lab_worklist_resource_includes_crud_and_action_routes(self) -> None:
        _, routes = gen.discover_routes("lab")
        options = GenerationOptions(
            app_label="lab",
            collection_name="worklist",
            resources={"worklist"},
        )
        result = build_collection(routes=routes, options=options)

        by_category: dict[str, set[str]] = {}
        for folder in result.collection["item"]:
            by_category[folder["name"]] = {item["name"] for item in folder.get("item", [])}

        self.assertIn("list", by_category.get("crud", set()))
        self.assertIn("retrieve", by_category.get("crud", set()))
        self.assertIn("assign", by_category.get("action", set()))
        self.assertIn("complete", by_category.get("action", set()))
