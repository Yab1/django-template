from gqlauth.settings_type import GqlAuthSettings, email_field, first_name_field, last_name_field

from config.env import env

SDA_TOKEN_SECRET_KEY = env("SDA_TOKEN_SECRET_KEY", default=None)
SDA_TOKEN_AUDIENCE = env("SDA_TOKEN_AUDIENCE", default="strawberry")
SDA_JWT_ACCESS_TOKEN_LIFETIME = env.int("SDA_JWT_ACCESS_TOKEN_LIFETIME", default=300)  # 5 minutes
SDA_JWT_REFRESH_TOKEN_LIFETIME = env.int("SDA_JWT_REFRESH_TOKEN_LIFETIME", default=60 * 60 * 24 * 7)  # 7 days
SDA_ACTIVATION_PERIOD = env.int("SDA_ACTIVATION_PERIOD", default=60 * 60 * 24)  # 1 day
SDA_PASSWORD_RESET_TIMEOUT = env.int("SDA_PASSWORD_RESET_TIMEOUT", default=60 * 60)  # 1 hour

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@example.com")

# Disable captcha during initial setup
GQL_AUTH = GqlAuthSettings(
    LOGIN_REQUIRE_CAPTCHA=False,
    REGISTER_REQUIRE_CAPTCHA=False,
    ALLOW_LOGIN_NOT_VERIFIED=True,
    # Use email for login (no username in custom user model)
    LOGIN_FIELDS={email_field},
    # Fields allowed/required for register mutation — align with custom User
    REGISTER_MUTATION_FIELDS={email_field, first_name_field, last_name_field},
    # Use email in JWT payload (string, avoids UUID JSON issues)
    JWT_PAYLOAD_PK=email_field,
)
