"""
Scaffold per-resource `serializers.py` modules from the discovered model context.

This follows the same model resolution pattern as `scaffold_standard_api`, but
only writes serializer modules.
"""

import importlib
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from core.common.management import scaffold_standard_api_generator as base_gen
from core.common.management import scaffold_standard_serializers_generator as ser_gen


def _resolve_app_label(raw: str) -> str:
    key = raw.strip()
    try:
        return apps.get_app_config(key).label
    except LookupError:
        pass

    lowered = key.lower()
    for app_config in apps.get_app_configs():
        if app_config.label.lower() == lowered:
            return app_config.label
    raise LookupError(key)


class Command(BaseCommand):
    requires_system_checks: list[str] = []

    help = (
        "Generate per-resource serializer modules using the same model context as the standard API scaffold. "
        "Examples:\n"
        "  python manage.py scaffold_standard_serializers individuals.PractitionerRole\n"
        "  python manage.py scaffold_standard_serializers individuals"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "target",
            nargs="?",
            type=str,
            help=(
                "App label (e.g. individuals) to scaffold every REST resource in that app "
                "(models with apis/<resource>/), or "
                '"app_label.ModelName" (e.g. individuals.Patient) for a single resource. '
                "The --all flag is optional when the target is already an app label."
            ),
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help=(
                "Generate serializers for every REST resource in the target app. "
                "Redundant when target is an app label only; still useful with app_label.ModelName "
                "to scaffold the whole app instead of one model."
            ),
        )
        parser.add_argument("--url-prefix", type=str, default=None, help="Reserved for parity with the API scaffold.")
        parser.add_argument("--openapi-tag", type=str, default=None, help="Reserved for parity with the API scaffold.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print paths that would be written; do not modify files.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite generated serializer modules if they already exist.",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        force: bool = options["force"]
        all_mode: bool = options["all"]
        target: str | None = options["target"]

        if not target:
            raise CommandError("target is required (app label or app_label.ModelName)")

        if all_mode or "." not in target:
            self._render_app(target=target, dry_run=dry_run, force=force)
            return

        app_label_raw, model_name = target.split(".", 1)
        app_label = _resolve_app_label(app_label_raw)
        try:
            model_cls = apps.get_model(app_label, model_name)
        except LookupError as exc:
            raise CommandError(f"Unknown model {target!r}") from exc
        self._render_one(model_cls=model_cls, dry_run=dry_run, force=force)

    def _iter_app_resource_models(self, app_label: str) -> list[type]:
        """Concrete models in ``app_label`` that have their own ``apis/<resource>/`` package.

        App-wide serializer scaffold targets first-class REST resources only — not
        django-simple-history ``Historical*`` rows and not cascade-owned child models
        (``PatientAddress``, ``PractitionerName``, …) that are inlined on the parent
        resource serializer.
        """
        return [
            model
            for model in apps.get_app_config(app_label).get_models()
            if not model._meta.abstract
            and not model._meta.proxy
            and not model.__name__.startswith("Historical")
            and base_gen._child_has_own_apis_module(model)
        ]

    def _render_app(self, *, target: str, dry_run: bool, force: bool) -> None:
        app_label = self._resolve_target_app(target)
        model_classes = self._iter_app_resource_models(app_label)
        if not model_classes:
            raise CommandError(
                f"No scaffoldable REST resources found for app {app_label!r} "
                "(expected models with core/{app}/apis/<resource>/)."
            )
        self.stdout.write(
            self.style.NOTICE(
                f"Scaffolding serializers for app {app_label} ({len(model_classes)} resources: "
                f"{', '.join(m.__name__ for m in sorted(model_classes, key=lambda c: c.__name__))})"
            )
        )
        for model_cls in model_classes:
            self._render_one(model_cls=model_cls, dry_run=dry_run, force=force)

    def _resolve_target_app(self, target: str) -> str:
        if "." in target:
            app_label_raw, _ = target.split(".", 1)
            return _resolve_app_label(app_label_raw)
        return _resolve_app_label(target)

    def _render_one(self, *, model_cls, dry_run: bool, force: bool) -> None:
        app_config = apps.get_app_config(model_cls._meta.app_label)
        models_mod = importlib.import_module(f"{app_config.name}.models")
        if getattr(models_mod, model_cls.__name__, None) is not model_cls:
            raise CommandError(
                f"Model {model_cls.__name__} must be exported from {app_config.name}.models "
                "(import it in models/__init__.py if it lives in a submodule)."
            )

        models_file = Path(models_mod.__file__).resolve()
        app_dir = models_file.parent.parent if models_file.name != "models.py" else models_file.parent
        try:
            ctx = base_gen.build_context(
                model=model_cls,
                url_prefix=None,
                openapi_tag=None,
                with_history_extras=True,
                with_crud_audit=True,
                rich_serializers=True,
                with_filters=True,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        files = ser_gen.collect_generated_files(ctx, app_dir=app_dir)
        for path, content in files.items():
            self._write_text(path, content, dry_run=dry_run, force=force)

        compacts_path = app_dir / "serializers" / "compacts.py"
        self._merge_serializers_compacts(compacts_path, ctx, dry_run=dry_run)

    def _merge_serializers_compacts(self, path: Path, ctx, *, dry_run: bool) -> None:
        existing = path.read_text() if path.exists() else ""
        merged = ser_gen.merge_compacts_py(existing, ctx)
        if merged.rstrip() == existing.rstrip():
            self.stdout.write(
                self.style.NOTICE(f"  skip {path} ({ctx.model_name}CompactSerializer already in compacts)")
            )
            return
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"  would merge {path} (serializers.compacts)"))
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(merged if merged.endswith("\n") else merged + "\n")
        self.stdout.write(self.style.SUCCESS(f"  merged {path}"))

    def _write_text(self, path: Path, content: str, *, dry_run: bool, force: bool) -> None:
        if dry_run:
            self.stdout.write(self.style.NOTICE(f"  would write {path}"))
            return
        if path.exists() and not force:
            self.stdout.write(self.style.WARNING(f"  skip existing {path} (use --force to overwrite)"))
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        self.stdout.write(self.style.SUCCESS(f"  wrote {path}"))
