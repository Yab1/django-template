"""Tests for Postman terminology fixture resolution."""

from django.test import TestCase

from core.common.management.postman.terminology import TerminologyResolver


class PostmanTerminologyResolverTests(TestCase):
    def test_charge_item_status_id_maps_to_planned_fixture(self) -> None:
        resolver = TerminologyResolver.for_app("billing")
        binding = resolver.bind_field("status_id", resource_folder="charge_item")
        self.assertIsNotNone(binding)
        assert binding is not None
        self.assertEqual(binding.constant_name, "CHARGE_ITEM_STATUS_CODESYSTEM_URL")
        self.assertEqual(binding.concept.code, "planned")
        self.assertEqual(
            binding.concept.fixture_path,
            "core/terminology/fixtures/charge_item_status/code_system.json",
        )

    def test_body_var_ref_uses_direct_concept_pk(self) -> None:
        resolver = TerminologyResolver.for_app("billing")
        refs = resolver.body_var_refs({"status_id"}, resource_folder="charge_item")
        # body_var_refs now returns direct Concept.pk (same as response_fixture_values)
        self.assertIn("status_id", refs)
        self.assertNotIn("{{", refs["status_id"])

    def test_collection_default_uses_concept_pk(self) -> None:
        resolver = TerminologyResolver.for_app("billing")
        defaults = resolver.collection_defaults({"status_id"}, resource_folder="charge_item")
        self.assertIn("status_id", defaults)
        self.assertEqual(defaults["status_id"]["value"], "49327613-3bbf-47c8-ba39-e5203de59e53")
        self.assertIn("CHARGE_ITEM_STATUS_CODESYSTEM_URL", defaults["status_id"]["description"])

    def test_code_system_status_id_from_terminology_app(self) -> None:
        resolver = TerminologyResolver.for_app("terminology")
        binding = resolver.bind_field("status_id", resource_folder="code_system")
        self.assertIsNotNone(binding)

    def test_accession_model_only_exposes_concept_fk_fields(self) -> None:
        from core.common.management.postman.introspection import concept_id_fields_from_view
        from core.common.management.postman.model_fields import (
            concept_id_field_names_for_model,
            filter_terminology_concept_fields,
            resolve_model_for_resource,
        )
        from core.lab.models import Accession

        model = resolve_model_for_resource("lab", "accession")
        self.assertIs(model, Accession)
        concept_names = concept_id_field_names_for_model(Accession)
        self.assertEqual(concept_names, frozenset({"status_id", "priority_id"}))

        filtered = filter_terminology_concept_fields(
            {
                "status_id",
                "priority_id",
                "performing_location_id",
                "patient_id",
                "accession_history_id",
            },
            app_label="lab",
            resource_folder="accession",
        )
        self.assertEqual(filtered, {"status_id", "priority_id"})

        from core.lab.apis.accession.crud import AccessionCreateApi

        view_fields = concept_id_fields_from_view(
            AccessionCreateApi,
            app_label="lab",
            resource_folder="accession",
        )
        self.assertEqual(view_fields, {"status_id", "priority_id"})
