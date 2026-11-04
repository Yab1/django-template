import pytest
from django.core.exceptions import ValidationError

from core.security.models import UserRole
from core.security.services import role_create, role_update, user_role_assign, user_role_revoke
from core.security.testing import grant_permissions
from core.users.models import User


def _user(*, username: str, email: str, phone: int) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password="NotAWeakPassw0rd!",
        phone_number=phone,
    )


@pytest.mark.django_db
class RoleServiceTests:
    def test_create_with_codes_and_assign(self):
        user = _user(username="sec_role_a", email="sec_role_a@example.com", phone=251911000311)
        role = role_create(
            code="cookbook_author",
            name="Cookbook author",
            permission_codes=["cookbook:recipe:create", "cookbook:recipe:list"],
        )
        assert role.reference_id.startswith("DT-ROL-")
        assert set(role.permissions.values_list("code", flat=True)) == {
            "cookbook:recipe:create",
            "cookbook:recipe:list",
        }
        user_role_assign(user=user, role=role)
        assert UserRole.objects.filter(user=user, role=role).count() == 1

    def test_unknown_code_rejected(self):
        with pytest.raises(ValidationError):
            role_create(code="bad", name="Bad", permission_codes=["not:a:real"])

    def test_update_replaces_permissions(self):
        role = role_create(
            code="swap",
            name="Swap",
            permission_codes=["cookbook:recipe:list"],
        )
        role_update(role_id=role.id, data={"permission_codes": ["cookbook:recipe:publish"]})
        assert list(role.permissions.values_list("code", flat=True)) == ["cookbook:recipe:publish"]

    def test_revoke_drops_perm(self):
        user = _user(username="sec_role_b", email="sec_role_b@example.com", phone=251911000312)
        grant_permissions(user=user, codes=["cookbook:recipe:list"])
        link = UserRole.objects.get(user=user)
        user_role_revoke(user_id=user.id, role_id=link.role_id)
        from core.security.services import user_has_permission

        assert user_has_permission(user=user, action="cookbook:recipe:list") is False
