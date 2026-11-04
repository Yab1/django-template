from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from core.notifications.adapters.base import Outbound
from core.notifications.constants import FORMAT_HTML


class EmailSender:
    def send(self, *, outbound: Outbound) -> str | None:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "") or settings.NOTIFICATION_EMAIL_FROM
        msg = EmailMultiAlternatives(
            subject=outbound.subject,
            body=outbound.body if outbound.format != FORMAT_HTML else "",
            from_email=from_email,
            to=[outbound.to],
        )
        if outbound.format == FORMAT_HTML:
            msg.attach_alternative(outbound.body, "text/html")
            if not msg.body:
                msg.body = outbound.subject
        msg.send(fail_silently=False)
        return None
