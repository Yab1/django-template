from typing import Any, Dict

import strawberry
from strawberry import UNSET


def input_to_dict(input_data: Any) -> Dict[str, Any]:
    """
    Convert input to dict and filter out UNSET values.

    This utility function handles the common pattern of converting GraphQL input
    objects (or any object) to a dictionary and removing UNSET values, which are
    used in Strawberry to represent fields that were not provided.

    Uses strawberry.asdict() for proper handling of nested Strawberry objects,
    which is especially beneficial for JSON fields as it ensures all nested objects
    are converted to JSON-serializable dicts.

    Args:
        input_data: The input object to convert. Can be a dict, Strawberry object,
                or any object that can be converted using strawberry.asdict() or vars().

    Returns:
        Dict[str, Any]: A dictionary with UNSET values filtered out and nested objects converted.

    Example:
        # Convert GraphQL input to dict without UNSET values
        data = input_to_dict(input)
        # Use the cleaned data
        instance = Model.objects.create(**data)
    """
    # Convert input to dict if it's not already a dict
    if isinstance(input_data, dict):
        data = input_data.copy()
    else:
        # Use strawberry.asdict() for better nested object handling
        try:
            data = strawberry.asdict(input_data)
        except (TypeError, AttributeError):
            # Fallback to vars() for non-Strawberry objects
            data = dict(vars(input_data))

    # Filter out UNSET values
    return {k: v for k, v in data.items() if v is not UNSET}


def create_object(*, model, data):
    # Handle both dict and object inputs
    if hasattr(data, "__dict__"):
        # Convert object to dict and filter out None and UNSET values
        data_dict = {k: v for k, v in data.__dict__.items() if v is not None and v is not UNSET}
    else:
        # If it's already a dict, filter out None and UNSET values
        data_dict = {k: v for k, v in data.items() if v is not None and v is not UNSET}

    # Detect ManyToMany fields from the model
    many_to_many_fields = {}
    for field in model._meta.get_fields():
        if field.many_to_many and not field.auto_created:
            field_name = field.name
            if field_name in data_dict:
                many_to_many_fields[field_name] = data_dict.pop(field_name)

    # Convert enum values to their string values for regular fields
    cleaned_data = {}
    for key, value in data_dict.items():
        if hasattr(value, "value") and hasattr(value, "name"):
            # It's an enum - extract the value
            cleaned_data[key] = value.value
        else:
            cleaned_data[key] = value

    # Create the instance without ManyToMany fields
    instance = model.objects.create(**cleaned_data)

    # Set ManyToMany fields after instance creation
    for field_name, field_value in many_to_many_fields.items():
        if field_value:
            # If it's a list of objects, extract IDs or use objects directly
            if isinstance(field_value, list):
                getattr(instance, field_name).set(field_value)
            else:
                getattr(instance, field_name).set([field_value])

    return instance


def remove_keys_from_dict(data: Dict[str, Any], keys: list[str]) -> Dict[str, Any]:
    """
    Remove multiple keys from a dictionary.

    This utility function removes multiple keys from a dictionary in one call,
    which is cleaner than calling data.pop() multiple times.

    Args:
        data: The dictionary to remove keys from.
        keys: List of keys to remove from the dictionary.

    Returns:
        Dict[str, Any]: The dictionary with the specified keys removed.

    Example:
        data = {"name": "John", "age": 30, "author": author_obj, "tags": tags_list}
        data = remove_keys_from_dict(data, ["author", "tags"])
        # data is now {"name": "John", "age": 30}
    """
    for key in keys:
        data.pop(key, None)
    return data


def update_object(*, instance, fields: list[str], data: dict):
    from django.core.exceptions import ValidationError

    update_fields: list[str] = []

    for field in fields:
        if field in data and data[field] is not None and data[field] is not UNSET:
            value = data[field]
            # Convert enum values to their string values
            if hasattr(value, "value") and hasattr(value, "name"):
                value = value.value
            setattr(instance, field, value)
            update_fields.append(field)

    # Validate only fields being updated (partial update pattern)
    # This prevents validation errors on fields we're not updating
    if update_fields:
        try:
            # Run full validation
            instance.full_clean()
        except ValidationError as e:
            # Filter out validation errors for fields we're not updating
            # Only raise errors for fields that are being updated
            if hasattr(e, "error_dict") and e.error_dict:
                filtered_errors = {}
                for field_name, error_list in e.error_dict.items():
                    if field_name in update_fields:
                        filtered_errors[field_name] = error_list
                # Only raise if we have errors for updated fields
                if filtered_errors:
                    raise ValidationError(filtered_errors)
                # If no errors for updated fields, validation passed for our changes
                # (existing invalid data in other fields is ignored for partial updates)
            elif hasattr(e, "messages") and e.messages:
                # Non-field errors from clean() - these are cross-field validation errors
                # Check if any of the updated fields are mentioned in the error
                # For now, we'll raise them as they might involve the fields we're updating
                # This is a conservative approach - if clean() fails, it might be due to
                # cross-field validation involving updated fields
                raise e
    else:
        # No fields to update, skip validation
        pass

    instance.save(update_fields=update_fields or None)
    return instance


def get_field_value(input_obj: Any, field_name: str, instance: Any, default: Any = None) -> Any:
    """
    Get field value from input if provided (not UNSET), otherwise get existing value from instance.

    This utility handles the upsert pattern where we need to preserve existing values
    when fields are not provided in partial updates.

    Args:
        input_obj: The input object containing the field.
        field_name: Name of the field to get.
        instance: The existing instance to get the value from if field is UNSET.
        default: Default value to return if field is UNSET and instance doesn't have the field.

    Returns:
        The field value from input if provided, or the existing value from instance if UNSET.
    """
    field_value = getattr(input_obj, field_name, UNSET)
    return field_value if field_value is not UNSET else getattr(instance, field_name, default)
