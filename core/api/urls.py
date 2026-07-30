from django.urls import include, path
from django.urls.resolvers import URLResolver

urlpatterns: list[URLResolver] = [
    path("", include(("core.users.urls", "users"), namespace="users")),
]
