"""
Patch strawberry-django's OffsetPaginationInfo, paginated wrapper types, and DjangoFileType to be shareable for Federation.

This module adds the @shareable directive to pagination types and DjangoFileType so they can be shared across subgraphs.
Based on Strawberry Federation documentation: https://strawberry.rocks/docs/guides/federation
"""  # noqa: E501

import strawberry_django.pagination as pagination_module
from strawberry.extensions import SchemaExtension
from strawberry.federation.schema_directives import Shareable

# Import DjangoFileType from strawberry_django
try:
    from strawberry_django.fields.types import DjangoFileType
except ImportError:
    DjangoFileType = None


def _add_shareable_directive(type_class):
    """Add Shareable directive to a type if it has a type definition."""
    # Try both old and new attribute names for compatibility
    type_def = None
    if hasattr(type_class, "__strawberry_definition__"):
        type_def = type_class.__strawberry_definition__
    elif hasattr(type_class, "_type_definition"):
        type_def = type_class._type_definition  # pyright: ignore[reportAttributeAccessIssue]

    if type_def is not None:
        directives = list(getattr(type_def, "directives", []) or [])

        # Add Shareable if not already present
        if not any(isinstance(d, Shareable) for d in directives):
            directives.append(Shareable())
            type_def.directives = tuple(directives)


# Patch OffsetPaginationInfo (the base pagination info type)
if hasattr(pagination_module, "OffsetPaginationInfo"):
    _add_shareable_directive(pagination_module.OffsetPaginationInfo)

# Patch OffsetPaginated base class if it exists
if hasattr(pagination_module, "OffsetPaginated"):
    _add_shareable_directive(pagination_module.OffsetPaginated)

# Patch DjangoFileType if available
if DjangoFileType is not None:
    _add_shareable_directive(DjangoFileType)


def patch_all_paginated_types():
    """Patch all paginated wrapper types from strawberry's type registry."""
    try:
        import strawberry.type as type_module  # pyright: ignore[reportMissingImports]

        if hasattr(type_module, "_type_registry"):
            for type_class in type_module._type_registry.values():  # pyright: ignore[reportPrivateUsage]
                if hasattr(type_class, "__name__") and type_class.__name__.endswith("OffsetPaginated"):
                    _add_shareable_directive(type_class)
    except Exception:
        pass


# Patch types immediately (for types already registered)
patch_all_paginated_types()


def _patch_schema_types_after_creation(schema):
    """Patch pagination types and DjangoFileType from the GraphQL schema's type map after schema creation."""
    try:
        if hasattr(schema, "_schema") and hasattr(schema._schema, "type_map"):
            for type_name, graphql_type in schema._schema.type_map.items():
                # Check if this is a paginated type or OffsetPaginationInfo
                if isinstance(type_name, str) and (
                    type_name.endswith("OffsetPaginated") or type_name == "OffsetPaginationInfo"
                ):
                    # Patch the Strawberry type definition
                    if hasattr(graphql_type, "_strawberry_definition"):
                        strawberry_type = graphql_type._strawberry_definition
                        if strawberry_type:
                            _add_shareable_directive(strawberry_type)

                # Also patch DjangoFileType if it exists
                if isinstance(type_name, str) and type_name == "DjangoFileType":
                    # Patch the Strawberry type definition
                    if hasattr(graphql_type, "_strawberry_definition"):
                        strawberry_type = graphql_type._strawberry_definition
                        if strawberry_type:
                            _add_shareable_directive(strawberry_type)

                    # Also ensure the GraphQL type has the directive in its extensions
                    if not hasattr(graphql_type, "extensions"):
                        graphql_type.extensions = {}
                    if "federation" not in graphql_type.extensions:
                        graphql_type.extensions["federation"] = {}
                    if "shareable" not in graphql_type.extensions.get("federation", {}):
                        graphql_type.extensions["federation"]["shareable"] = True
    except Exception:
        pass


class PaginationShareableExtension(SchemaExtension):
    """
    Schema extension to mark paginated wrapper types and DjangoFileType as shareable.

    This extension doesn't implement resolve, so it won't be used as middleware.
    The actual patching happens at module import time and when operations are executed.
    """

    def __init__(self, *, execution_context=None):
        """Initialize the extension."""
        super().__init__(execution_context=execution_context)
        # Patch types when extension is instantiated (schema initialization)
        patch_all_paginated_types()
        # Also patch DjangoFileType if available
        if DjangoFileType is not None:
            _add_shareable_directive(DjangoFileType)
        self._patched = False

    def on_operation(self):
        """Called when an operation starts - patch types from schema if not already patched."""
        if not self._patched and hasattr(self, "execution_context") and self.execution_context:
            schema = self.execution_context.schema
            self._patch_schema_types(schema)
            self._patched = True
        yield

    def _patch_schema_types(self, schema):
        """Patch pagination types and DjangoFileType from the GraphQL schema's type map."""
        try:
            if hasattr(schema, "_schema") and hasattr(schema._schema, "type_map"):
                # Get the Shareable directive from the schema
                shareable_directive = None
                for directive in schema._schema.directives:
                    if directive.name == "shareable":
                        shareable_directive = directive
                        break

                if not shareable_directive:
                    # Create shareable directive if not found
                    from graphql import GraphQLDirective

                    shareable_directive = GraphQLDirective(
                        name="shareable",
                        locations=[],
                    )

                for type_name, graphql_type in schema._schema.type_map.items():
                    # Check if this is a paginated type or OffsetPaginationInfo
                    if isinstance(type_name, str) and (
                        type_name.endswith("OffsetPaginated") or type_name == "OffsetPaginationInfo"
                    ):
                        # Patch the Strawberry type definition
                        if hasattr(graphql_type, "_strawberry_definition"):
                            strawberry_type = graphql_type._strawberry_definition
                            if strawberry_type:
                                _add_shareable_directive(strawberry_type)

                        # Also ensure the GraphQL type has the directive in its extensions
                        if not hasattr(graphql_type, "extensions"):
                            graphql_type.extensions = {}
                        if "federation" not in graphql_type.extensions:
                            graphql_type.extensions["federation"] = {}
                        if "shareable" not in graphql_type.extensions.get("federation", {}):
                            if "federation" not in graphql_type.extensions:
                                graphql_type.extensions["federation"] = {}
                            graphql_type.extensions["federation"]["shareable"] = True

                    # Also patch DjangoFileType if it exists
                    if isinstance(type_name, str) and type_name == "DjangoFileType":
                        # Patch the Strawberry type definition
                        if hasattr(graphql_type, "_strawberry_definition"):
                            strawberry_type = graphql_type._strawberry_definition
                            if strawberry_type:
                                _add_shareable_directive(strawberry_type)

                        # Also ensure the GraphQL type has the directive in its extensions
                        if not hasattr(graphql_type, "extensions"):
                            graphql_type.extensions = {}
                        if "federation" not in graphql_type.extensions:
                            graphql_type.extensions["federation"] = {}
                        if "shareable" not in graphql_type.extensions.get("federation", {}):
                            if "federation" not in graphql_type.extensions:
                                graphql_type.extensions["federation"] = {}
                            graphql_type.extensions["federation"]["shareable"] = True
        except Exception:
            pass
