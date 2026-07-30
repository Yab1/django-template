from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from kombu import Exchange, Queue

from config.env import env

# https://docs.celeryproject.org/en/stable/userguide/configuration.html

# RabbitMQ broker URL with vhost isolation (format: amqp://user:pass@host:port/vhost)
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="amqp://guest:guest@localhost:5672/ehr_backend")  # type: ignore
CELERY_RESULT_BACKEND = "django-db"

CELERY_TIMEZONE = "UTC"

CELERY_TASK_SOFT_TIME_LIMIT = 20  # seconds
CELERY_TASK_TIME_LIMIT = 30  # seconds
CELERY_TASK_MAX_RETRIES = 3

# Queue configuration to isolate this project from others and prevent cross-domain blocking
CELERY_TASK_DEFAULT_QUEUE = "ehr_backend"
CELERY_TASK_DEFAULT_EXCHANGE = "ehr_backend"
CELERY_TASK_DEFAULT_ROUTING_KEY = "ehr_backend"

# Define dedicated queues with routing keys; give OTP queue priorities
CELERY_TASK_QUEUES = (
    Queue(
        "ehr_backend",
        Exchange("ehr_backend", type="direct"),
        routing_key="ehr_backend",
    ),
)

# Route tasks to their dedicated queues
CELERY_TASK_ROUTES = {}

# Fair task distribution; avoid one worker prefetching too many tasks
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

# Celery Beat Scheduler - Use database scheduler to support both DB and code schedules
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"


CELERY_BEAT_SCHEDULE = {
    "events-process-outbox": {
        "task": "events.process_outbox",
        # Drain unprocessed DomainEvent rows every 10 seconds. Tune for prod
        # by either increasing the interval or running it as a long-poll worker.
        "schedule": 10.0,
        "options": {"queue": "ehr_backend"},
    },
    "scheduling-check-task-sla": {
        "task": "scheduling.check_task_sla",
        "schedule": 120.0,
        "options": {"queue": "ehr_backend"},
    },
    "notifications-escalation-beat": {
        "task": "notifications.escalation_beat",
        # Run every 60 s — granularity determines how late an escalation can fire.
        # Tune to 30 s for high-acuity environments.
        "schedule": 60.0,
        "options": {"queue": "ehr_backend"},
    },
    "notifications-sweep-retrying": {
        "task": "notifications.sweep_retrying_notifications",
        # Run every 60 s — picks up Celery tasks lost between countdown scheduling
        # and execution (worker restart / broker reconnect window).
        "schedule": 60.0,
        "options": {"queue": "ehr_backend"},
    },
    "notifications-digest-flush-beat": {
        "task": "notifications.digest_flush_beat",
        # Run every 120 s — flushes digest buckets whose scheduled_flush_at has elapsed.
        # Most routing rules configure digest windows of 5–60 min; 120 s beat gives ~2 min max latency.
        "schedule": 120.0,
        "options": {"queue": "ehr_backend"},
    },
    "capacity-transit-sweep-beat": {
        "task": "capacity.transit_sweep_beat",
        "schedule": 60.0,
        "options": {"queue": "ehr_backend"},
    },
    "capacity-turnover-sweep-beat": {
        "task": "capacity.turnover_sweep_beat",
        "schedule": 120.0,
        "options": {"queue": "ehr_backend"},
    },
    "billing-accommodation-census-beat": {
        "task": "billing.accommodation_census_beat",
        "schedule": 3600.0,
        "options": {"queue": "ehr_backend"},
    },
    "workflows-sweep-pending-temporal-starts": {
        "task": "workflows.sweep_pending_temporal_starts",
        # Run every 60 s — recovers workflow instances whose start_temporal_workflow
        # task was lost (worker restart / broker reconnect / stale duplicate worker).
        # Idempotent: re-enqueued starts no-op once run_id is bound.
        "schedule": 60.0,
        "options": {"queue": "ehr_backend"},
    },
    "workflows-sweep-stale-triage-vitals-gates": {
        "task": "workflows.sweep_stale_triage_vitals_gates",
        # Run every 120 s — escalate WAITING record_triage_vitals gates past 30m SLA.
        "schedule": 120.0,
        "options": {"queue": "ehr_backend"},
    },
    "diagnostics-expire-stale-study-claims": {
        "task": "diagnostics.expire_stale_study_claims",
        # Run every 60 s — frees abandoned radiologist reading claims (RIS-03) back
        # to the worklist once their idle window elapses. Idempotent.
        "schedule": 60.0,
        "options": {"queue": "ehr_backend"},
    },
    "diagnostics-sweep-preliminary-report-expiry": {
        "task": "diagnostics.sweep_preliminary_report_expiry",
        # Run every 300 s — escalates preliminary reports left unsigned past the
        # configured window (RIS-05). Emits events only; does not mutate status.
        "schedule": 300.0,
        "options": {"queue": "ehr_backend"},
    },
    "diagnostics-sweep-image-storage-tier": {
        "task": "diagnostics.sweep_image_storage_tier",
        # Run hourly — moves aged imaging studies to the next storage tier per
        # ImageLifecycleConfig (RIS-07). Skips studies under legal hold. Idempotent.
        "schedule": 3600.0,
        "options": {"queue": "ehr_backend"},
    },
    "teleradiology-sweep-sla-breaches": {
        "task": "teleradiology.sweep_sla_breaches",
        # Run every 300 s — emits imaging.teleradiology.sla_breach for studies past
        # their contracted reading SLA (RIS-09). Notifications via RoutingRule. Idempotent.
        "schedule": 300.0,
        "options": {"queue": "ehr_backend"},
    },
    "diagnostics-sweep-tat-sla": {
        "task": "diagnostics.sweep_tat_sla",
        # Run every 300 s — evaluates order-to-read TAT SLA for all active imaging
        # studies, records ImagingTATBreach rows, and emits imaging.tat.breach events.
        # Idempotent: skips studies that already have a matching breach row.
        "schedule": 300.0,
        "options": {"queue": "ehr_backend"},
    },
    "diagnostics-select-peer-review-cases": {
        "task": "diagnostics.select_peer_review_cases",
        # Run daily — nominates a random 5% sample of recently issued diagnostic
        # reports that have not yet received a peer review. Emits
        # imaging.peer_review.case_nominated per report; RoutingRule fans out to reviewers.
        "schedule": 86400.0,
        "options": {"queue": "ehr_backend"},
    },
    "scheduling-sweep-appointment-reminders": {
        "task": "scheduling.sweep_appointment_reminders",
        # Hourly sweep — queries active AppointmentReminderPolicy rows and emits
        # scheduling.appointment.reminder_requested for each appointment that falls
        # within a configured reminder window (e.g. 168h/24h/2h before start).
        "schedule": 3600.0,
        "options": {"queue": "ehr_backend"},
    },
    "security-sweep-break-glass-grants": {
        "task": "security.sweep_break_glass_grants",
        # Every 5 minutes — expires BreakGlassGrants whose effective_until has passed.
        "schedule": 300.0,
        "options": {"queue": "ehr_backend"},
    },
    "diagnostics-deliver-scheduled-reports": {
        "task": "diagnostics.deliver_scheduled_reports",
        # Every 10 minutes — evaluates ScheduledReportDeliveryConfig rows whose
        # schedule_cron is due, generates the analytics report, and dispatches it
        # via email/SFTP/webhook/object-storage (RIS-11-010). Idempotent.
        "schedule": 600.0,
        "options": {"queue": "ehr_backend"},
    },
    "diagnostics-staff-credential-expiry-sweep": {
        "task": "diagnostics.staff_credential_expiry_sweep",
        # Daily — marks expired credentials; emits 30d/7d expiry alerts (RIS-13-013).
        # Idempotent: last_alerted_at gate prevents double-alerting within 24h.
        "schedule": 86400.0,
        "options": {"queue": "ehr_backend"},
    },
    "clinical-requests-standing-order-due-sweep": {
        "task": "clinical_requests.standing_order_due_sweep",
        # Hourly — generates new ServiceRequest rows from active RecurringOrderSchedule
        # templates whose next_due_at has passed (RIS-01-003). Uses select_for_update
        # (skip_locked) so concurrent workers cannot double-generate.
        "schedule": 3600.0,
        "options": {"queue": "ehr_backend"},
    },
    "medications-scan-due-medication-administrations": {
        "task": "medications.scan_due_medication_administrations",
        # Every 5 minutes — starts WF-11 for each active inpatient MedicationRequest whose
        # next dose is due, anchored to a fresh Task per cycle. Idempotent: skips a request
        # that already has an open medication-administration Task.
        "schedule": 300.0,
        "options": {"queue": "ehr_backend"},
    },
}

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.base")

app = Celery("ehr_backend")

# Use UTC consistently across all workers to avoid clock drift
app.conf.timezone = "UTC"
app.conf.enable_utc = True

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.broker_connection_retry_on_startup = True

app.autodiscover_tasks()
