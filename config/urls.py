from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import AsyncGraphQLView

from config.settings.gql import ENABLE_GRAPHIQL

from .schema import schema


def trigger_error(request):
    """Test route to trigger an error for GlitchTip verification."""
    division_by_zero = 1 / 0  # noqa: F841
    return


urlpatterns = [
    path(
        "graphql/",
        csrf_exempt(
            AsyncGraphQLView.as_view(
                schema=schema,
                graphiql=ENABLE_GRAPHIQL,
                multipart_uploads_enabled=True,
            ),
        ),
        name="graphql",
    ),
    path("glitchtip-debug/", trigger_error, name="glitchtip-debug"),
    path("", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from config.settings.debug_toolbar.setup import DebugToolbarSetup  # noqa

urlpatterns = DebugToolbarSetup.do_urls(urlpatterns)
