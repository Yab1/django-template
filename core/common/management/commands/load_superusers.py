"""
Management command to load superusers from YAML secrets file.

This command reads superuser credentials from a YAML file (path specified
via SECRETS_FILE_PATH environment variable) and creates or updates them.
"""

import logging
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from core.common.utils.secrets_loader import (
    SecretsFileInvalidError,
    SecretsFileNotFoundError,
    get_superusers,
)

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
    help = "Load superusers from YAML secrets file (path from SECRETS_FILE_PATH env var)"

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
        required_fields = ["email", "password", "first_name", "last_name", "phone_number"]
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

        # Check if user exists
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

        # Prepare user data
        user_data = {
            "email": email,
            "first_name": su_data["first_name"],
            "last_name": su_data["last_name"],
            "phone_number": phone_number,
            "is_superuser": True,
            "is_staff": True,
            "is_admin": True,
            "is_active": True,
        }

        if dry_run:
            if exists:
                action = f"Would update: {email}"
            else:
                action = f"Would create: {email}"
            return (None, action)

        # Create or update user
        if exists:
            # Update existing user
            for key, value in user_data.items():
                setattr(user, key, value)
            user.set_password(su_data["password"])
            user.save()
            return (user, f"Updated: {email}")
        # Create new user
        user = User.objects.create_superuser(
            email=email,
            password=su_data["password"],
            first_name=su_data["first_name"],
            last_name=su_data["last_name"],
            phone_number=phone_number,
        )
        return (user, f"Created: {email}")

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
