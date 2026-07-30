from django.db import models
from django.utils.translation import gettext_lazy as _
from easyaudit.models import CRUDEvent, LoginEvent


class CrudEventType(models.TextChoices):
    CREATE = "create", _("Create")
    UPDATE = "update", _("Update")
    DELETE = "delete", _("Delete")
    M2M_CHANGE = "m2m_change", _("Many-to-many change")


class LoginEventType(models.TextChoices):
    LOGIN = "login", _("Login")
    LOGOUT = "logout", _("Logout")
    FAILED = "failed", _("Failed login")


_CRUD_EVENT_TO_INT = {
    CrudEventType.CREATE: CRUDEvent.CREATE,
    CrudEventType.UPDATE: CRUDEvent.UPDATE,
    CrudEventType.DELETE: CRUDEvent.DELETE,
    CrudEventType.M2M_CHANGE: CRUDEvent.M2M_CHANGE_REV,
}

_CRUD_INT_TO_EVENT = {value: key.value for key, value in _CRUD_EVENT_TO_INT.items()}

_LOGIN_EVENT_TO_INT = {
    LoginEventType.LOGIN: LoginEvent.LOGIN,
    LoginEventType.LOGOUT: LoginEvent.LOGOUT,
    LoginEventType.FAILED: LoginEvent.FAILED,
}

_LOGIN_INT_TO_EVENT = {value: key.value for key, value in _LOGIN_EVENT_TO_INT.items()}


def crud_event_type_to_int(value: str) -> int:
    return _CRUD_EVENT_TO_INT[CrudEventType(value)]


def int_to_crud_event_type(value: int) -> str:
    return _CRUD_INT_TO_EVENT[value]


def login_event_type_to_int(value: str) -> int:
    return _LOGIN_EVENT_TO_INT[LoginEventType(value)]


def int_to_login_event_type(value: int) -> str:
    return _LOGIN_INT_TO_EVENT[value]
