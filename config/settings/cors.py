from config.env import env

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CORS_ORIGIN_WHITELIST = env.list("DJANGO_CORS_ORIGIN_WHITELIST", default=["http://localhost:3000"])
