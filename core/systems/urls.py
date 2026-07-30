from django.urls import path

from .apis import SystemHealthCheckApi

app_name = "systems"

urlpatterns = [
    path("health-check/", SystemHealthCheckApi.as_view(), name="health-check"),
]
