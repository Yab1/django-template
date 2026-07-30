"""
Common utility functions for the EHR Patient Service.

This package provides various utility functions organized by functionality:
- database: Database query utilities
- object_creation: Object creation and update utilities
- secrets_loader: Secrets loader utilities

This module uses the "barrel export" pattern (also called "re-export") where
all public functions are exported from this __init__.py file, making imports
cleaner: `from core.common.utils import create_object` instead of
`from core.common.utils.object_creation import create_object`.
"""

# Database utilities
from .database import get_list, get_object, resolve_foreign_key

# Object creation utilities
from .object_creation import create_object, get_field_value, input_to_dict, remove_keys_from_dict, update_object

# Secrets loader utilities
from .secrets_loader import (
    SecretsFileInvalidError,
    SecretsFileNotFoundError,
    get_secrets_file_path,
    get_superusers,
    load_secrets,
)

# Terminology validation utilities
from .terminology_validation import get_code_system_for_field, validate_terminology_field

__all__ = [
    # Database
    "get_list",
    "get_object",
    "resolve_foreign_key",
    # Object creation
    "input_to_dict",
    "create_object",
    "get_field_value",
    "remove_keys_from_dict",
    "update_object",
    # Secrets loader
    "get_secrets_file_path",
    "load_secrets",
    "get_superusers",
    "SecretsFileNotFoundError",
    "SecretsFileInvalidError",
    # Terminology validation
    "get_code_system_for_field",
    "validate_terminology_field",
]
