from corsheaders.defaults import default_headers

from config.env import env

CORS_ENABLED = env.bool("DJANGO_CORS_ENABLED", default=True)
CORS_ALLOW_CREDENTIALS = env.bool("DJANGO_CORS_ALLOW_CREDENTIALS", default=True)
CORS_ALLOW_ALL_ORIGINS = env.bool("DJANGO_CORS_ALLOW_ALL", default=False) if CORS_ENABLED else False
# Browser forbids Access-Control-Allow-Origin: * with credentials.
if CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOW_CREDENTIALS = False

_cors_origins = env.list("DJANGO_CORS_ORIGIN_WHITELIST", default=["http://localhost:3000"])
if not CORS_ENABLED:
    _cors_origins = []

CORS_ORIGIN_WHITELIST = _cors_origins
CORS_ALLOWED_ORIGINS = _cors_origins

# Custom request headers the frontend sends must be added to the CORS allow-list,
# otherwise the browser rejects the preflight even though the server answers OPTIONS 200.
CORS_ALLOW_HEADERS = (*default_headers, "x-organization-id", "idempotency-key")
