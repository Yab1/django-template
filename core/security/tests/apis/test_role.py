import pytest
from rest_framework.test import APIClient

from core.security.testing import grant_permissions
from core.users.models import User

_URL = "/api/v1/security/"


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
class SecurityApiTests:
    def setup_method(self):
        self.client = APIClient()

    def test_create_list_assign_me_revoke(self):
        admin = _user(
            username="sec_api_su",
            email="sec_api_su@example.com",
            phone=251911000321,
            superuser=True,
        )
        target = _user(username="sec_api_u", email="sec_api_u@example.com", phone=251911000322)
        self.client.force_authenticate(user=admin)

        created = self.client.post(
            f"{_URL}roles/create/",
            {
                "code": "cookbook_writer",
                "name": "Cookbook writer",
                "permission_codes": ["cookbook:recipe:create", "cookbook:recipe:list"],
            },
            format="json",
        )
        assert created.status_code == 201
        role_id = created.json()["result"]["id"]

        listed = self.client.get(f"{_URL}roles/")
        assert listed.status_code == 200
        assert listed.json()["result"]["count"] >= 1

        assigned = self.client.post(
            f"{_URL}users/{target.id}/roles/assign/",
            {"role_id": role_id},
            format="json",
        )
        assert assigned.status_code == 201

        self.client.force_authenticate(user=target)
        mine = self.client.get(f"{_URL}me/permissions/")
        assert mine.status_code == 200
        codes = mine.json()["result"]["codes"]
        assert "cookbook:recipe:create" in codes
        assert mine.json()["result"]["is_superuser"] is False

        self.client.force_authenticate(user=admin)
        revoked = self.client.post(f"{_URL}users/{target.id}/roles/{role_id}/revoke/")
        assert revoked.status_code == 200

    def test_non_admin_cannot_create_role(self):
        user = _user(username="sec_api_no", email="sec_api_no@example.com", phone=251911000323)
        grant_permissions(user=user, codes=["cookbook:recipe:list"])
        self.client.force_authenticate(user=user)
        response = self.client.post(
            f"{_URL}roles/create/",
            {"code": "nope", "name": "Nope"},
            format="json",
        )
        assert response.status_code == 403
