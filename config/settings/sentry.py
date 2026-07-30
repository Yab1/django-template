from config.env import env

SENTRY_DSN = env("SENTRY_DSN", default="")

if SENTRY_DSN:
    environment = env("SENTRY_ENVIRONMENT", default="local")
    release = env("SENTRY_RELEASE", default=None)
    send_pii = env.bool("SENTRY_SEND_DEFAULT_PII", default=False)  # type: ignore
    debug = env.bool("SENTRY_DEBUG", default=False)  # type: ignore
    track_performance = environment == "production"

    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    def traces_sampler(sampling_context):
        """
        Sample web transactions for performance monitoring, ignore Celery tasks.

        Returns:
            - 0: Don't sample (disabled or Celery tasks)
            - 0.5: Sample 50% of web transactions (when performance tracking is enabled)
        """
        if not track_performance:
            return 0

        transaction_context = sampling_context.get("transaction_context")
        if transaction_context is None:
            return 0

        op = transaction_context.get("op")
        if op is None:
            return 0

        if op == "celery.task":
            return 0

        return 0.5

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=environment,
        release=release,
        traces_sampler=traces_sampler,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        # GlitchTip-specific: Session tracking is not supported
        auto_session_tracking=False,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=send_pii,
        # Set to True to view more information about the SDK when troubleshooting
        debug=debug,
    )
