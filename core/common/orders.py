import strawberry
import strawberry_django

from core.common.models import BaseModel


@strawberry_django.order_type(BaseModel)
class CommonOrder:
    """Common order fields"""

    created_at: strawberry.auto
    updated_at: strawberry.auto
