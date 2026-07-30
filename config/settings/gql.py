from config.env import env

# Default settings for Strawberry Django
# https://strawberry.rocks/docs/django/guide/settings

STRAWBERRY_DJANGO = {
    "FIELD_DESCRIPTION_FROM_HELP_TEXT": True,
    "TYPE_DESCRIPTION_FROM_MODEL_DOCSTRING": True,
    "MUTATIONS_DEFAULT_ARGUMENT_NAME": "input",
    "MUTATIONS_DEFAULT_HANDLE_DJANGO_ERRORS": True,
    "GENERATE_ENUMS_FROM_CHOICES": True,
    "PAGINATION_DEFAULT_LIMIT": 10,
}


ENABLE_GRAPHIQL = env.bool("DJANGO_DEBUG", default=True)
