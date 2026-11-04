from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.cookbook.constants import OPENAPI_TAG_COOKBOOK
from core.cookbook.serializers import RecipeOutputSerializer
from core.cookbook.services import recipe_publish


class RecipePublishApi(AuthorizedAPIView):
    """Publish a draft recipe. Not a CRUD update — status has its own verb."""

    authorization_resource_code = "Recipe"
    authorization_action = "cookbook:recipe:publish"

    OutputSerializer = RecipeOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RecipePublishSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="cookbook_recipe_publish",
        tags=[OPENAPI_TAG_COOKBOOK],
        request=None,
        responses={200: SuccessResponseSerializer},
        summary="Publish recipe",
    )
    def post(self, request, id: UUID) -> Response:
        obj = recipe_publish(recipe_id=id, requesting_user=request.user)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)
