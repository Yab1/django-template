"""
Generate Postman Collection v2.1 JSON from Django URL patterns for a core app.

Conventions: .cursor/rules/postman.mdc and docs/external/postman/variables-list.md

Examples:
  python manage.py generate_postman_collection terminology
  python manage.py generate_postman_collection billing --resource charge_item
  python manage.py generate_postman_collection billing --resource charge_item --category crud --category action
  python manage.py generate_postman_collection billing --list-resources
  python manage.py generate_postman_collection billing --list-routes
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.urls import URLResolver

import core.api.urls as api_urls
from core.common.management.postman import (
    GenerationOptions,
    TerminologyResolver,
    build_collection,
    build_manifest,
    collection_to_json,
    concept_id_fields_from_view,
    default_output_path,
    discover_routes,
    list_resources,
    list_routes_table,
    merge_collections,
)


def _mounted_app_labels() -> list[str]:
    labels: list[str] = []
    for pattern in api_urls.urlpatterns:
        if not isinstance(pattern, URLResolver):
            continue
        urlconf = pattern.urlconf_name
        if isinstance(urlconf, tuple):
            mod_name = urlconf[0]
        else:
            mod_name = getattr(urlconf, "__name__", str(urlconf))
        if mod_name.startswith("core.") and mod_name.endswith(".urls"):
            labels.append(mod_name.split(".")[1])
    return sorted(set(labels))


class Command(BaseCommand):
    help = (
        "Generate Postman Collection JSON by introspecting core.<app_label>.urls. "
        "Supports per-resource output, endpoint categories, saved response examples, and merge mode."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            nargs="?",
            type=str,
            default=None,
            help="Django app label under core/ (e.g. terminology, billing). Omit with --all-apps.",
        )
        parser.add_argument("--output", "-o", type=str, default=None, help="Output file path.")
        parser.add_argument("--name", type=str, default=None, help="Collection display name.")
        parser.add_argument("--resource", "-r", action="append", default=None, help="Limit to resource(s). Repeatable.")
        parser.add_argument(
            "--category",
            "-c",
            action="append",
            default=None,
            help="Include only categories: crud, bulk, history, audit, action, capability, misc.",
        )
        parser.add_argument(
            "--exclude-category",
            action="append",
            default=None,
            help="Exclude categories. Repeatable.",
        )
        parser.add_argument("--list-resources", action="store_true", help="List discoverable resources and exit.")
        parser.add_argument("--list-routes", action="store_true", help="List routes table and exit.")
        parser.add_argument("--dry-run", action="store_true", help="Print summary; do not write files.")
        parser.add_argument("--merge", action="store_true", help="Merge into an existing collection file when present.")
        parser.add_argument(
            "--refresh-responses",
            action="store_true",
            help="When merging, replace saved response examples.",
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="When merging, add only requests that do not already exist.",
        )
        parser.add_argument("--skip-responses", action="store_true", help="Do not generate saved response examples.")
        parser.add_argument("--skip-scripts", action="store_true", help="Do not generate test scripts.")
        parser.add_argument(
            "--skip-terminology",
            action="store_true",
            help="Do not resolve terminology fixture defaults for collection variables.",
        )
        parser.add_argument(
            "--terminology-report",
            action="store_true",
            help="Print Concept *_id fields that could not be mapped to fixture UUIDs (implies --dry-run).",
        )
        parser.add_argument("--stable-id", action="store_true", help="Use deterministic collection _postman_id.")
        parser.add_argument("--pr", type=str, default=None, help="PR prefix for collection name (PR-<id> - ...).")
        parser.add_argument(
            "--auth",
            choices=("user", "admin"),
            default="user",
            help="Default bearer token variable for all requests.",
        )
        parser.add_argument(
            "--generate-environment",
            action="store_true",
            help="Also write a Postman environment JSON next to the collection.",
        )
        parser.add_argument(
            "--manifest",
            action="store_true",
            help="Write postman/.generated/manifest.json summarizing outputs.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit with error when generation emits warnings.",
        )
        parser.add_argument(
            "--all-apps",
            action="store_true",
            help="Generate collections for every app mounted in core.api.urls.",
        )

    def handle(self, *args, **options):
        if options["all_apps"]:
            if options["app_label"]:
                raise CommandError("Do not pass app_label with --all-apps.")
            manifest_entries: list[dict] = []
            for app_label in _mounted_app_labels():
                if app_label in {"playground"}:
                    continue
                manifest_entries.extend(self._generate_for_app(app_label, options))
            if options["manifest"] and manifest_entries:
                self._write_manifest(app_label="all", outputs=manifest_entries)
            return

        app_label = (options["app_label"] or "").strip()
        if not app_label:
            raise CommandError("app_label is required unless --all-apps is set.")

        outputs = self._generate_for_app(app_label, options)
        if options["manifest"] and outputs:
            self._write_manifest(app_label=app_label, outputs=outputs)

    def _generate_for_app(self, app_label: str, options: dict) -> list[dict]:
        try:
            _segment, routes = discover_routes(app_label)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        except ImportError as exc:
            raise CommandError(f"Cannot import urls for app {app_label!r}: {exc}") from exc

        if options["list_resources"]:
            for resource in list_resources(routes):
                self.stdout.write(resource)
            return []

        if options["list_routes"]:
            for row in list_routes_table(routes):
                self.stdout.write(
                    f"{row['resource']}\t{row['category']}\t{row['method']}\t{row['url_name']}\t{row['path']}"
                )
            return []

        if options["terminology_report"]:
            resolver = TerminologyResolver.for_app(app_label)
            by_resource: dict[str, set[str]] = {}
            for route in routes:
                bucket = by_resource.setdefault(route.resource_folder, set())
                if route.view_class is not None:
                    bucket.update(
                        concept_id_fields_from_view(
                            route.view_class,
                            app_label=app_label,
                            resource_folder=route.resource_folder,
                        )
                    )
            for resource_folder, field_names in sorted(by_resource.items()):
                bindings = resolver.bind_fields(field_names, resource_folder=resource_folder)
                unbound = resolver.unbound_concept_id_fields(field_names, resource_folder=resource_folder)
                self.stdout.write(
                    self.style.NOTICE(f"[{resource_folder}] bound={len(bindings)} unbound={len(unbound)}")
                )
                for field_name, binding in sorted(bindings.items()):
                    self.stdout.write(
                        f"  {field_name} -> {binding.concept.pk} ({binding.concept.code}) via {binding.constant_name}"
                    )
                for field_name in unbound:
                    self.stdout.write(self.style.WARNING(f"  {field_name} -> (no fixture)"))
            return []

        resource_targets = options["resource"] or [None]
        outputs: list[dict] = []

        for resource in resource_targets:
            collection_name = options["name"]
            if not collection_name:
                collection_name = resource.replace("_", " ") if resource else app_label
            collection_name = collection_name.strip().lower()

            gen_options = GenerationOptions(
                app_label=app_label,
                collection_name=collection_name,
                resources={resource} if resource else None,
                categories=set(options["category"]) if options["category"] else None,
                exclude_categories=set(options["exclude_category"]) if options["exclude_category"] else None,
                skip_responses=options["skip_responses"],
                skip_scripts=options["skip_scripts"],
                skip_terminology=options["skip_terminology"],
                merge=options["merge"],
                refresh_responses=options["refresh_responses"],
                only_missing=options["only_missing"],
                stable_id=options["stable_id"],
                pr_prefix=options["pr"],
                per_resource_file=bool(resource),
                generate_environment=options["generate_environment"],
                write_manifest=options["manifest"],
                strict=options["strict"],
                auth_default=options["auth"],
            )

            result = build_collection(routes=routes, options=gen_options)
            if result.request_count == 0:
                self.stdout.write(self.style.WARNING(f"No requests matched filters for app {app_label!r}."))
                continue

            for warning in result.warnings:
                line = warning.message if not warning.url_name else f"{warning.url_name}: {warning.message}"
                self.stdout.write(self.style.WARNING(line))
            if options["strict"] and result.warnings:
                raise CommandError("Generation completed with warnings (--strict).")

            if options["dry_run"]:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Would generate {result.request_count} requests for app {app_label!r}"
                        + (f" resource {resource!r}" if resource else "")
                        + "."
                    )
                )
                if result.collection["item"]:
                    first_folder = result.collection["item"][0]
                    while "item" in first_folder and first_folder["item"] and "request" not in first_folder["item"][0]:
                        first_folder = first_folder["item"][0]
                    if first_folder.get("item"):
                        req = first_folder["item"][0]["request"]
                        self.stdout.write(f"  Example: {req['method']} {req['url']['raw']}")
                continue

            output_path = options["output"]
            if output_path and len(resource_targets) > 1:
                raise CommandError("Use --output only when generating a single target.")
            if not output_path:
                output_path = default_output_path(app_label=app_label, resource=resource)

            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)

            collection = result.collection
            if options["merge"] and out.exists():
                existing = json.loads(out.read_text(encoding="utf-8"))
                collection = merge_collections(
                    existing,
                    collection,
                    refresh_responses=options["refresh_responses"],
                    only_missing=options["only_missing"],
                )

            out.write_text(collection_to_json(collection), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Wrote {out} ({result.request_count} requests)."))
            outputs.append({
                "path": str(out),
                "request_count": result.request_count,
                "resource": resource,
            })

            if result.environment is not None:
                env_path = out.with_suffix(".postman_environment.json")
                env_path.write_text(json.dumps(result.environment, indent=2) + "\n", encoding="utf-8")
                self.stdout.write(self.style.SUCCESS(f"Wrote {env_path}."))

        return outputs

    def _write_manifest(self, *, app_label: str, outputs: list[dict]) -> None:
        manifest_dir = Path("postman") / ".generated"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = manifest_dir / "manifest.json"
        payload = build_manifest(app_label=app_label, outputs=outputs)
        manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {manifest_path}."))
