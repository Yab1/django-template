import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IdempotencyRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("metadata", models.JSONField(blank=True, default=dict, null=True)),
                ("operation", models.CharField(max_length=64)),
                ("key", models.CharField(max_length=128)),
                ("request_hash", models.CharField(max_length=64)),
                ("response_status", models.PositiveSmallIntegerField()),
                ("response_body", models.JSONField()),
                ("resource_id", models.UUIDField(blank=True, null=True)),
                (
                    "state",
                    models.CharField(
                        choices=[("completed", "Completed")],
                        default="completed",
                        max_length=16,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="idempotency_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Idempotency record",
                "verbose_name_plural": "Idempotency records",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "operation", "key"),
                        name="common_idempotency_user_operation_key",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("state", "completed")),
                        name="common_idempotency_state_completed",
                    ),
                ],
            },
        ),
    ]
