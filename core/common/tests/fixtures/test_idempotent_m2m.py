import pytest
from django.contrib.auth.models import Group, Permission

from core.common.fixtures.idempotent import (
    sync_many_to_many_from_fixture_fields,
)


@pytest.mark.django_db
def test_sync_many_to_many_from_fixture_fields_sets_permissions() -> None:
    permission = Permission.objects.first()
    assert permission is not None

    group = Group.objects.create(name="fixture-m2m-sync-set")
    synced = sync_many_to_many_from_fixture_fields(
        instance=group,
        fields={"permissions": [permission.pk]},
        using="default",
    )

    assert synced == 1
    assert list(group.permissions.values_list("pk", flat=True)) == [permission.pk]


@pytest.mark.django_db
def test_sync_many_to_many_from_fixture_fields_clears_permissions() -> None:
    permission = Permission.objects.first()
    assert permission is not None

    group = Group.objects.create(name="fixture-m2m-sync-clear")
    group.permissions.add(permission)

    synced = sync_many_to_many_from_fixture_fields(
        instance=group,
        fields={"permissions": []},
        using="default",
    )

    assert synced == 1
    assert group.permissions.count() == 0


@pytest.mark.django_db
def test_sync_many_to_many_ignores_non_list_fields() -> None:
    group = Group.objects.create(name="fixture-m2m-sync-skip")
    synced = sync_many_to_many_from_fixture_fields(
        instance=group,
        fields={"name": "ignored"},
        using="default",
    )
    assert synced == 0
