from django.urls import path

from core.cookbook.apis import (
    RecipeCreateApi,
    RecipeDetailApi,
    RecipeListApi,
    RecipePublishApi,
    RecipeUpdateApi,
)

app_name = "cookbook"

urlpatterns = [
    path("cookbook/recipes/", RecipeListApi.as_view(), name="recipe-list"),
    path("cookbook/recipes/create/", RecipeCreateApi.as_view(), name="recipe-create"),
    path("cookbook/recipes/<uuid:id>/", RecipeDetailApi.as_view(), name="recipe-detail"),
    path("cookbook/recipes/<uuid:id>/update/", RecipeUpdateApi.as_view(), name="recipe-update"),
    path("cookbook/recipes/<uuid:id>/publish/", RecipePublishApi.as_view(), name="recipe-publish"),
]
