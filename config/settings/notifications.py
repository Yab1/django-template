"""
Notification module settings.
All env vars are optional — adapters skip gracefully when credentials are absent.
"""

from config.env import env

# ── Twilio (SMS) ──────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID: str = env.str("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN: str = env.str("TWILIO_AUTH_TOKEN", default="")
TWILIO_FROM_NUMBER: str = env.str("TWILIO_FROM_NUMBER", default="")
TWILIO_WEBHOOK_AUTH_TOKEN: str = env.str("TWILIO_WEBHOOK_AUTH_TOKEN", default=TWILIO_AUTH_TOKEN)

# ── FCM (Android push) ────────────────────────────────────────────────────────
# Legacy HTTP API — server key from Firebase console.
# Migrate to FCM v1 (service account JSON) when google-auth is added to deps.
FCM_SERVER_KEY: str = env.str("FCM_SERVER_KEY", default="")
# FCM v1 fields (future):
FCM_PROJECT_ID: str = env.str("FCM_PROJECT_ID", default="")
FCM_SERVICE_ACCOUNT_FILE: str = env.str("FCM_SERVICE_ACCOUNT_FILE", default="")

# ── APNs (iOS push) ───────────────────────────────────────────────────────────
# Requires uv add h2 (HTTP/2 support for httpx).
APNS_KEY_FILE: str = env.str("APNS_KEY_FILE", default="")
APNS_KEY_ID: str = env.str("APNS_KEY_ID", default="")
APNS_TEAM_ID: str = env.str("APNS_TEAM_ID", default="")
APNS_BUNDLE_ID: str = env.str("APNS_BUNDLE_ID", default="")
APNS_USE_SANDBOX: bool = env.bool("APNS_USE_SANDBOX", default=True)

# ── Email transport (Django EMAIL_* settings) ─────────────────────────────────
# DJANGO_EMAIL_BACKEND options:
#   console  → django.core.mail.backends.console.EmailBackend  (local dev)
#   smtp     → django.core.mail.backends.smtp.EmailBackend     (production SMTP)
#   ses      → django_ses.SESBackend                           (AWS SES, requires django-ses)
#   locmem   → django.core.mail.backends.locmem.EmailBackend   (tests — set in config/django/test.py)
EMAIL_BACKEND: str = env.str(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST: str = env.str("DJANGO_EMAIL_HOST", default="localhost")
EMAIL_PORT: int = env.int("DJANGO_EMAIL_PORT", default=587)
EMAIL_USE_TLS: bool = env.bool("DJANGO_EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL: bool = env.bool("DJANGO_EMAIL_USE_SSL", default=False)
EMAIL_HOST_USER: str = env.str("DJANGO_EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD: str = env.str("DJANGO_EMAIL_HOST_PASSWORD", default="")
EMAIL_TIMEOUT: int = env.int("DJANGO_EMAIL_TIMEOUT", default=10)
NOTIFICATION_EMAIL_FROM: str = env.str("NOTIFICATION_EMAIL_FROM", default="noreply@localhost")

# ── Telegram ─────────────────────────────────────────────────────────────────
# Bot token from @BotFather. No PHI in body — deep-link only.
TELEGRAM_BOT_TOKEN: str = env.str("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_PARSE_MODE: str = env.str("TELEGRAM_PARSE_MODE", default="HTML")

# ── WhatsApp ──────────────────────────────────────────────────────────────────
# Supported providers: "twilio" (sandbox/approved number) or "meta" (Cloud API).
WHATSAPP_PROVIDER: str = env.str("WHATSAPP_PROVIDER", default="twilio")
# Twilio WhatsApp — uses existing TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN
WHATSAPP_FROM_NUMBER: str = env.str("WHATSAPP_FROM_NUMBER", default="")
# Meta WhatsApp Cloud API
META_WHATSAPP_PHONE_NUMBER_ID: str = env.str("META_WHATSAPP_PHONE_NUMBER_ID", default="")
META_WHATSAPP_ACCESS_TOKEN: str = env.str("META_WHATSAPP_ACCESS_TOKEN", default="")

# ── Fax ───────────────────────────────────────────────────────────────────────
# Supported providers: "twilio"
FAX_PROVIDER: str = env.str("FAX_PROVIDER", default="twilio")
FAX_FROM_NUMBER: str = env.str("FAX_FROM_NUMBER", default="")

# ── Pager ─────────────────────────────────────────────────────────────────────
# Supported providers: "twilio_sms" (SMS-to-pager gateway)
PAGER_PROVIDER: str = env.str("PAGER_PROVIDER", default="twilio_sms")
PAGER_FROM_NUMBER: str = env.str("PAGER_FROM_NUMBER", default=TWILIO_FROM_NUMBER)

# ── Deep-link tokens (non-secure channel bodies: SMS, email, pager) ───────────
NOTIFICATION_DEEP_LINK_BASE_URL: str = env.str("NOTIFICATION_DEEP_LINK_BASE_URL", default="http://localhost:3000")
NOTIFICATION_DEEP_LINK_TOKEN_TTL_SECONDS: int = env.int("NOTIFICATION_DEEP_LINK_TOKEN_TTL_SECONDS", default=900)
