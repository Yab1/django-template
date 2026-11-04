from typing import Any
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.common.services import model_update
from core.cookbook.models import Recipe
from core.cookbook.selectors.recipe import recipe_get
from core.cookbook.tasks import recipe_published_task
from core.users.models import User

_RECIPE_UPDATE_FIELDS = ["title", "body", "is_visible", "metadata"]


def recipe_create(*, title: str, body: str = "", created_by: User) -> Recipe:
    obj = Recipe(
        title=title,
        body=body or "",
        created_by=created_by,
        updated_by=created_by,
        status=Recipe.Status.DRAFT,
    )
    obj.full_clean()
    obj.save()
    return obj


@transaction.atomic
def recipe_update(*, recipe_id: UUID, data: dict[str, Any], requesting_user: User) -> Recipe:
    obj = recipe_get(recipe_id=recipe_id, requesting_user=requesting_user)
    obj, _ = model_update(
        instance=obj,
        fields=[*_RECIPE_UPDATE_FIELDS, "updated_by"],
        data={**data, "updated_by": requesting_user},
    )
    return obj


def recipe_delete(*, recipe_id: UUID, requesting_user: User) -> Recipe:
    obj = recipe_get(recipe_id=recipe_id, requesting_user=requesting_user)
    obj.delete(user=requesting_user)
    return obj


@transaction.atomic
def recipe_publish(*, recipe_id: UUID, requesting_user: User) -> Recipe:
    obj = recipe_get(recipe_id=recipe_id, requesting_user=requesting_user)
    if obj.status == Recipe.Status.PUBLISHED:
        raise ValidationError({"status": "Recipe is already published."})
    if obj.status != Recipe.Status.DRAFT:
        raise ValidationError({"status": "Only a draft recipe can be published."})
    obj.status = Recipe.Status.PUBLISHED
    obj.updated_by = requesting_user
    obj.full_clean()
    obj.save(update_fields=["status", "updated_by", "updated_at"])
    published_id = str(obj.id)
    transaction.on_commit(lambda: recipe_published_task.delay(published_id))
    return obj


def recipe_after_publish(*, recipe_id: UUID) -> Recipe:
    """
    Async work after a recipe is published. Runs in Celery.

    Cookbook only stamps metadata so the path is testable. A real app
    sends mail, writes a ledger line, or kicks the next domain service.
    """
    obj = Recipe.objects.get(pk=recipe_id)
    if obj.status != Recipe.Status.PUBLISHED:
        return obj
    metadata = dict(obj.metadata or {})
    metadata["published_at"] = timezone.now().isoformat()
    obj.metadata = metadata
    obj.save(update_fields=["metadata", "updated_at"])
    return obj
