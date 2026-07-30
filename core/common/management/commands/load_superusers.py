"""
Management command to load superusers from YAML secrets file.

This command reads superuser credentials from a YAML file (path specified
via DJANGO_SECRETS_FILE_PATH environment variable) and creates or updates them.
"""

import logging
import re
import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.management.base import BaseCommand, CommandError

from .secrets_loader import (
    SecretsFileInvalidError,
    SecretsFileNotFoundError,
    get_superusers,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = "Load superusers from YAML secrets file (path from DJANGO_SECRETS_FILE_PATH env var)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing superusers (default: skip if exists)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force update even if user exists (same as --update)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created/updated without making changes",
        )

    def _parse_optional_uuid(self, value) -> uuid.UUID | None:
        """
        Parse an optional UUID from YAML input.

        Returns ``None`` if the value is missing/empty. Raises ``CommandError``
        for anything that isn't a valid UUID, so we fail fast on the YAML
        rather than inside an ``INSERT``.
        """
        if value is None or value == "":
            return None
        try:
            return uuid.UUID(str(value))
        except (ValueError, TypeError, AttributeError) as e:
            raise CommandError(f"Invalid UUID for 'id': {value!r}") from e

    def _normalize_phone_number(self, phone_number: str | int) -> int:
        """
        Normalize phone number from string or integer format to integer.

        Args:
            phone_number: Phone number string (e.g., "+251931470920") or integer

        Returns:
            int: Phone number as integer (e.g., 251931470920)

        Raises:
            CommandError: If phone number format is invalid.
        """
        # If already an integer, return it
        if isinstance(phone_number, int):
            return phone_number

        # Convert to string if not already
        if not isinstance(phone_number, str):
            phone_number = str(phone_number)

        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone_number)

        if not digits_only:
            raise CommandError(f"Invalid phone number format: {phone_number}")

        try:
            return int(digits_only)
        except ValueError as e:
            raise CommandError(f"Invalid phone number format: {phone_number}") from e

    def _validate_superuser_data(self, su_data: dict) -> None:
        """
        Validate superuser data structure.

        Args:
            su_data: Dictionary containing superuser data.

        Raises:
            CommandError: If required fields are missing or invalid.
        """
        required_fields = ["email", "password", "phone_number"]
        missing_fields = [field for field in required_fields if field not in su_data]

        if missing_fields:
            raise CommandError(
                f"Missing required fields for superuser: {', '.join(missing_fields)}",
            )

        # Validate email format (basic check)
        email = su_data["email"]
        if "@" not in email or "." not in email.split("@")[1]:
            raise CommandError(f"Invalid email format: {email}")

        # Validate password is not empty
        if not su_data["password"]:
            raise CommandError("Password cannot be empty")

        if "id" in su_data:
            self._parse_optional_uuid(su_data["id"])

    def _resolve_username(self, *, su_data: dict, email: str) -> str:
        raw = (su_data.get("username") or "").strip()
        if not raw:
            raw = email.split("@", 1)[0]
        return User.normalize_username(raw)

    def _create_or_update_superuser(
        self,
        su_data: dict,
        update: bool = False,
        dry_run: bool = False,
    ) -> tuple[User | None, str]:
        """
        Create or update a superuser.

        Args:
            su_data: Dictionary containing superuser data.
            update: Whether to update existing users.
            dry_run: If True, don't actually create/update, just return what would happen.

        Returns:
            tuple: (User instance or None, action message)
        """
        email = su_data["email"]
        phone_number = self._normalize_phone_number(su_data["phone_number"])
        username = self._resolve_username(su_data=su_data, email=email)
        desired_id = self._parse_optional_uuid(su_data.get("id"))

        try:
            user = User.objects.get(email=email)
            exists = True
        except User.DoesNotExist:
            user = None
            exists = False

        if exists and not update:
            return (
                user,
                f"Skipped (already exists): {email}",
            )

        policy_user = user if exists else User(username=username, email=email, phone_number=phone_number)
        try:
            validate_password(su_data["password"], policy_user)
        except DjangoValidationError as e:
            raise CommandError("; ".join(e.messages)) from e

        user_data = {
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "is_superuser": True,
            "is_staff": True,
            "is_admin": True,
            "is_active": True,
        }

        if dry_run:
            if exists:
                return (None, f"Would update: {email}")
            if desired_id is not None:
                return (None, f"Would create: {email} (id={desired_id})")
            return (None, f"Would create: {email}")

        if exists:
            if desired_id is not None and user.id != desired_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"  id mismatch for {email}: YAML={desired_id}, DB={user.id}; "
                        "leaving DB id unchanged (changing a user PK is unsafe).",
                    ),
                )
            for key, value in user_data.items():
                setattr(user, key, value)
            user.set_password(su_data["password"])
            user.save()
            return (user, f"Updated: {email}")

        create_kwargs: dict = {
            "username": username,
            "email": email,
            "password": su_data["password"],
            "phone_number": phone_number,
        }
        if desired_id is not None:
            create_kwargs["id"] = desired_id

        user = User.objects.create_superuser(**create_kwargs)
        suffix = f" (id={desired_id})" if desired_id is not None else ""
        return (user, f"Created: {email}{suffix}")

    def handle(self, *args, **options):
        update = options.get("update") or options.get("force", False)
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No changes will be made"),
            )

        try:
            superusers = get_superusers()
        except SecretsFileNotFoundError as e:
            raise CommandError(str(e)) from e
        except SecretsFileInvalidError as e:
            raise CommandError(str(e)) from e

        if not superusers:
            self.stdout.write(
                self.style.WARNING("No superusers found in secrets file"),
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"Found {len(superusers)} superuser(s) in secrets file"),
        )

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for i, su_data in enumerate(superusers, 1):
            try:
                self._validate_superuser_data(su_data)
                _user, message = self._create_or_update_superuser(
                    su_data,
                    update=update,
                    dry_run=dry_run,
                )

                if "Created" in message:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  [{i}] {message}"))
                elif "Updated" in message:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"  [{i}] {message}"))
                elif "Would create" in message:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  [{i}] {message}"))
                elif "Would update" in message:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"  [{i}] {message}"))
                else:
                    skipped_count += 1
                    self.stdout.write(self.style.NOTICE(f"  [{i}] {message}"))

            except CommandError as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  [{i}] Error: {str(e)}"),
                )
                logger.error(f"Error processing superuser {i}: {e}")
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  [{i}] Unexpected error: {str(e)}"),
                )
                logger.exception(f"Unexpected error processing superuser {i}: {e}")

        # Summary
        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY RUN SUMMARY:"),
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("SUMMARY:"),
            )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"  Created: {created_count}"),
            )
        if updated_count > 0:
            self.stdout.write(
                self.style.WARNING(f"  Updated: {updated_count}"),
            )
        if skipped_count > 0:
            self.stdout.write(
                self.style.NOTICE(f"  Skipped: {skipped_count}"),
            )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f"  Errors: {error_count}"),
            )

        if error_count > 0:
            raise CommandError(f"Failed to process {error_count} superuser(s)")
