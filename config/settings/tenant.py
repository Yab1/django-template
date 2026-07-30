"""
Multi-tenant database configuration for Patient Service.

This module configures the django-tenant-db-router package for per-tenant
database routing and management.
"""

from config.env import env

# Prefix for tenant database names
TENANT_DB_PREFIX = env.str("TENANT_DB_PREFIX", default="ehr_patient_tenant_")

# Auto-create tenant databases (set to False if databases are pre-provisioned)
TENANT_AUTO_CREATE_DATABASE = env.bool("TENANT_AUTO_CREATE_DATABASE", default=False)

# ==========================================================================
# TEMPORARY: Disable tenant routing until authentication is implemented
# Set to True to enable tenant routing (requires proper authentication setup)
TENANT_ROUTING_ENABLED = env.bool("TENANT_ROUTING_ENABLED", default=False)
# ==========================================================================


def tenant_db_config_provider(db_name: str) -> dict:
    """
    Provide database configuration for a given tenant database.

    This function is called by django-tenant-db-router when a tenant database
    needs to be configured. It returns a Django DATABASES dict for the tenant.

    By default, it uses the same credentials as the default database but with
    a different database name. Override this in production to use different
    credentials per tenant if needed.

    Args:
        db_name: The name of the tenant database

    Returns:
        Django DATABASES configuration dict
    """
    from django.conf import settings

    # Get the default database configuration as a template
    default_db = settings.DATABASES.get("default", {})

    # Copy the default config and override with tenant-specific values
    return {
        "ENGINE": default_db.get("ENGINE", "django.db.backends.postgresql"),
        "NAME": db_name,
        "USER": env.str("DB_USER"),
        "PASSWORD": env.str("DB_PASSWORD"),
        "HOST": env.str("DB_HOST"),
        "PORT": env.str("DB_PORT"),
        "ATOMIC_REQUESTS": default_db.get("ATOMIC_REQUESTS", True),
        "AUTOCOMMIT": default_db.get("AUTOCOMMIT", True),
        "CONN_MAX_AGE": default_db.get("CONN_MAX_AGE", 600),
        "CONN_HEALTH_CHECKS": default_db.get("CONN_HEALTH_CHECKS", False),
        "OPTIONS": default_db.get("OPTIONS", {}),
        "TIME_ZONE": default_db.get("TIME_ZONE", None),
        "DISABLE_SERVER_SIDE_CURSORS": default_db.get("DISABLE_SERVER_SIDE_CURSORS", False),
    }


def tenant_resolver(request) -> "TenantLite | None":  # type: ignore # noqa: F821
    """
        Resolve tenant from an HTTP request.

        This function extracts tenant information from the request and returns
        a TenantLite object that will be used for database routing.

        Strategy:
        1. Check for X-Tenant-Slug header (for API clients)
        2. Extract subdomain from host (e.g., acme.example.com -> acme)
        3. Return None for non-tenant requests (will use default database)

        Args:
            request: Django HttpRequest object

        Returns:
            TenantLite object with tenant info, or None for default database

    # ==========================================================================

        NOTE: Tenant routing is temporarily disabled until authentication is implemented.
        Set TENANT_ROUTING_ENABLED=True in environment to enable tenant routing.
    """
    # TEMPORARY: Always use default database until authentication is implemented
    # TODO: Re-enable tenant routing once authentication is properly set up
    if not TENANT_ROUTING_ENABLED:
        return None
    # ==========================================================================

    from django_tenant_db_router import TenantLite  # pyright: ignore[reportMissingImports]

    # Strategy 1: Check for explicit tenant header
    tenant_slug = request.headers.get("X-Tenant-Slug")

    if not tenant_slug:
        # Strategy 2: Extract from subdomain
        host = request.get_host().split(":")[0]
        parts = host.split(".")

        # Only use subdomain if we have at least 2 parts (subdomain.domain)
        # and the subdomain is not 'www' or 'api'
        if len(parts) >= 2:
            subdomain = parts[0]
            if subdomain not in ("www", "api", "localhost", "127"):
                tenant_slug = subdomain

    if not tenant_slug:
        return None

    db_name = f"{TENANT_DB_PREFIX}{tenant_slug}"
    return TenantLite(name=tenant_slug, db_name=db_name)


# Register the custom resolver and config provider
TENANT_RESOLVER = tenant_resolver
TENANT_DB_CONFIG_PROVIDER = tenant_db_config_provider
