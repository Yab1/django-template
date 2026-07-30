from config.env import env

SILK_ENABLED = env.bool("DJANGO_SILK_ENABLED", default=False)  # type: ignore

# Require Django login to access /silk/
SILKY_AUTHENTICATION = True
# Restrict to staff users only
SILKY_AUTHORISATION = True

# Limit stored body sizes to avoid large DB writes during heavy use
SILKY_MAX_REQUEST_BODY_SIZE = 10 * 1024  # 10 KB
SILKY_MAX_RESPONSE_BODY_SIZE = 10 * 1024  # 10 KB

# Record how long Silk itself takes per request (useful during development)
SILKY_META = True
