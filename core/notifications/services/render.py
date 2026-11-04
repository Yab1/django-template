from django.template import Context, Template

from core.notifications.constants import CHANNEL_EMAIL, FORMAT_HTML, FORMAT_TEXT
from core.notifications.models import NotificationTemplate


def _fallback(*, channel: str, category: str, data: dict) -> tuple[str, str, str, None]:
    message = str(data.get("message") or category)
    subject = str(data.get("subject") or category.replace("_", " ").title())
    if channel == CHANNEL_EMAIL:
        body = f"<p>{message}</p>"
        return subject, body, FORMAT_HTML, None
    return subject, message, FORMAT_TEXT, None


def render_template(*, channel: str, category: str, data: dict) -> tuple[str, str, str, NotificationTemplate | None]:
    row = NotificationTemplate.objects.filter(
        channel=channel,
        category=category,
        locale="en",
        is_active=True,
        deleted_at__isnull=True,
    ).first()
    ctx = {str(k): str(v) if v is not None else "" for k, v in data.items()}
    if row is None:
        return _fallback(channel=channel, category=category, data=data)
    subject = Template(row.subject).render(Context(ctx))
    body = Template(row.body).render(Context(ctx))
    return subject, body, row.format, row
