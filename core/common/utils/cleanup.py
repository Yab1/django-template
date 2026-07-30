"""
Cleanup utilities for safely removing replaced relationship objects.

This module provides utilities for safely deleting ForeignKey and OneToOne
objects that have been replaced during upsert operations, ensuring that
objects are only deleted if they are not referenced elsewhere.
"""

import logging
from typing import Any, List, Tuple, Type

from django.db import models

logger = logging.getLogger(__name__)


def safe_delete_replaced_foreign_key(
    old_obj: Any,
    model_class: Type[models.Model],
    reference_checks: List[Tuple[Type[models.Model], str]],
) -> bool:
    """
    Safely delete a ForeignKey or OneToOne object if it's no longer referenced.

    This function checks if the old object is referenced by any other models
    before deleting it. If references are found, the object is kept. If no
    references are found, the object is deleted.

    Args:
        old_obj: The old ForeignKey/OneToOne object to potentially delete
        model_class: The model class (for logging purposes)
        reference_checks: List of (model_class, field_name) tuples to check
                         for references. Each tuple represents a model and field
                         that might reference the old_obj.

    Returns:
        bool: True if deleted, False if kept (has references or deletion failed)

    Example:
        >>> from core.fhir.models import Identifier
        >>> from core.organization.models import Organization
        >>> old_identifier = Identifier.objects.get(id=some_id)
        >>> checks = [(Organization, 'identifier')]
        >>> deleted = safe_delete_replaced_foreign_key(old_identifier, Identifier, checks)
        >>> if deleted:
        ...     print("Identifier was safely deleted")
        ... else:
        ...     print("Identifier is still referenced, kept")
    """
    if old_obj is None:
        return False

    # Check all possible references
    for ref_model, field_name in reference_checks:
        try:
            # Check if any instance of ref_model references old_obj via field_name
            if ref_model.objects.filter(**{field_name: old_obj}).exists():
                logger.debug(
                    f"{model_class.__name__} {old_obj.id} is still referenced by {ref_model.__name__}.{field_name}, keeping it"  # noqa: E501
                )
                return False
        except Exception as e:
            logger.warning(
                f"Error checking references in {ref_model.__name__}.{field_name} for {model_class.__name__} {old_obj.id}: {e}"  # noqa: E501
            )
            # If we can't check, err on the side of caution and keep the object
            return False

    # No references found, safe to delete
    try:
        old_obj.delete()
        logger.debug(f"Successfully deleted {model_class.__name__} {old_obj.id}")
        return True
    except Exception as e:
        logger.warning(
            f"Failed to delete {model_class.__name__} {old_obj.id}: {e}. Keeping the object to avoid data loss."
        )
        return False
