from django.urls import include, path
from django.urls.resolvers import URLResolver

urlpatterns: list[URLResolver] = [
    path("", include(("core.users.urls", "users"), namespace="users")),
    path(
        "authentication/",
        include(("core.authentication.urls", "authentication"), namespace="authentication"),
    ),
    path("systems/", include(("core.systems.urls", "systems"), namespace="systems")),
]
