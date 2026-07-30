import os
import sys

from config.env import APPS_DIR, BASE_DIR, env

env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env.bool("DJANGO_DEBUG", default=True)  # type: ignore

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

CORS_ALLOWED_ORIGINS = env.list("DJANGO_CORS_ORIGIN_WHITELIST", default=[])

# Application definition
LOCAL_APPS = [
    "core.common.apps.CommonConfig",
    "core.users.apps.UsersConfig",
    "core.seed.apps.SeedConfig",
    "core.fhir.apps.FhirConfig",
    "core.health_check.apps.HealthCheckConfig",
]

THIRD_PARTY_APPS: list[str] = [
    "corsheaders",
    "django_celery_beat",
    "django_celery_results",
    "django_extensions",
    "django_filters",
    "django_guid",
    "easyaudit",
    "simple_history",
    "strawberry_django",
    "django_grpc",
    "django_tenant_db_router",
]
INSTALLED_APPS: list[str] = [
    "daphne",
    "unfold",
    "unfold.contrib.simple_history",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    *THIRD_PARTY_APPS,
    *LOCAL_APPS,
]


MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django_guid.middleware.guid_middleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_tenant_db_router.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "easyaudit.middleware.easyaudit.EasyAuditMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(APPS_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DB_NAME"),
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": env.str("DB_HOST"),
        "PORT": env.str("DB_PORT"),
    },
}

# Database routing for multi-tenancy
DATABASE_ROUTERS = [
    "django_tenant_db_router.routers.TenantDatabaseRouter",
]

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "users.User"

API_AUTH_TYPE = "JWT"

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Addis_Ababa"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


APP_DOMAIN = env("APP_DOMAIN", default="http://localhost:7000")  # type: ignore

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

from config.settings.unfold import *  # noqa

from config.settings.logging import *  # noqa
from config.settings.guid import *  # noqa
from config.settings.sentry import *  # noqa

from config.settings.cors import *  # noqa

from config.settings.files_and_storages import *  # noqa

from config.settings.gql import *  # noqa
from config.settings.grpc import *  # noqa
from config.settings.tenant import *  # noqa

from config.settings.celery import *  # noqa

from config.settings.debug_toolbar.settings import *  # noqa
from config.settings.debug_toolbar.setup import DebugToolbarSetup  # noqa

INSTALLED_APPS, MIDDLEWARE = DebugToolbarSetup.do_settings(INSTALLED_APPS, MIDDLEWARE)

# Ensure generated gRPC stubs package (tenant.v1) can be imported
sys.path.insert(0, os.path.join(BASE_DIR, "core", "grpc", "protos"))
