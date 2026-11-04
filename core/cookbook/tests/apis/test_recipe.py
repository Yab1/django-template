import pytest
from rest_framework.test import APIClient

from core.cookbook.models import Recipe
from core.cookbook.services import recipe_create
from core.security.testing import grant_permissions
from core.users.models import User

_COOKBOOK_WRITE = (
    "cookbook:recipe:create",
    "cookbook:recipe:list",
    "cookbook:recipe:get",
    "cookbook:recipe:update",
    "cookbook:recipe:delete",
    "cookbook:recipe:publish",
)

_URL = "/api/v1/cookbook/recipes/"


def _user(*, username: str, email: str, phone: int) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password="NotAWeakPassw0rd!",
        phone_number=phone,
    )


@pytest.mark.django_db
class RecipeApiTests:
    def setup_method(self):
        self.client = APIClient()
        self.user = _user(username="api_cook", email="api_cook@example.com", phone=251911000221)
        grant_permissions(user=self.user, codes=_COOKBOOK_WRITE)
        self.client.force_authenticate(user=self.user)

    def test_create_list_get_update_publish_delete(self):
        create = self.client.post(f"{_URL}create/", {"title": "Misir wot", "body": "Red lentils"}, format="json")
        assert create.status_code == 201
        body = create.json()["result"]
        assert body["status"] == Recipe.Status.DRAFT
        assert body["created_by_id"] == str(self.user.id)
        assert body["updated_by_id"] == str(self.user.id)
        recipe_id = body["id"]

        listed = self.client.get(_URL)
        assert listed.status_code == 200
        assert listed.json()["result"]["count"] == 1
        hidden = self.client.get(_URL, {"is_visible": "false"})
        assert hidden.status_code == 200
        assert hidden.json()["result"]["count"] == 0

        got = self.client.get(f"{_URL}{recipe_id}/")
        assert got.status_code == 200
        assert got.json()["result"]["title"] == "Misir wot"

        updated = self.client.patch(
            f"{_URL}{recipe_id}/update/",
            {"title": "Misir wot spicy"},
            format="json",
        )
        assert updated.status_code == 200
        assert updated.json()["result"]["title"] == "Misir wot spicy"
        assert updated.json()["result"]["updated_by_id"] == str(self.user.id)

        published = self.client.post(f"{_URL}{recipe_id}/publish/")
        assert published.status_code == 200
        assert published.json()["result"]["status"] == Recipe.Status.PUBLISHED

        again = self.client.post(f"{_URL}{recipe_id}/publish/")
        assert again.status_code == 400

        deleted = self.client.delete(f"{_URL}{recipe_id}/")
        assert deleted.status_code == 200
        missing = self.client.get(f"{_URL}{recipe_id}/")
        assert missing.status_code == 404

    def test_other_user_cannot_get(self):
        owner = _user(username="api_owner", email="api_owner@example.com", phone=251911000222)
        recipe = recipe_create(title="Private", created_by=owner)
        response = self.client.get(f"{_URL}{recipe.id}/")
        assert response.status_code == 404

    def test_forbidden_without_permission(self):
        stranger = _user(username="api_none", email="api_none@example.com", phone=251911000223)
        self.client.force_authenticate(user=stranger)
        response = self.client.post(f"{_URL}create/", {"title": "Nope"}, format="json")
        assert response.status_code == 403
