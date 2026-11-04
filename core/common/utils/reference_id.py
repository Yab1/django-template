"""
Generate human-readable reference IDs for models using ReferenceIdMixin.

Format: {platform_prefix}-{model_prefix}-{6 random alphanumeric}
Example: DT-NTF-A3X9K2
"""

import secrets
import string
from typing import TypeVar

from django.conf import settings
from django.db import models

T = TypeVar("T", bound=models.Model)

# Alphanumeric (uppercase + digits), no ambiguous chars (0/O, 1/I/L)
REFERENCE_ID_ALPHABET = string.ascii_uppercase + string.digits
for _ch in "0O1IL":
    REFERENCE_ID_ALPHABET = REFERENCE_ID_ALPHABET.replace(_ch, "")


def generate_reference_id(*, model: type[T], max_attempts: int = 50) -> str:
    """
    Generate a unique ``reference_id`` for ``model``.

    The model must use ``ReferenceIdMixin`` and set ``reference_id_prefix``
    (exactly 3 chars, e.g. ``"NTF"``).
    """
    prefix = getattr(model, "reference_id_prefix", None)
    if not prefix:
        raise AttributeError(f"{model.__name__} must set reference_id_prefix when using ReferenceIdMixin")
    if len(prefix) != 3:
        raise ValueError(
            f"{model.__name__}.reference_id_prefix must be exactly 3 characters, got {prefix!r}",
        )

    platform = getattr(settings, "REFERENCE_ID_PLATFORM_PREFIX", "DT")
    base = f"{platform}-{prefix}-"

    for _ in range(max_attempts):
        random_part = "".join(secrets.choice(REFERENCE_ID_ALPHABET) for _ in range(6))
        value = f"{base}{random_part}"
        if not model.objects.filter(reference_id=value).exists():
            return value

    raise RuntimeError(f"Could not generate unique reference_id for {model.__name__} after {max_attempts} attempts")
