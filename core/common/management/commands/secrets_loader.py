"""
Load superuser secrets from YAML (used by load_superusers command only).

Provides secure loading of superuser config from a YAML file
referenced via DJANGO_SECRETS_FILE_PATH environment variable.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml

logger = logging.getLogger(__name__)


class SecretsLoaderError(Exception):
    """Base exception for secrets loader errors."""


class SecretsFileNotFoundError(SecretsLoaderError):
    """Raised when the secrets file path is not found."""


class SecretsFileInvalidError(SecretsLoaderError):
    """Raised when the secrets file is invalid or malformed."""


def get_secrets_file_path() -> Path:
    """
    Get the secrets file path from environment variable.

    Returns:
        Path: Path to the secrets file.

    Raises:
        SecretsFileNotFoundError: If DJANGO_SECRETS_FILE_PATH is not set or file doesn't exist.
    """
    secrets_path = os.getenv("DJANGO_SECRETS_FILE_PATH")
    if not secrets_path:
        raise SecretsFileNotFoundError(
            "DJANGO_SECRETS_FILE_PATH environment variable is not set. Please set it in your .env file.",
        )

    # Remove quotes if present
    secrets_path = secrets_path.strip().strip('"').strip("'")

    path = Path(secrets_path)
    if not path.exists():
        raise SecretsFileNotFoundError(
            f"Secrets file not found at: {path}. Please ensure the file exists and the path is correct.",
        )

    if not path.is_file():
        raise SecretsFileNotFoundError(
            f"Secrets file path is not a file: {path}",
        )

    return path


def load_secrets() -> Dict[str, Any]:
    """
    Load secrets from YAML file.

    The file path is read from the DJANGO_SECRETS_FILE_PATH environment variable.

    Returns:
        Dict[str, Any]: Dictionary containing the secrets data.

    Raises:
        SecretsFileNotFoundError: If the secrets file is not found.
        SecretsFileInvalidError: If the secrets file is invalid or malformed.
    """
    try:
        secrets_path = get_secrets_file_path()
    except SecretsFileNotFoundError:
        raise

    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            secrets = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SecretsFileInvalidError(
            f"Invalid YAML in secrets file {secrets_path}: {e}",
        ) from e
    except IOError as e:
        raise SecretsFileNotFoundError(
            f"Error reading secrets file {secrets_path}: {e}",
        ) from e

    if not isinstance(secrets, dict):
        raise SecretsFileInvalidError(
            f"Secrets file {secrets_path} must contain a YAML dictionary.",
        )

    logger.info(f"Successfully loaded secrets from {secrets_path}")
    return secrets


def get_superusers() -> list[Dict[str, Any]]:
    """
    Get superusers list from secrets file.

    Returns:
        list[Dict[str, Any]]: List of superuser dictionaries.

    Raises:
        SecretsFileNotFoundError: If the secrets file is not found.
        SecretsFileInvalidError: If the secrets file is invalid or malformed.
    """
    secrets = load_secrets()
    superusers = secrets.get("superusers", [])

    if not isinstance(superusers, list):
        raise SecretsFileInvalidError(
            "The 'superusers' key in secrets file must contain a list.",
        )

    return superusers
