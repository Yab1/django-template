from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404

from core.cookbook.models import Recipe
from core.cookbook.services import (
    recipe_after_publish,
    recipe_create,
    recipe_delete,
    recipe_publish,
    recipe_update,
)
from core.cookbook.tasks import recipe_published_task
from core.files.models import FileObject
from core.files.services import file_object_create
from core.users.models import User


def _user(*, username: str, email: str, phone: int, staff: bool = False) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password="NotAWeakPassw0rd!",
        phone_number=phone,
        is_staff=staff,
        is_superuser=staff,
    )


@pytest.mark.django_db
class RecipeServiceTests:
    def test_create_starts_as_draft(self):
        owner = _user(username="cook_a", email="cook_a@example.com", phone=251911000201)
        recipe = recipe_create(title="Injera", body="Teh", created_by=owner)
        assert recipe.status == Recipe.Status.DRAFT
        assert recipe.created_by_id == owner.id
        assert recipe.updated_by_id == owner.id
        assert recipe.reference_id.startswith("DT-RCP-")

    def test_publish_draft(self, django_capture_on_commit_callbacks):
        owner = _user(username="cook_b", email="cook_b@example.com", phone=251911000202)
        recipe = recipe_create(title="Doro", created_by=owner)
        with patch("core.cookbook.services.recipe.recipe_published_task.delay") as delay:
            with django_capture_on_commit_callbacks(execute=True):
                published = recipe_publish(recipe_id=recipe.id, requesting_user=owner)
        assert published.status == Recipe.Status.PUBLISHED
        delay.assert_called_once_with(str(recipe.id))

    def test_after_publish_stamps_metadata(self):
        owner = _user(username="cook_b2", email="cook_b2@example.com", phone=251911000212)
        recipe = recipe_create(title="Doro async", created_by=owner)
        with patch("core.cookbook.services.recipe.recipe_published_task.delay"):
            recipe_publish(recipe_id=recipe.id, requesting_user=owner)
        updated = recipe_after_publish(recipe_id=recipe.id)
        assert updated.metadata.get("published_at")

    def test_published_task_calls_service(self):
        owner = _user(username="cook_b3", email="cook_b3@example.com", phone=251911000213)
        recipe = recipe_create(title="Doro task", created_by=owner)
        with patch("core.cookbook.services.recipe.recipe_published_task.delay"):
            recipe_publish(recipe_id=recipe.id, requesting_user=owner)
        recipe_published_task(str(recipe.id))
        recipe.refresh_from_db()
        assert recipe.metadata.get("published_at")

    def test_publish_twice_rejected(self):
        owner = _user(username="cook_c", email="cook_c@example.com", phone=251911000203)
        recipe = recipe_create(title="Shiro", created_by=owner)
        with patch("core.cookbook.services.recipe.recipe_published_task.delay"):
            recipe_publish(recipe_id=recipe.id, requesting_user=owner)
            with pytest.raises(ValidationError):
                recipe_publish(recipe_id=recipe.id, requesting_user=owner)

    def test_update_does_not_change_status(self):
        owner = _user(username="cook_d", email="cook_d@example.com", phone=251911000204)
        recipe = recipe_create(title="Kitfo", created_by=owner)
        updated = recipe_update(
            recipe_id=recipe.id,
            data={"title": "Kitfo special", "status": Recipe.Status.PUBLISHED},
            requesting_user=owner,
        )
        assert updated.title == "Kitfo special"
        assert updated.status == Recipe.Status.DRAFT
        assert updated.updated_by_id == owner.id

    def test_delete_soft(self):
        owner = _user(username="cook_e", email="cook_e@example.com", phone=251911000205)
        recipe = recipe_create(title="Tibs", created_by=owner)
        recipe_delete(recipe_id=recipe.id, requesting_user=owner)
        recipe.refresh_from_db()
        assert recipe.deleted_at is not None
        with pytest.raises(Http404):
            recipe_publish(recipe_id=recipe.id, requesting_user=owner)

    def test_owner_can_attach_file(self):
        owner = _user(username="cook_f", email="cook_f@example.com", phone=251911000206)
        recipe = recipe_create(title="Photo stew", created_by=owner)
        row = file_object_create(
            user=owner,
            upload=SimpleUploadedFile("note.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
            resource="recipe",
            field="file",
            object_id=recipe.id,
        )
        assert row.resource == "recipe"
        assert row.content_type.app_label == "cookbook"
        assert row.content_type.model == "recipe"
        assert FileObject.objects.filter(pk=row.id).count() == 1

    def test_non_owner_cannot_attach_file(self):
        owner = _user(username="cook_g", email="cook_g@example.com", phone=251911000207)
        other = _user(username="cook_h", email="cook_h@example.com", phone=251911000208)
        recipe = recipe_create(title="Secret stew", created_by=owner)
        with pytest.raises(ValidationError):
            file_object_create(
                user=other,
                upload=SimpleUploadedFile("note.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
                resource="recipe",
                field="file",
                object_id=recipe.id,
            )
