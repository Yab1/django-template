from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from config.env import env

"""
UNFOLD Django Admin Customization Settings

This file contains configuration for the Unfold Django admin UI extension.

- For configuring icons, you can refer to the available icon set here:
    see: https://fonts.google.com/icons

- For details on all available options and documentation, visit:
    see: https://unfoldadmin.com/docs/

Adjust the settings below to customize the look and feel of your Django admin using Unfold.
"""


UNFOLD = {
    "SITE_TITLE": "EHR Django Template",
    "SITE_HEADER": "EHR Django Template",
    "SITE_SUBHEADER": "Admin Dashboard",
    "SITE_URL": "/",
    "SITE_ICON": {
        "light": lambda request: static("icon.png"),
        "dark": lambda request: static("icon.png"),
    },
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/x-icon",
            "href": lambda request: static("icon.png"),
        },
    ],
    "SITE_DROPDOWN": [
        {
            "icon": "graph_7",
            "title": _("Apollo Router"),
            "link": env("APOLLO_ROUTER_URL", default="http://localhost:4000"),
        },
        {
            "icon": "graph_1",
            "title": _("GraphQL Playground"),
            "link": env("GRAPHQL_PLAYGROUND_URL", default="http://localhost:7004/graphql/"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,
    "ENVIRONMENT": "config.settings.unfold.environment_callback",  # environment name in header
    "ENVIRONMENT_TITLE_PREFIX": "config.settings.unfold.environment_title_prefix_callback",  # title prefix
    "LOGIN": {
        "image": lambda request: static("login-bg.jpg"),
    },
    "STYLES": [
        lambda request: static("css/style.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/script.js"),
    ],
    "BORDER_RADIUS": "6px",
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .002 247.839)",
            "100": "oklch(96.7% .003 264.542)",
            "200": "oklch(92.8% .006 264.531)",
            "300": "oklch(87.2% .01 258.338)",
            "400": "oklch(70.7% .022 261.325)",
            "500": "oklch(55.1% .027 264.364)",
            "600": "oklch(44.6% .03 256.802)",
            "700": "oklch(37.3% .034 259.733)",
            "800": "oklch(27.8% .033 256.848)",
            "900": "oklch(21% .034 264.665)",
            "950": "oklch(13% .028 261.692)",
        },
        "primary": {
            "50": "oklch(97.5% .015 150)",
            "100": "oklch(94.5% .035 150)",
            "200": "oklch(89.5% .065 150)",
            "300": "oklch(82% .12 150)",
            "400": "oklch(70% .20 150)",
            "500": "oklch(60% .25 150)",
            "600": "oklch(52% .28 150)",
            "700": "oklch(45% .25 150)",
            "800": "oklch(38% .20 150)",
            "900": "oklch(32% .16 150)",
            "950": "oklch(24% .14 150)",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {
                "en": "🇬🇧",
            },
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": _("Navigation"),
                "separator": False,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        "permission": lambda request: request.user.is_superuser,
                    },
                    # {
                    #     "title": _("Playground Test"),
                    #     "icon": "person",
                    #     "link": reverse_lazy("admin:playground_playground_changelist"),
                    #     "permission": lambda request: request.user.is_superuser,
                    # },
                    # {
                    #     "title": _("Shops"),
                    #     "icon": "store",
                    #     "link": reverse_lazy("admin:shop_shop_changelist"),
                    #     "permission": lambda request: request.user.is_superuser,
                    # },
                    # {
                    #     "title": _("Patients"),
                    #     "icon": "person",
                    #     "link": reverse_lazy("admin:patients_patient_changelist"),
                    #     "permission": lambda request: request.user.is_superuser,
                    # },
                ],
            },
            {
                "title": _("FHIR Terminology"),
                "separator": False,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Codings"),
                        "icon": "code",
                        "link": reverse_lazy("admin:fhir_coding_changelist"),
                    },
                    {
                        "title": _("Codeable Concepts"),
                        "icon": "category",
                        "link": reverse_lazy("admin:fhir_codeableconcept_changelist"),
                    },
                ],
            },
            {
                "title": _("Users & Groups"),
                "separator": False,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "account_circle",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("Celery Tasks"),
                "separator": False,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Clocked"),
                        "icon": "hourglass_bottom",
                        "link": reverse_lazy("admin:django_celery_beat_clockedschedule_changelist"),
                    },
                    {
                        "title": _("Crontabs"),
                        "icon": "update",
                        "link": reverse_lazy("admin:django_celery_beat_crontabschedule_changelist"),
                    },
                    {
                        "title": _("Intervals"),
                        "icon": "timer",
                        "link": reverse_lazy("admin:django_celery_beat_intervalschedule_changelist"),
                    },
                    {
                        "title": _("Periodic tasks"),
                        "icon": "task",
                        "link": reverse_lazy("admin:django_celery_beat_periodictask_changelist"),
                    },
                    {
                        "title": _("Solar events"),
                        "icon": "event",
                        "link": reverse_lazy("admin:django_celery_beat_solarschedule_changelist"),
                    },
                ],
            },
            {
                "title": _("Easy Audit"),
                "separator": False,
                "collapsible": True,
                "items": [
                    {
                        "title": _("CRUD events"),
                        "icon": "edit",
                        "link": reverse_lazy("admin:easyaudit_crudevent_changelist"),
                    },
                    {
                        "title": _("Login events"),
                        "icon": "login",
                        "link": reverse_lazy("admin:easyaudit_loginevent_changelist"),
                    },
                    {
                        "title": _("Request events"),
                        "icon": "http",
                        "link": reverse_lazy("admin:easyaudit_requestevent_changelist"),
                    },
                ],
            },
        ],
    },
}


def environment_callback(request):
    """
    Callback has to return a list of two values representing text value and the color
    type of the label displayed in top right corner.
    Reads DJANGO_ENVIRONMENT from .env file.
    """
    try:
        env_name = env.str("DJANGO_ENVIRONMENT", default="development").upper()  # type: ignore
    except Exception:
        env_name = "DEVELOPMENT"

    # Map environment to color
    color_map = {
        "DEVELOPMENT": "info",
        "DEV": "info",
        "STAGING": "warning",
        "STAGE": "warning",
        "PRODUCTION": "danger",
        "PROD": "danger",
        "TEST": "success",
    }

    return [env_name, color_map.get(env_name, "info")]  # info, danger, warning, success


def environment_title_prefix_callback(request):
    """
    Returns prefix for browser tab title (e.g., "[DEV]" or "[PROD]").
    Reads DJANGO_ENVIRONMENT from .env file.
    """
    try:
        env_name = env.str("DJANGO_ENVIRONMENT", default="development").upper()  # type: ignore
    except Exception:
        env_name = "DEVELOPMENT"

    prefix_map = {
        "DEVELOPMENT": "[DEV]",
        "DEV": "[DEV]",
        "STAGING": "[STAGING]",
        "STAGE": "[STAGING]",
        "PRODUCTION": "[PROD]",
        "PROD": "[PROD]",
        "TEST": "[TEST]",
    }

    return prefix_map.get(env_name, "[DEV]")
