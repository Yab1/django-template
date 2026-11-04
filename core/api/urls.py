from django.conf import settings
from django.urls import include, path
from django.urls.resolvers import URLResolver

urlpatterns: list[URLResolver] = [
    path("", include(("core.users.urls", "users"), namespace="users")),
    path("", include(("core.security.urls", "security"), namespace="security")),
    path(
        "authentication/",
        include(("core.authentication.urls", "authentication"), namespace="authentication"),
    ),
    path("systems/", include(("core.systems.urls", "systems"), namespace="systems")),
    path("", include(("core.notifications.urls", "notifications"), namespace="notifications")),
    path("", include(("core.files.urls", "files"), namespace="files")),
]

if getattr(settings, "COOKBOOK_ENABLED", True):
    urlpatterns.append(path("", include(("core.cookbook.urls", "cookbook"), namespace="cookbook")))
