import pytest
from django.http import Http404

from core.cookbook.selectors import recipe_get, recipe_list
from core.cookbook.services import recipe_create
from core.security.testing import grant_permissions
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
class RecipeSelectorTests:
    def test_non_staff_sees_own_only(self):
        owner = _user(username="sel_a", email="sel_a@example.com", phone=251911000211)
        other = _user(username="sel_b", email="sel_b@example.com", phone=251911000212)
        mine = recipe_create(title="Mine", created_by=owner)
        recipe_create(title="Theirs", created_by=other)
        qs = recipe_list(requesting_user=owner)
        assert list(qs.values_list("id", flat=True)) == [mine.id]

    def test_staff_sees_all(self):
        owner = _user(username="sel_c", email="sel_c@example.com", phone=251911000213)
        staff = _user(username="sel_staff", email="sel_staff@example.com", phone=251911000214, staff=True)
        recipe_create(title="Visible to staff", created_by=owner)
        qs = recipe_list(requesting_user=staff)
        assert qs.count() == 1

    def test_list_all_permission_sees_all(self):
        owner = _user(username="sel_g", email="sel_g@example.com", phone=251911000218)
        reviewer = _user(username="sel_rev", email="sel_rev@example.com", phone=251911000219)
        grant_permissions(user=reviewer, codes=["cookbook:recipe:list_all"])
        recipe_create(title="Visible with list_all", created_by=owner)
        qs = recipe_list(requesting_user=reviewer)
        assert qs.count() == 1

    def test_non_owner_get_404(self):
        owner = _user(username="sel_d", email="sel_d@example.com", phone=251911000215)
        other = _user(username="sel_e", email="sel_e@example.com", phone=251911000216)
        recipe = recipe_create(title="Hidden", created_by=owner)
        with pytest.raises(Http404):
            recipe_get(recipe_id=recipe.id, requesting_user=other)

    def test_filter_status(self):
        owner = _user(username="sel_f", email="sel_f@example.com", phone=251911000217)
        recipe_create(title="Draft only", created_by=owner)
        qs = recipe_list(filters={"status": "draft", "title": "Draft"}, requesting_user=owner)
        assert qs.count() == 1
