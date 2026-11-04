from django.urls import path

from core.notifications.apis import (
    NotificationDeliveryGetApi,
    NotificationDeliveryListApi,
    NotificationDeliveryRetryApi,
    NotificationInboxListApi,
    NotificationPreferenceEffectiveApi,
    NotificationPreferenceListApi,
    NotificationPreferenceUpsertApi,
    NotificationReadAllApi,
    NotificationReadApi,
    NotificationSendApi,
    NotificationTemplateListApi,
    NotificationTemplateUpdateApi,
    NotificationUnreadCountApi,
)

app_name = "notifications"

urlpatterns = [
    path("notifications/", NotificationInboxListApi.as_view(), name="inbox-list"),
    path("notifications/unread-count/", NotificationUnreadCountApi.as_view(), name="unread-count"),
    path("notifications/read-all/", NotificationReadAllApi.as_view(), name="read-all"),
    path("notifications/<uuid:notification_id>/read/", NotificationReadApi.as_view(), name="read"),
    path("notifications/send/", NotificationSendApi.as_view(), name="send"),
    path("notification-deliveries/", NotificationDeliveryListApi.as_view(), name="delivery-list"),
    path(
        "notification-deliveries/<uuid:notification_id>/",
        NotificationDeliveryGetApi.as_view(),
        name="delivery-get",
    ),
    path(
        "notification-deliveries/<uuid:notification_id>/retry/",
        NotificationDeliveryRetryApi.as_view(),
        name="delivery-retry",
    ),
    path("notification-preferences/", NotificationPreferenceListApi.as_view(), name="preference-list"),
    path(
        "notification-preferences/effective/",
        NotificationPreferenceEffectiveApi.as_view(),
        name="preference-effective",
    ),
    path("notification-preferences/update/", NotificationPreferenceUpsertApi.as_view(), name="preference-upsert"),
    path("notification-templates/", NotificationTemplateListApi.as_view(), name="template-list"),
    path(
        "notification-templates/<uuid:template_id>/update/",
        NotificationTemplateUpdateApi.as_view(),
        name="template-update",
    ),
]
