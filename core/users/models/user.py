from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager as BUM  # noqa: N817
from django.contrib.auth.password_validation import validate_password
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.common.models import BaseModel
from core.users.models.mixins import HistoryMixin, SoftDeleteMixin, VisibleMixin


class BaseUserManager(BUM):
    def create_user(
        self,
        username: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields,
    ):
        if not username:
            raise ValueError("Users must have a username")
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)

        if password:
            validate_password(password, user)
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username: str,
        email: str | None = None,
        password: str | None = None,
        **extra_fields,
    ):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_admin", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self.create_user(username, email, password, **extra_fields)


class BaseUser(BaseModel):
    class Meta:
        abstract = True


class User(VisibleMixin, SoftDeleteMixin, HistoryMixin, BaseUser, AbstractUser, PermissionsMixin):
    first_name = None
    last_name = None

    email = models.EmailField(
        blank=False,
        max_length=255,
        unique=True,
        help_text=_("Primary email address used for login and notifications."),
    )
    phone_number = models.PositiveBigIntegerField(
        unique=True,
        help_text=_("Unique phone number for the account."),
    )

    is_active = models.BooleanField(
        default=True,
        help_text=_("Whether this account can authenticate."),
    )
    is_staff = models.BooleanField(
        default=False,
        help_text=_("Whether this account can access the Django admin site."),
    )
    is_admin = models.BooleanField(
        default=False,
        help_text=_("Whether this account has administrative privileges in the application."),
    )
    is_superuser = models.BooleanField(
        default=False,
        help_text=_("Whether this account has all permissions without explicit assignment."),
    )
    must_change_password = models.BooleanField(
        default=False,
        db_index=True,
        help_text=_("True when provisioned with a temporary password. API returns 403 until cleared."),
    )

    objects = BaseUserManager()  # pyright: ignore[reportAssignmentType]

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "phone_number"]

    class Meta:
        db_table = "users_user"
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]
        default_related_name = "users"

    def __str__(self) -> str:
        return f"{self.username} <{self.email}>"
