def register_cookbook_file_targets() -> None:
    from core.cookbook.constants import FIELD_FILE, RESOURCE_RECIPE
    from core.cookbook.models import Recipe
    from core.files.targets import FileTarget, register_file_target

    register_file_target(
        FileTarget(resource=RESOURCE_RECIPE, field=FIELD_FILE, model=Recipe, replace=False),
    )
