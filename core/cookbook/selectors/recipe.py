from uuid import UUID

from django.db.models import QuerySet
from django.http import Http404

from core.cookbook.filters import RecipeFilter
from core.cookbook.models import Recipe
from core.security.services import user_has_permission
from core.users.models import User

_LIST_FILTER_KEYS = frozenset({"status", "is_visible", "title", "order_by"})


def _visible_qs(*, requesting_user: User) -> QuerySet[Recipe]:
    qs = Recipe.objects.filter(deleted_at__isnull=True)
    if user_has_permission(user=requesting_user, action="cookbook:recipe:list_all"):
        return qs
    return qs.filter(created_by=requesting_user)


def recipe_get(*, recipe_id: UUID, requesting_user: User) -> Recipe:
    try:
        return _visible_qs(requesting_user=requesting_user).get(pk=recipe_id)
    except Recipe.DoesNotExist as exc:
        raise Http404("Recipe not found.") from exc


def recipe_list(*, filters: dict | None = None, requesting_user: User) -> QuerySet[Recipe]:
    raw = dict(filters or {})
    cleaned = {key: value for key, value in raw.items() if key in _LIST_FILTER_KEYS and value not in (None, "")}
    return RecipeFilter(cleaned, _visible_qs(requesting_user=requesting_user)).qs
