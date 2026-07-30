from django.contrib.contenttypes.models import ContentType


def content_type_from_natural_key(*, natural_key: str) -> ContentType:
    app_label, model = natural_key.split(".", 1)
    return ContentType.objects.get(app_label=app_label, model=model)
