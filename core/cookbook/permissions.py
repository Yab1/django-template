from core.security.registry import register_permission


def register_cookbook_permissions() -> None:
    register_permission(code="cookbook:recipe:create", name="Create recipe")
    register_permission(code="cookbook:recipe:list", name="List own recipes")
    register_permission(code="cookbook:recipe:list_all", name="List all recipes")
    register_permission(code="cookbook:recipe:get", name="Get recipe")
    register_permission(code="cookbook:recipe:update", name="Update recipe")
    register_permission(code="cookbook:recipe:delete", name="Delete recipe")
    register_permission(code="cookbook:recipe:publish", name="Publish recipe")
