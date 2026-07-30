import strawberry
from strawberry.federation.schema_directives import Shareable


@strawberry.type(directives=[Shareable()])
class DeleteType:
    success: bool
    message: str


@strawberry.type(directives=[Shareable()])
class BulkDeleteType:
    success: bool
    message: str
    count: int
