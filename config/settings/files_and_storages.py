# pyright: reportArgumentType=false

import os

from config.env import BASE_DIR, env

# Media
MEDIA_ROOT_NAME = "media"
MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_ROOT_NAME)
MEDIA_URL = f"/{MEDIA_ROOT_NAME}/"

FILES_ENABLED = env.bool("DJANGO_FILES_ENABLED", default=True)

_STORAGE_DRIVER_BACKENDS = {
    "minio": "core.files.storage.SseMinioMediaStorage",
    "s3": "storages.backends.s3boto3.S3Boto3Storage",
    "local": "django.core.files.storage.FileSystemStorage",
}

STORAGE_DRIVER = env.str("DJANGO_STORAGE_DRIVER", default="minio").strip().lower()
_explicit_backend = env.str("DJANGO_DEFAULT_FILE_STORAGE", default="").strip()
if not FILES_ENABLED:
    _default_backend = "django.core.files.storage.FileSystemStorage"
elif _explicit_backend:
    _default_backend = _explicit_backend
else:
    _default_backend = _STORAGE_DRIVER_BACKENDS.get(STORAGE_DRIVER, _STORAGE_DRIVER_BACKENDS["minio"])

FILE_MAX_BYTES = env.int("DJANGO_FILE_MAX_BYTES", default=10 * 1024 * 1024)
DATA_UPLOAD_MAX_MEMORY_SIZE = FILE_MAX_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = FILE_MAX_BYTES
FILE_ALLOWED_TYPES = [
    item.strip().lower()
    for item in env.list(
        "DJANGO_FILE_ALLOWED_TYPES",
        default=["image/jpeg", "image/png", "image/webp", "application/pdf"],
    )
    if item.strip()
]

# ClamAV scan on upload (clamd INSTREAM). When on, uploads fail while clamd is down.
CLAMAV_ENABLED = env.bool("CLAMAV_ENABLED", default=False)
CLAMAV_HOST = env.str("CLAMAV_HOST", default="localhost")
CLAMAV_PORT = env.int("CLAMAV_PORT", default=3310)
CLAMAV_TIMEOUT = env.int("CLAMAV_TIMEOUT", default=30)

# Storage — media via driver; static always WhiteNoise (never MinIO).
STORAGES = {
    "default": {
        "BACKEND": _default_backend,
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Minio (required when DJANGO_STORAGE_DRIVER=minio)
MINIO_STORAGE_ENDPOINT = env.str("MINIO_STORAGE_ENDPOINT", default="")
MINIO_STORAGE_ACCESS_KEY = env.str("MINIO_ROOT_USER", default="")
MINIO_STORAGE_SECRET_KEY = env.str("MINIO_ROOT_PASSWORD", default="")
MINIO_STORAGE_USE_HTTPS = env.bool("MINIO_STORAGE_USE_HTTPS", default=False)
MINIO_STORAGE_MEDIA_BUCKET_NAME = env.str("MINIO_STORAGE_MEDIA_BUCKET_NAME", default="")
MINIO_STORAGE_STATIC_BUCKET_NAME = env.str("MINIO_STORAGE_STATIC_BUCKET_NAME", default="")
MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True
# Library default is GET_ONLY, which publishes every object. Media stays private.
MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY = "NONE"
MINIO_STORAGE_STATIC_URL = env.str("MINIO_STORAGE_STATIC_URL", default="")
MINIO_STORAGE_MEDIA_URL = env.str("MINIO_STORAGE_MEDIA_URL", default="")

# AWS S3 settings (for production / DJANGO_STORAGE_DRIVER=s3)
AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_CUSTOM_DOMAIN = env.str("AWS_S3_CUSTOM_DOMAIN", default="")

DEFAULT_BACKEND = STORAGES["default"]["BACKEND"]

if "s3" in DEFAULT_BACKEND.lower():
    FILE_STORAGE_ENDPOINT = AWS_S3_CUSTOM_DOMAIN
    AWS_S3_OBJECT_PARAMETERS = {"ServerSideEncryption": "AES256"}

elif "minio" in DEFAULT_BACKEND.lower():
    FILE_STORAGE_ENDPOINT = MINIO_STORAGE_ENDPOINT
    scheme = "https" if MINIO_STORAGE_USE_HTTPS else "http"
    if not MINIO_STORAGE_MEDIA_URL and MINIO_STORAGE_ENDPOINT and MINIO_STORAGE_MEDIA_BUCKET_NAME:
        MINIO_STORAGE_MEDIA_URL = f"{scheme}://{MINIO_STORAGE_ENDPOINT}/{MINIO_STORAGE_MEDIA_BUCKET_NAME}"

else:
    FILE_STORAGE_ENDPOINT = env.str("DJANGO_FILE_STORAGE_ENDPOINT", default="")
