from corsheaders.defaults import default_headers

from config.env import env

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CORS_ORIGIN_WHITELIST = env.list("DJANGO_CORS_ORIGIN_WHITELIST", default=["http://localhost:3000"])

# Custom request headers the frontend sends must be added to the CORS allow-list,
# otherwise the browser rejects the preflight even though the server answers OPTIONS 200.
# X-Organization-ID is read by OrganizationContextMiddleware on org-scoped endpoints.
CORS_ALLOW_HEADERS = (*default_headers, "x-organization-id")
