import django_filters

from core.cookbook.models import Recipe


class RecipeFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Recipe.Status.choices)
    is_visible = django_filters.BooleanFilter(field_name="is_visible", lookup_expr="exact")
    title = django_filters.CharFilter(field_name="title", lookup_expr="icontains")
    order_by = django_filters.OrderingFilter(
        fields=[
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("title", "title"),
        ],
    )

    class Meta:
        model = Recipe
        fields = []
