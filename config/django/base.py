import os

from config.env import APPS_DIR, BASE_DIR, env

env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env.bool("DJANGO_DEBUG", default=True)  # type: ignore

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])  # pyright: ignore[reportArgumentType]

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])  # pyright: ignore[reportArgumentType]

CORS_ALLOWED_ORIGINS = env.list("DJANGO_CORS_ORIGIN_WHITELIST", default=[])  # pyright: ignore[reportArgumentType]

# Application definition
LOCAL_APPS = [
    "core.accounting.apps.AccountingConfig",
    "core.authentication.apps.AuthenticationConfig",
    "core.billing.apps.BillingConfig",
    "core.capacity.apps.CapacityConfig",
    "core.care.apps.CareConfig",
    "core.clinical.apps.ClinicalConfig",
    "core.clinical_audit.apps.ClinicalAuditConfig",
    "core.clinical_requests.apps.ClinicalRequestsConfig",
    "core.clinical_inventory.apps.ClinicalInventoryConfig",
    "core.common.apps.CommonConfig",
    "core.contents.apps.ContentsConfig",
    "core.devices.apps.DevicesConfig",
    "core.diagnostics.apps.DiagnosticsConfig",
    "core.documents.apps.DocumentsConfig",
    "core.encounters.apps.EncountersConfig",
    "core.entities.apps.EntitiesConfig",
    "core.events.apps.EventsConfig",
    "core.extensions.apps.ExtensionsConfig",
    "core.identities.apps.IdentitiesConfig",
    "core.individuals.apps.IndividualsConfig",
    "core.interop.apps.InteropConfig",
    "core.inventory.apps.InventoryConfig",
    "core.inventory_stock.apps.InventoryStockConfig",
    "core.procurement.apps.ProcurementConfig",
    "core.lab.apps.LabConfig",
    "core.medications.apps.MedicationsConfig",
    "core.notifications.apps.NotificationsConfig",
    "core.operations.apps.OperationsConfig",
    "core.order_sets.apps.OrderSetsConfig",
    "core.payments.apps.PaymentsConfig",
    "core.perioperative.apps.PerioperativeConfig",
    "core.pricing.apps.PricingConfig",
    "core.playground.apps.PlaygroundConfig",
    "core.questionnaires.apps.QuestionnairesConfig",
    "core.realtime.apps.RealtimeConfig",
    "core.resource_definition.apps.ResourceDefinitionConfig",
    "core.scheduling.apps.SchedulingConfig",
    "core.security.apps.SecurityConfig",
    "core.systems.apps.SystemsConfig",
    "core.teleradiology.apps.TeleradiologyConfig",
    "core.terminology.apps.TerminologyConfig",
    "core.users.apps.UsersConfig",
    "core.workflows.apps.WorkflowsConfig",
]

THIRD_PARTY_APPS: list[str] = [
    "corsheaders",
    "drf_spectacular",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "django_celery_beat",
    "django_celery_results",
    "django_extensions",
    "easyaudit",
    "guardian",
    "simple_history",
]
INSTALLED_APPS: list[str] = [
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    *THIRD_PARTY_APPS,
    *LOCAL_APPS,
]


MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.api.middleware.organization_context.OrganizationContextMiddleware",
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

# CHANNEL_LAYERS: set in config.settings.channels (Redis; required for Celery→WS push)


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.str("DJANGO_DB_NAME"),
        "USER": env.str("DJANGO_DB_USER"),
        "PASSWORD": env.str("DJANGO_DB_PASSWORD"),
        "HOST": env.str("DJANGO_DB_HOST"),
        "PORT": env.str("DJANGO_DB_PORT"),
        # Connection persistence is env-tunable but defaults OFF: on ASGI (many threads
        # per worker x 2 workers x blue+green) persistent connections multiply held
        # connections and exhaust the shared Postgres max_connections. Only raise this
        # once a pooler (pgbouncer) fronts Postgres or max_connections is sized for it.
        "CONN_MAX_AGE": env.int("DJANGO_DB_CONN_MAX_AGE", default=0),
        "CONN_HEALTH_CHECKS": env.bool("DJANGO_DB_CONN_HEALTH_CHECKS", default=False),
    },
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 6,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "core.users.validators.PwnedPasswordValidator",
        "OPTIONS": {
            "min_pwned_count": 1,
            "timeout_seconds": 2.0,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    {
        "NAME": "core.users.validators.PasswordComplexityValidator",
        "OPTIONS": {
            "max_length": 128,
        },
    },
    {
        "NAME": "core.users.validators.PasswordHistoryValidator",
        "OPTIONS": {
            "history_limit": 10,
        },
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
# No project-level static/ dir — app assets come from AppDirectoriesFinder.
# Static storage backend: config/settings/files_and_storages.py (MinIO when default storage is MinIO).

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

from config.settings.app import *  # noqa
from config.settings.cache import *  # noqa
from config.settings.channels import *  # noqa
from config.settings.celery import *  # noqa
from config.settings.cors import *  # noqa
from config.settings.debug_toolbar.settings import *  # noqa
from config.settings.debug_toolbar.setup import DebugToolbarSetup  # noqa
from config.settings.silk.settings import *  # noqa
from config.settings.silk.setup import SilkSetup  # noqa
from config.settings.files_and_storages import *  # noqa
from config.settings.logging import *  # noqa
from config.settings.rest_framework import *  # noqa
from config.settings.simple_jwt import *  # noqa
from config.settings.swagger import *  # noqa
from config.settings.sentry import *  # noqa
from config.settings.temporal import *  # noqa
from config.settings.notifications import *  # noqa

INSTALLED_APPS, MIDDLEWARE = DebugToolbarSetup.do_settings(INSTALLED_APPS, MIDDLEWARE)
INSTALLED_APPS, MIDDLEWARE = SilkSetup.do_settings(INSTALLED_APPS, MIDDLEWARE)
