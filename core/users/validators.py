"""Custom ``AUTH_PASSWORD_VALIDATORS`` for ``users.User``."""

import hashlib
import logging

import httpx
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.users.constants import PASSWORD_HISTORY_LIMIT, PASSWORD_MAX_LENGTH

logger = logging.getLogger(__name__)


class PasswordComplexityValidator:
    """
    Requires upper, lower, digit, and punctuation; rejects whitespace; caps length.
    Complements ``CommonPasswordValidator``, breach checks (``PwnedPasswordValidator``), and length validators.
    """

    def __init__(self, *, max_length: int = PASSWORD_MAX_LENGTH):
        self.max_length = max_length

    def validate(self, password: str, user=None) -> None:
        del user
        if len(password) > self.max_length:
            raise ValidationError(
                _("This password is too long. It must contain at most %(max)d characters."),
                code="password_too_long",
                params={"max": self.max_length},
            )
        if any(ch.isspace() for ch in password):
            raise ValidationError(
                _("This password must not contain spaces or other whitespace."),
                code="password_whitespace",
            )
        missing: list[str] = []
        if not any(ch.isupper() for ch in password):
            missing.append(str(_("one uppercase letter")))
        if not any(ch.islower() for ch in password):
            missing.append(str(_("one lowercase letter")))
        if not any(ch.isdigit() for ch in password):
            missing.append(str(_("one digit")))
        if not any((not ch.isalnum() and not ch.isspace()) for ch in password):
            missing.append(str(_("one punctuation or symbol character")))
        if missing:
            joined = ", ".join(missing)
            raise ValidationError(
                _("This password must contain %(missing)s."),
                code="password_missing_character_classes",
                params={"missing": joined},
            )

    def get_help_text(self) -> str:
        return _(
            "Your password must be at most %(max)d characters, must not contain whitespace, "
            "and must include an uppercase letter, a lowercase letter, a digit, "
            "and a punctuation or symbol character."
        ) % {"max": self.max_length}


class PwnedPasswordValidator:
    """
    Check password against `Have I Been Pwned?`_ Pwned Passwords using k-anonymity (SHA-1 prefix only).

    Only the first five hex characters of the password's SHA-1 hash are sent over the network.
    On timeout or any request error, validation **passes** (fail open) so outages do not lock users out.

    .. _Have I Been Pwned?: https://haveibeenpwned.com/API/v3#PwnedPasswords
    """

    _range_url = "https://api.pwnedpasswords.com/range/{}"

    def __init__(
        self,
        *,
        min_pwned_count: int = 1,
        timeout_seconds: float = 2.0,
    ):
        self.min_pwned_count = min_pwned_count
        self.timeout_seconds = timeout_seconds

    def validate(self, password: str, user=None) -> None:
        del user
        sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]

        app = getattr(settings, "APP_DOMAIN", None) or "ehr-backend"
        headers = {
            "User-Agent": f"ehr-backend-password-validator ({app})",
            "Add-Padding": "true",
        }
        try:
            response = httpx.get(
                self._range_url.format(prefix),
                headers=headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.warning("Pwned passwords check skipped (fail open): %s", exc)
            return

        for raw_line in response.text.splitlines():
            line = raw_line.strip()
            if ":" not in line:
                continue
            hash_suffix, _sep, count_part = line.partition(":")
            hash_suffix = hash_suffix.strip().upper()
            if hash_suffix != suffix:
                continue
            try:
                count = int(count_part.strip())
            except ValueError:
                continue
            if count >= self.min_pwned_count:
                raise ValidationError(
                    _(
                        "This password has appeared in a data breach %(count)s time(s). "
                        "Please choose a different password."
                    ),
                    code="password_pwned",
                    params={"count": count},
                )
            return

    def get_help_text(self) -> str:
        return str(_("Your password must not have appeared in a known public data breach (Have I Been Pwned)."))


class PasswordHistoryValidator:
    """Rejects passwords matching the current hash or any stored retired hash."""

    def __init__(self, history_limit: int = PASSWORD_HISTORY_LIMIT):
        self.history_limit = history_limit

    def validate(self, password: str, user=None) -> None:
        if user is None or not user.pk:
            return

        from core.users.models import PasswordHistory  # local import avoids cycles at startup

        if user.has_usable_password() and check_password(password, user.password):
            raise ValidationError(
                _("Your new password must be different from your current password."),
                code="password_same_as_current",
            )

        recent = PasswordHistory.objects.filter(user=user).order_by("-created_at")[: self.history_limit]
        for entry in recent:
            if check_password(password, entry.hashed_password):
                raise ValidationError(
                    _("You cannot reuse any of your last %(n)d passwords."),
                    code="password_recently_used",
                    params={"n": self.history_limit},
                )

    def get_help_text(self) -> str:
        return _("Your password cannot match your current password or any of your last %(n)d previous passwords.") % {
            "n": self.history_limit,
        }
