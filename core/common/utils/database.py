import uuid

from django.http import Http404
from django.shortcuts import get_list_or_404, get_object_or_404


def get_list(model_or_queryset, **kwargs):
    try:
        return get_list_or_404(model_or_queryset)
    except Http404 as exc:
        raise exc


def get_object(model_or_queryset, **kwargs):
    try:
        return get_object_or_404(model_or_queryset, **kwargs)
    except Http404:
        raise Http404(f"{model_or_queryset.__name__} not found")


def resolve_foreign_key(value, model):
    """
    Resolve a strawberry_django foreign key input to a model instance.

    strawberry_django wraps foreign keys in OneToManyInput objects with a .set attribute.
    This function extracts the ID and resolves it to the actual model instance.

    Args:
        value: Either a OneToManyInput object (with .set attribute) or a model instance/ID
        model: The Django model class to resolve to

    Returns:
        The model instance

    Example:
        user = resolve_foreign_key(input.user, User)
        idir = resolve_foreign_key(input.idir, Idir)
    """
    # Extract ID from OneToManyInput if present
    if hasattr(value, "set"):
        value = value.set

    # If it's already a model instance, return it
    if isinstance(value, model):
        return value

    # If it's an ID (string or UUID), resolve it
    if isinstance(value, (str, uuid.UUID)):
        return get_object(model, id=value)

    # Fallback: return as-is (might already be the instance)
    return value
