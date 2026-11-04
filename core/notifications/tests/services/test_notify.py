import pytest
from django.core import mail

from core.notifications.constants import CHANNEL_EMAIL, CHANNEL_IN_APP, STATUS_SENT
from core.notifications.models import NotificationDelivery
from core.notifications.services import notification_notify
from core.users.models import User


@pytest.mark.django_db
class NotificationNotifyTests:
    def test_welcome_writes_inbox_and_email(self, settings, django_capture_on_commit_callbacks):
        settings.NOTIFICATION_DISPATCH_ENABLED = True
        settings.NOTIFICATION_EMAIL_ENABLED = True
        settings.NOTIFICATION_IN_APP_ENABLED = True
        settings.MAIL_ENABLED = True
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        user = User.objects.create_user(
            username="notify_user",
            email="notify@example.com",
            password="NotAWeakPassw0rd!",
            phone_number=251911000001,
        )
        with django_capture_on_commit_callbacks(execute=True):
            rows = notification_notify(
                user=user,
                category="welcome",
                event_code="user.created",
                idempotency_key=f"test.welcome:{user.id}",
                data={"message": "Welcome to django-template."},
            )
        channels = {row.channel: row for row in rows}
        assert CHANNEL_IN_APP in channels
        assert CHANNEL_EMAIL in channels
        inbox = NotificationDelivery.objects.get(pk=channels[CHANNEL_IN_APP].id)
        email_row = NotificationDelivery.objects.get(pk=channels[CHANNEL_EMAIL].id)
        assert inbox.status == STATUS_SENT
        assert email_row.status == STATUS_SENT
        assert len(mail.outbox) == 1
        assert "Welcome" in mail.outbox[0].subject or "Welcome" in mail.outbox[0].body

    def test_idempotency_replays(self, settings):
        settings.NOTIFICATION_DISPATCH_ENABLED = False
        user = User.objects.create_user(
            username="notify_user2",
            email="notify2@example.com",
            password="NotAWeakPassw0rd!",
            phone_number=251911000002,
        )
        key = f"test.idem:{user.id}"
        first = notification_notify(
            user=user,
            category="status",
            event_code="test.ping",
            idempotency_key=key,
            channels=[CHANNEL_IN_APP],
            data={"message": "ping"},
        )
        second = notification_notify(
            user=user,
            category="status",
            event_code="test.ping",
            idempotency_key=key,
            channels=[CHANNEL_IN_APP],
            data={"message": "ping"},
        )
        assert first[0].id == second[0].id
        assert NotificationDelivery.objects.filter(idempotency_key=key).count() == 1
