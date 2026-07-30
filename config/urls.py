from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser

from core.systems.apis import SystemHealthCheckApi

docs_permission_classes = [IsAdminUser]
docs_authentication_classes = [SessionAuthentication]

api_v1_patterns = [
    path("", include(("core.api.urls", "api"), namespace="api")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    # Infra probes (LB / k8s) — outside versioned API
    path("health/", SystemHealthCheckApi.as_view(), name="health"),
    path("api/v1/", include(api_v1_patterns)),
    path(
        "schema/",
        SpectacularAPIView.as_view(
            authentication_classes=docs_authentication_classes,
            permission_classes=docs_permission_classes,
        ),
        name="schema",
    ),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema",
            authentication_classes=docs_authentication_classes,
            permission_classes=docs_permission_classes,
        ),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(
            url_name="schema",
            authentication_classes=docs_authentication_classes,
            permission_classes=docs_permission_classes,
        ),
        name="schema-redoc",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from config.settings.debug_toolbar.setup import DebugToolbarSetup  # noqa
from config.settings.silk.setup import SilkSetup  # noqa

urlpatterns = DebugToolbarSetup.do_urls(urlpatterns)
urlpatterns = SilkSetup.do_urls(urlpatterns)
