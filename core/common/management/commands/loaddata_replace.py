"""
Load fixtures idempotently: delete rows that would conflict, then run loaddata.

Re-run safe on shared dev DBs where ``flush`` is not an option. Clears rows
matching fixture PKs and model unique constraints (e.g. pricing package items
with the same package + charge item definition but a different PK).
"""

from pathlib import Path

from django.conf import settings
from django.core import serializers
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.management.commands.loaddata import READ_STDIN
from django.core.management.commands.loaddata import Command as LoaddataCommand
from django.db import DEFAULT_DB_ALIAS, transaction

from core.common.fixtures.idempotent import (
    collect_entries_from_files,
    load_fixture_files,
    replace_fixture_rows,
)


class Command(BaseCommand):
    help = (
        "Load fixtures after removing conflicting rows (PK + unique constraints). "
        "Safe to re-run on a non-empty database."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("args", metavar="fixture", nargs="+", help="Fixture labels.")
        parser.add_argument(
            "--database",
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to load fixtures into. Defaults to "default".',
        )
        parser.add_argument(
            "--app",
            dest="app_label",
            help="Only look for fixtures in the specified app.",
        )
        parser.add_argument(
            "--ignorenonexistent",
            "-i",
            action="store_true",
            dest="ignore",
            help="Ignore fixture fields that do not exist on the model.",
        )
        parser.add_argument(
            "-e",
            "--exclude",
            action="append",
            default=[],
            help="An app_label or app_label.ModelName to exclude (repeatable).",
        )
        parser.add_argument(
            "--format",
            help="Format of serialized data when reading from stdin.",
        )
        parser.add_argument(
            "--no-replace",
            action="store_true",
            help="Skip preloaded row removal (equivalent to stock loaddata).",
        )

    def handle(self, *fixture_labels, **options) -> None:
        using = options["database"]
        loaddata_kwargs = {
            "database": using,
            "verbosity": options["verbosity"],
            "app_label": options["app_label"],
            "ignore": options["ignore"],
            "exclude": options["exclude"],
            "format": options["format"],
        }

        if options["no_replace"]:
            call_command("loaddata", *fixture_labels, **loaddata_kwargs)
            return

        if READ_STDIN in fixture_labels:
            self.stderr.write(self.style.ERROR("stdin fixtures are not supported for loaddata_replace"))
            return

        fixture_files = self._resolve_fixture_files(fixture_labels, options)
        if not fixture_files:
            call_command("loaddata", *fixture_labels, **loaddata_kwargs)
            return

        entries_by_model = collect_entries_from_files(fixture_files)

        with transaction.atomic(using=using):
            replace_fixture_rows(
                entries_by_model=entries_by_model,
                using=using,
                verbosity=options["verbosity"],
                log=self.stdout.write,
            )
            load_fixture_files(
                fixture_files=fixture_files,
                entries_by_model=entries_by_model,
                using=using,
                ignorenonexistent=options["ignore"],
                verbosity=options["verbosity"],
                log=self.stdout.write,
            )

    def _resolve_fixture_files(self, fixture_labels, options) -> list[str]:
        base_dir = Path(settings.BASE_DIR)
        loaddata_cmd = LoaddataCommand()
        loaddata_cmd.using = options["database"]
        loaddata_cmd.verbosity = options["verbosity"]
        loaddata_cmd.app_label = options["app_label"]
        loaddata_cmd.format = options["format"]
        loaddata_cmd.ignore = options["ignore"]
        loaddata_cmd.serialization_formats = serializers.get_public_serializer_formats()

        paths: list[str] = []
        seen: set[str] = set()
        for label in fixture_labels:
            direct_path = base_dir / label
            if direct_path.is_file():
                resolved = str(direct_path.resolve())
                if resolved not in seen:
                    seen.add(resolved)
                    paths.append(resolved)
                continue

            for fixture_file, _, _ in loaddata_cmd.find_fixtures(label):
                if fixture_file in seen:
                    continue
                seen.add(fixture_file)
                paths.append(fixture_file)
        return paths
