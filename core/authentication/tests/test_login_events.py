import pytest
from django.contrib.auth import get_user_model
from easyaudit.models import LoginEvent
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_jwt_obtain_wrong_password_creates_failed_login_event() -> None:
    User.objects.create_user(
        "loginev1",
        "loginev1@example.com",
        password="ValidPassw0rd!!",
        phone_number=251900000020,
    )
    before = LoginEvent.objects.filter(login_type=LoginEvent.FAILED).count()
    client = APIClient()
    response = client.post(
        "/api/v1/authentication/token/",
        {"username": "loginev1", "password": "wrong-password"},
        format="json",
    )
    assert response.status_code == 401
    after = LoginEvent.objects.filter(login_type=LoginEvent.FAILED).count()
    assert after == before + 1


@pytest.mark.django_db
def test_jwt_blacklist_creates_logout_login_event() -> None:
    User.objects.create_user(
        "loginev2",
        "loginev2@example.com",
        password="ValidPassw0rd!!",
        phone_number=251900000021,
    )
    client = APIClient()
    obtain = client.post(
        "/api/v1/authentication/token/",
        {"username": "loginev2", "password": "ValidPassw0rd!!"},
        format="json",
    )
    assert obtain.status_code == 200
    refresh = obtain.data["refresh"]

    before = LoginEvent.objects.filter(login_type=LoginEvent.LOGOUT).count()
    logout = client.post(
        "/api/v1/authentication/token/blacklist/",
        {"refresh": refresh},
        format="json",
    )
    assert logout.status_code == 200
    after = LoginEvent.objects.filter(login_type=LoginEvent.LOGOUT).count()
    assert after == before + 1
