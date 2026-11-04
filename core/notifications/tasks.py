from celery import shared_task


@shared_task
def notification_dispatch_pending_task():
    from core.notifications.services.dispatch import notification_dispatch_pending

    return notification_dispatch_pending()
