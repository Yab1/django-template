import pytest
from django.core.exceptions import PermissionDenied

from core.security.services import authorize, authorize_queryset, user_has_permission
from core.security.testing import grant_permissions
from core.users.models import User


def _user(*, username: str, email: str, phone: int, superuser: bool = False) -> User:
    return User.objects.create_user(
        username=username,
        email=email,
        password="NotAWeakPassw0rd!",
        phone_number=phone,
        is_superuser=superuser,
        is_staff=superuser,
    )


@pytest.mark.django_db
class PermissionCheckTests:
    def test_superuser_has_any_action(self):
        admin = _user(
            username="sec_su",
            email="sec_su@example.com",
            phone=251911000301,
            superuser=True,
        )
        assert user_has_permission(user=admin, action="cookbook:recipe:publish") is True

    def test_staff_without_role_denied(self):
        staff = _user(username="sec_staff", email="sec_staff@example.com", phone=251911000302)
        staff.is_staff = True
        staff.save(update_fields=["is_staff"])
        assert user_has_permission(user=staff, action="users:user:list") is False

    def test_granted_code_allowed(self):
        user = _user(username="sec_ok", email="sec_ok@example.com", phone=251911000303)
        grant_permissions(user=user, codes=["cookbook:recipe:publish"])
        assert user_has_permission(user=user, action="cookbook:recipe:publish") is True
        assert user_has_permission(user=user, action="cookbook:recipe:delete") is False

    def test_authorize_raises_without_perm(self):
        user = _user(username="sec_no", email="sec_no@example.com", phone=251911000304)
        with pytest.raises(PermissionDenied):
            authorize(user=user, action="users:user:list")

    def test_authorize_queryset_empty_without_perm(self):
        user = _user(username="sec_qs", email="sec_qs@example.com", phone=251911000305)
        qs = authorize_queryset(
            queryset=User.objects.all(),
            user=user,
            action="users:user:list",
        )
        assert qs.count() == 0

    def test_permissions_flag_off_allows_authenticated(self, settings):
        settings.PERMISSIONS_ENABLED = False
        user = _user(username="sec_off", email="sec_off@example.com", phone=251911000306)
        assert user_has_permission(user=user, action="users:user:list") is True
