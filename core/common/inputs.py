import uuid
from typing import List

import strawberry
from strawberry.federation.schema_directives import Shareable


@strawberry.input(directives=[Shareable()])
class DeleteInput:
    id: uuid.UUID


@strawberry.input(directives=[Shareable()])
class BulkDeleteInput:
    ids: List[uuid.UUID]
