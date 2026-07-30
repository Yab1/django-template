# pyright: reportArgumentType=false

import os

from config.env import BASE_DIR, env

# Media
MEDIA_ROOT_NAME = "media"
MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_ROOT_NAME)
MEDIA_URL = f"/{MEDIA_ROOT_NAME}/"

# Storage
STORAGES = {
    "default": {
        "BACKEND": env.str(
            "DJANGO_DEFAULT_FILE_STORAGE",
            default="minio_storage.storage.MinioMediaStorage",
        ),
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Minio
MINIO_STORAGE_ENDPOINT = env.str("MINIO_STORAGE_ENDPOINT")
MINIO_STORAGE_ACCESS_KEY = env.str("MINIO_ROOT_USER")
MINIO_STORAGE_SECRET_KEY = env.str("MINIO_ROOT_PASSWORD")
MINIO_STORAGE_USE_HTTPS = env.bool("MINIO_STORAGE_USE_HTTPS", default=False)
MINIO_STORAGE_MEDIA_BUCKET_NAME = env.str("MINIO_STORAGE_MEDIA_BUCKET_NAME")
MINIO_STORAGE_STATIC_BUCKET_NAME = env.str("MINIO_STORAGE_STATIC_BUCKET_NAME")
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True
MINIO_STORAGE_STATIC_URL = env.str("MINIO_STORAGE_STATIC_URL", default="")

# AWS S3 settings (for production)
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME")
AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN")

DEFAULT_BACKEND = STORAGES["default"]["BACKEND"]

if "s3" in DEFAULT_BACKEND.lower():
    FILE_STORAGE_ENDPOINT = AWS_S3_CUSTOM_DOMAIN

elif "minio" in DEFAULT_BACKEND.lower():
    FILE_STORAGE_ENDPOINT = MINIO_STORAGE_ENDPOINT
    STORAGES["staticfiles"] = {
        "BACKEND": "minio_storage.storage.MinioStaticStorage",
    }
    if not MINIO_STORAGE_STATIC_URL:
        scheme = "https" if MINIO_STORAGE_USE_HTTPS else "http"
        MINIO_STORAGE_STATIC_URL = f"{scheme}://{MINIO_STORAGE_ENDPOINT}/{MINIO_STORAGE_STATIC_BUCKET_NAME}"
    # Admin / {% static %} must match where collectstatic uploaded (same host as MINIO_STORAGE_STATIC_URL).
    STATIC_URL = f"{MINIO_STORAGE_STATIC_URL.rstrip('/')}/"

else:
    FILE_STORAGE_ENDPOINT = env.str("DJANGO_FILE_STORAGE_ENDPOINT")
    STORAGES["staticfiles"] = {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    }
