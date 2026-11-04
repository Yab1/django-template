from django.core.cache import cache

LIST_CACHE_TIMEOUT = 60


def bust_cache(*namespaces: str) -> None:
    """Drop cached reads for these namespaces after the current transaction commits."""
    from django.db import transaction

    def _run() -> None:
        for namespace in namespaces:
            invalidate_list_cache(namespace)

    transaction.on_commit(_run)


def invalidate_list_cache(namespace: str) -> None:
    """Drop cached read responses whose key contains ``namespace``.

    django-redis implements ``delete_pattern``. The test cache does not, and
    then this is a no-op.
    """
    delete_pattern = getattr(cache, "delete_pattern", None)
    if delete_pattern is None:
        return
    delete_pattern(f"*{namespace}*")
