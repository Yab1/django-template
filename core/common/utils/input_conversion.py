"""
Input conversion utilities for GraphQL services.

This module provides utilities for converting between different input types,
particularly for upsert operations that need to convert InputPartial to Input.
"""

from typing import Any, Type


def convert_partial_to_input(partial_input: Any, input_class: Type) -> Any:
    """
    Convert InputPartial to Input for create operations.

    This is used in upsert operations when an ID is missing and we need to
    create a new instance. The InputPartial (which has all optional fields)
    is converted to Input (which may have required fields) by extracting
    all non-UNSET values.

    Args:
        partial_input: InputPartial object containing the data
        input_class: The Input class to convert to

    Returns:
        Input: New Input instance with all non-UNSET values from partial_input

    Example:
        >>> from core.organization.inputs import OrganizationInputPartial, OrganizationInput
        >>> partial = OrganizationInputPartial(name="Test")
        >>> input_obj = convert_partial_to_input(partial, OrganizationInput)
        >>> isinstance(input_obj, OrganizationInput)
        True
    """
    from core.common.utils import input_to_dict

    # Convert InputPartial to dict (filters out UNSET values)
    data = input_to_dict(partial_input)

    # Create Input instance with the data
    return input_class(**data)
