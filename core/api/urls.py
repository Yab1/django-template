from django.urls import include, path
from django.urls.resolvers import URLResolver

urlpatterns: list[URLResolver] = [
    path(
        "accounting/",
        include(("core.accounting.urls", "accounting"), namespace="accounting"),
    ),
    path(
        "authentication/",
        include(("core.authentication.urls", "authentication"), namespace="authentication"),
    ),
    path(
        "billing/",
        include(("core.billing.urls", "billing"), namespace="billing"),
    ),
    path(
        "care/",
        include(("core.care.urls", "care"), namespace="care"),
    ),
    path(
        "clinical/",
        include(("core.clinical.urls", "clinical"), namespace="clinical"),
    ),
    path(
        "clinical-requests/",
        include(("core.clinical_requests.urls", "clinical_requests"), namespace="clinical_requests"),
    ),
    path(
        "clinical-inventory/",
        include(("core.clinical_inventory.urls", "clinical_inventory"), namespace="clinical_inventory"),
    ),
    path(
        "contents/",
        include(("core.contents.urls", "contents"), namespace="contents"),
    ),
    path(
        "diagnostics/",
        include(("core.diagnostics.urls", "diagnostics"), namespace="diagnostics"),
    ),
    path(
        "devices/",
        include(("core.devices.urls", "devices"), namespace="devices"),
    ),
    path(
        "documents/",
        include(("core.documents.urls", "documents"), namespace="documents"),
    ),
    path(
        "entities/",
        include(("core.entities.urls", "entities"), namespace="entities"),
    ),
    path(
        "events/",
        include(("core.events.urls", "events"), namespace="events"),
    ),
    path(
        "inventory/",
        include(("core.inventory.urls", "inventory"), namespace="inventory"),
    ),
    path(
        "inventory-stock/",
        include(("core.inventory_stock.urls", "inventory_stock"), namespace="inventory_stock"),
    ),
    path(
        "procurement/",
        include(("core.procurement.urls", "procurement"), namespace="procurement"),
    ),
    path(
        "",
        include(("core.encounters.urls", "encounters"), namespace="encounters"),
    ),
    path(
        "extensions/",
        include(("core.extensions.urls", "extensions"), namespace="extensions"),
    ),
    path(
        "identities/",
        include(("core.identities.urls", "identities"), namespace="identities"),
    ),
    path(
        "individuals/",
        include(("core.individuals.urls", "individuals"), namespace="individuals"),
    ),
    path(
        "medications/",
        include(("core.medications.urls", "medications"), namespace="medications"),
    ),
    path(
        "notifications/",
        include(("core.notifications.urls", "notifications"), namespace="notifications"),
    ),
    path(
        "",
        include(("core.payments.urls", "payments"), namespace="payments"),
    ),
    path(
        "pricing/",
        include(("core.pricing.urls", "pricing"), namespace="pricing"),
    ),
    path(
        "",
        include(("core.questionnaires.urls", "questionnaires"), namespace="questionnaires"),
    ),
    path(
        "resource-definition/",
        include(("core.resource_definition.urls", "resource_definition"), namespace="resource_definition"),
    ),
    path(
        "scheduling/",
        include(("core.scheduling.urls", "scheduling"), namespace="scheduling"),
    ),
    path(
        "security/",
        include(("core.security.urls", "security"), namespace="security"),
    ),
    path(
        "systems/",
        include(("core.systems.urls", "systems"), namespace="systems"),
    ),
    path(
        "terminology/",
        include(("core.terminology.urls", "terminology"), namespace="terminology"),
    ),
    path(
        "",
        include(("core.users.urls", "users"), namespace="users"),
    ),
    path(
        "workflows/",
        include(("core.workflows.urls", "workflows"), namespace="workflows"),
    ),
    path(
        "capacity/",
        include(("core.capacity.urls", "capacity"), namespace="capacity"),
    ),
    path(
        "order-sets/",
        include(("core.order_sets.urls", "order_sets"), namespace="order_sets"),
    ),
    path(
        "lab/",
        include(("core.lab.urls", "lab"), namespace="lab"),
    ),
    path(
        "operations/",
        include(("core.operations.urls", "operations"), namespace="operations"),
    ),
    path(
        "simulate/",
        include(("core.simulations.urls", "simulations"), namespace="simulations"),
    ),
    path(
        "interop/",
        include(("core.interop.urls", "interop"), namespace="interop"),
    ),
    path(
        "teleradiology/",
        include(("core.teleradiology.urls", "teleradiology"), namespace="teleradiology"),
    ),
    path(
        "perioperative/",
        include(("core.perioperative.urls", "perioperative"), namespace="perioperative"),
    ),
]
