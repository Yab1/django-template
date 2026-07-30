"""Tests for scaffold_standard_api generator and command."""

from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.test import TestCase

from core.common.management import scaffold_standard_api_generator as gen
from core.common.management.commands.scaffold_standard_api import _resolve_app_label


class ScaffoldStandardApiGeneratorTests(TestCase):
    def test_resolve_app_label_case_insensitive(self) -> None:
        self.assertEqual(_resolve_app_label("terminology"), "terminology")
        self.assertEqual(_resolve_app_label("Terminology"), "terminology")
        self.assertEqual(_resolve_app_label("identities"), "identities")
        self.assertEqual(_resolve_app_label("Identities"), "identities")

    def test_build_context_code_system(self) -> None:
        CodeSystem = apps.get_model("terminology", "CodeSystem")
        ctx = gen.build_context(model=CodeSystem, url_prefix=None, openapi_tag=None)
        self.assertEqual(ctx.resource_module, "code_system")
        self.assertEqual(ctx.model_name, "CodeSystem")
        self.assertTrue(ctx.has_history)
        self.assertTrue(ctx.has_soft_delete)
        self.assertEqual(ctx.openapi_tag_constant_name, "OPENAPI_TAG_TERMINOLOGY_CODE_SYSTEMS")
        self.assertEqual(ctx.app_url_namespace, "terminology")
        self.assertIn("code-systems", ctx.openapi_tag_value)

    def test_build_context_skips_history_when_no_historical_model(self) -> None:
        PolicyAuditEvent = apps.get_model("security", "PolicyAuditEvent")
        ctx = gen.build_context(
            model=PolicyAuditEvent,
            url_prefix=None,
            openapi_tag=None,
            with_history_extras=True,
        )
        self.assertFalse(ctx.has_history)
        self.assertFalse(ctx.with_history_extras)
        self.assertTrue(ctx.has_soft_delete)
        apis = gen.render_apis_py(ctx)
        self.assertNotIn("PolicyAuditEventHistoryListApi", apis)
        self.assertIn("PolicyAuditEventDeleteApi", apis)
        selectors = gen.render_selectors_py(ctx)
        self.assertNotIn("def get_policy_audit_event_history", selectors)
        self.assertNotIn("from django.apps import apps", selectors)

    def test_plural_snake(self) -> None:
        self.assertEqual(gen._plural_snake("policy"), "policies")
        self.assertEqual(gen._plural_snake("code_system"), "code_systems")

    def test_render_apis_contains_list_selector(self) -> None:
        CodeSystem = apps.get_model("terminology", "CodeSystem")
        ctx = gen.build_context(model=CodeSystem, url_prefix="code-systems", openapi_tag="terminology")
        text = gen.render_apis_py(ctx)
        self.assertIn("get_code_systems", text)
        self.assertIn("CodeSystemCreateApi", text)
        self.assertIn("from core.terminology.constants import OPENAPI_TAG_TERMINOLOGY_CODE_SYSTEMS", text)
        self.assertIn("tags=[OPENAPI_TAG_TERMINOLOGY_CODE_SYSTEMS]", text)

    def test_terminology_concept_fk_uses_concept_compact_serializer(self) -> None:
        CodeSystem = apps.get_model("terminology", "CodeSystem")
        ctx = gen.build_context(model=CodeSystem, url_prefix="code-systems", openapi_tag=None)
        self.assertTrue(gen._context_has_terminology_concept_fk(ctx))
        text = gen.render_apis_py(ctx)
        self.assertIn("from core.terminology.serializers import ConceptCompactSerializer", text)
        self.assertIn("status = ConceptCompactSerializer", text)

    def test_char_field_with_choices_emits_choice_field(self) -> None:
        IdentityGroup = apps.get_model("identities", "IdentityGroup")
        ctx = gen.build_context(
            model=IdentityGroup,
            url_prefix="identity-groups",
            openapi_tag=None,
        )
        text = gen.render_apis_py(ctx)
        self.assertIn("membership_mode = serializers.ChoiceField", text)
        self.assertIn("from core.identities.models import IdentityGroup", text)
        self.assertIn("choices=IdentityGroup.MembershipMode.choices", text)

    def test_ordered_fields_put_concrete_model_fields_before_mixin_base_fields(self) -> None:
        """Django sets Field.model to the concrete class for inherited fields; scaffold uses abstract ancestors."""
        IdentityGroup = apps.get_model("identities", "IdentityGroup")
        ctx = gen.build_context(
            model=IdentityGroup,
            url_prefix="identity-groups",
            openapi_tag=None,
        )
        names = [item.name for item in ctx.ordered_fields]
        self.assertLess(names.index("name"), names.index("metadata"))
        self.assertLess(names.index("name"), names.index("is_visible"))
        self.assertIsNone(ctx.reference_id_field)

    def test_field_names_from_abstract_ancestors_includes_base_and_mixin(self) -> None:
        IdentityGroup = apps.get_model("identities", "IdentityGroup")
        abstract = gen._field_names_from_abstract_ancestors(IdentityGroup)
        self.assertIn("metadata", abstract)
        self.assertIn("is_visible", abstract)

    def test_content_type_fk_uses_integer_input_and_compact_serializer_output(self) -> None:
        IdentityGroup = apps.get_model("identities", "IdentityGroup")
        ctx = gen.build_context(
            model=IdentityGroup,
            url_prefix="identity-groups",
            openapi_tag=None,
        )
        self.assertTrue(gen._context_has_content_type_fk(ctx))
        text = gen.render_apis_py(ctx)
        self.assertIn("from core.api.serializers import ContentTypeCompactSerializer", text)
        self.assertIn("ContentTypeNaturalKeyField", text)
        self.assertIn("managing_entity_type = ContentTypeCompactSerializer", text)
        self.assertIn(
            'managing_entity_type = ContentTypeNaturalKeyField(source="managing_entity_type_id"',
            text,
        )

    def test_reference_id_is_output_only_not_create_or_update_input(self) -> None:
        Patient = apps.get_model("individuals", "Patient")
        ctx = gen.build_context(model=Patient, url_prefix="patients", openapi_tag=None)
        self.assertIsNotNone(ctx.reference_id_field)

        apis_text = gen.render_apis_py(ctx)
        self.assertIn("reference_id = serializers.CharField", apis_text)

        create_idx = apis_text.find("class PatientCreateApi")
        update_idx = apis_text.find("class PatientUpdateApi")

        self.assertNotEqual(create_idx, -1)
        self.assertNotEqual(update_idx, -1)

        create_input_idx = apis_text.find("class InputSerializer", create_idx)
        create_output_idx = apis_text.find("class OutputSerializer", create_input_idx)
        update_input_idx = apis_text.find("class InputSerializer", update_idx)
        update_output_idx = apis_text.find("class OutputSerializer", update_input_idx)

        self.assertNotEqual(create_input_idx, -1)
        self.assertNotEqual(create_output_idx, -1)
        self.assertNotEqual(update_input_idx, -1)
        self.assertNotEqual(update_output_idx, -1)

        create_block = apis_text[create_input_idx:create_output_idx]
        update_block = apis_text[update_input_idx:update_output_idx]
        self.assertNotIn("reference_id = serializers.", create_block)
        self.assertNotIn("reference_id = serializers.", update_block)

    def test_reference_id_not_writable_in_services(self) -> None:
        Patient = apps.get_model("individuals", "Patient")
        ctx = gen.build_context(model=Patient, url_prefix="patients", openapi_tag=None)
        services_text = gen.render_services_py(ctx)

        self.assertNotIn("reference_id:", services_text)
        self.assertNotIn('kwargs["reference_id"]', services_text)

    def test_output_field_order_follows_model_declaration(self) -> None:
        CodeSystem = apps.get_model("terminology", "CodeSystem")
        ctx = gen.build_context(model=CodeSystem, url_prefix="code-systems", openapi_tag=None)
        text = gen.render_apis_py(ctx)
        block_start = text.find("class CodeSystemCreateApi")
        block_end = text.find("class CodeSystemListApi", block_start)
        block = text[block_start:block_end]
        out_start = block.find("class OutputSerializer")
        out_block = block[out_start:]
        idx_version = out_block.find("version = serializers.CharField")
        idx_status = out_block.find("status = ConceptCompactSerializer")
        idx_description = out_block.find("description = serializers.CharField")
        idx_metadata = out_block.find("metadata = serializers.JSONField")
        idx_is_visible = out_block.find("is_visible = serializers.BooleanField")
        self.assertNotEqual(idx_version, -1, msg="version field missing from Create OutputSerializer")
        self.assertNotEqual(idx_status, -1, msg="status field missing")
        self.assertNotEqual(idx_description, -1, msg="description field missing")
        self.assertLess(idx_version, idx_status, "status should follow version as on the model")
        self.assertLess(idx_status, idx_description, "description should follow status")
        self.assertLess(idx_description, idx_metadata, "BaseModel metadata should follow concrete fields")
        self.assertLess(idx_description, idx_is_visible, "VisibleMixin is_visible should follow concrete fields")

    def test_command_dry_run_policy(self) -> None:
        buf = StringIO()
        call_command(
            "scaffold_standard_api",
            "security.Policy",
            dry_run=True,
            skip_filters=True,
            skip_urls=True,
            skip_constants=True,
            stdout=buf,
        )
        out = buf.getvalue()
        self.assertIn("would write", out)
        self.assertIn("core/security/apis/policy/crud.py", out)

    def test_merge_package_init_py_adds_second_module(self) -> None:
        existing = """from .policy import (
    PolicyCreateApi,
)

__all__ = [
    "PolicyCreateApi",
]
"""
        merged = gen.merge_package_init_py(
            existing,
            from_module="policy_assignment",
            export_names=["PolicyAssignmentCreateApi", "PolicyAssignmentListApi"],
        )
        self.assertIn("from .policy_assignment import", merged)
        self.assertIn("PolicyAssignmentCreateApi", merged)
        self.assertIn("from .policy import", merged)
        self.assertIn('"PolicyCreateApi"', merged)
        self.assertIn('"PolicyAssignmentListApi"', merged)

    def test_merge_openapi_constant_into_constants(self) -> None:
        CodeSystem = apps.get_model("terminology", "CodeSystem")
        ctx = gen.build_context(model=CodeSystem, url_prefix="widgets", openapi_tag=None)
        merged = gen.merge_openapi_constant_into_constants("", ctx)
        self.assertIn("OPENAPI_TAG_TERMINOLOGY_WIDGETS", merged)
        self.assertIn("'widgets'", merged)
        again = gen.merge_openapi_constant_into_constants(merged, ctx)
        self.assertEqual(again, merged)

    def test_merge_package_init_py_idempotent(self) -> None:
        CodeSystem = apps.get_model("terminology", "CodeSystem")
        ctx = gen.build_context(model=CodeSystem, url_prefix="code-systems", openapi_tag=None)
        names = gen.api_export_names(ctx)
        text = gen.render_init_py(from_module="policy", export_names=names)
        again = gen.merge_package_init_py(
            text,
            from_module="policy",
            export_names=names,
        )
        self.assertEqual(again.rstrip(), text.rstrip())

    def test_full_blueprint_more_endpoints_than_core_nine(self) -> None:
        CodeSystem = apps.get_model("terminology", "CodeSystem")
        ctx = gen.build_context(
            model=CodeSystem,
            url_prefix="code-systems",
            openapi_tag=None,
            with_history_extras=True,
            with_crud_audit=True,
            rich_serializers=True,
        )
        self.assertGreater(len(gen.api_export_names(ctx)), 9)
        apis = gen.render_apis_py(ctx)
        self.assertIn("HistoryDiffApi", apis)
        self.assertIn("ObjectCrudAuditListApi", apis)
        self.assertIn("get_code_system(", apis)
