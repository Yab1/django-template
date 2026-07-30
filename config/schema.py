import strawberry
from django.core.files.uploadedfile import UploadedFile
from strawberry.file_uploads import Upload
from strawberry.schema.config import StrawberryConfig
from strawberry.tools import merge_types
from strawberry_django.optimizer import DjangoOptimizerExtension

import core.common.pagination_patch  # noqa: F401
from core.common.pagination_patch import PaginationShareableExtension
from core.fhir.mutations import CodeableConceptMutation, CodeableReferenceMutation, CodingMutation
from core.fhir.queries import CodeableConceptQuery, CodeableReferenceQuery, CodingQuery

Query = merge_types(
    "Query",
    (
        CodeableConceptQuery,
        CodeableReferenceQuery,
        CodingQuery,
    ),
)

Mutation = merge_types(
    "Mutation",
    (
        CodeableConceptMutation,
        CodeableReferenceMutation,
        CodingMutation,
    ),
)


schema = strawberry.federation.Schema(
    query=Query,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension, PaginationShareableExtension],
    config=StrawberryConfig(auto_camel_case=True),
    enable_federation_2=True,
    scalar_overrides={
        UploadedFile: Upload,
    },
)

# Patch pagination types from the schema after it's created
from core.common.pagination_patch import _patch_schema_types_after_creation  # noqa: E402

_patch_schema_types_after_creation(schema)
