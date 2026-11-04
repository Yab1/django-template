from celery import shared_task


@shared_task
def recipe_published_task(recipe_id: str) -> None:
    """
    After-commit follow-up for recipe_publish.

    Import the service inside the task (avoids import cycles). Insurance
    events copy this: policy_issued_task, claim_approved_task, …
    Clocks (expire quotes) go in CELERY_BEAT_SCHEDULE, not here.
    """
    from uuid import UUID

    from core.cookbook.services.recipe import recipe_after_publish

    recipe_after_publish(recipe_id=UUID(recipe_id))
