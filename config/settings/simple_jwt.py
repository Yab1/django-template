"""
djangorestframework-simplejwt configuration.

Secure defaults: short-lived access tokens, refresh rotation,
blacklist after rotation, and optional dedicated signing key via DJANGO_JWT_SIGNING_KEY.
"""

from datetime import timedelta

from config.env import env

# Dedicated JWT signing key (recommended for production). Falls back to SECRET_KEY if unset.
JWT_SIGNING_KEY = env.str(
    "DJANGO_JWT_SIGNING_KEY",
    default=env.str("DJANGO_SECRET_KEY"),  # pyright: ignore[reportArgumentType]
)

JWT_ACCESS_TOKEN_LIFETIME_MINUTES: int = int(env.int("DJANGO_JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60))  # pyright: ignore[reportArgumentType]
JWT_REFRESH_TOKEN_LIFETIME_DAYS: int = int(env.int("DJANGO_JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=1))  # pyright: ignore[reportArgumentType]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_TOKEN_LIFETIME_MINUTES),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=JWT_REFRESH_TOKEN_LIFETIME_DAYS),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "CHECK_USER_IS_ACTIVE": True,
    "TOKEN_OBTAIN_SERIALIZER": "core.authentication.serializers.CustomTokenObtainPairSerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "core.authentication.serializers.CustomTokenBlacklistSerializer",
}
