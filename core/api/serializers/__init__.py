"""DRF serializers used by the API layer (schemas, shared response shapes)."""

from .bulk import (
    build_bulk_ids_input_serializer,
    build_bulk_input_serializer,
    build_bulk_output_serializer,
)
from .content_type import ContentTypeCompactSerializer, ContentTypeNaturalKeyField
from .easy_audit import (
    CrudEventAuditListFilterSerializer,
    CrudEventOutputSerializer,
    LoginEventListQuerySerializer,
    LoginEventOutputSerializer,
    crud_event_to_representation,
    login_event_to_representation,
)
from .envelope import (
    SuccessMetaSerializer,
    build_error_response_serializer,
    build_paginated_result_serializer,
    build_success_response_serializer,
)
from .history_diff import HistoryDiffResponseSerializer, HistoryListItemSerializer
from .revision import RevisionSerializer

__all__ = [
    "ContentTypeCompactSerializer",
    "ContentTypeNaturalKeyField",
    "CrudEventAuditListFilterSerializer",
    "CrudEventOutputSerializer",
    "HistoryDiffResponseSerializer",
    "HistoryListItemSerializer",
    "LoginEventListQuerySerializer",
    "LoginEventOutputSerializer",
    "RevisionSerializer",
    "SuccessMetaSerializer",
    "build_bulk_ids_input_serializer",
    "build_bulk_input_serializer",
    "build_bulk_output_serializer",
    "build_error_response_serializer",
    "build_paginated_result_serializer",
    "build_success_response_serializer",
    "crud_event_to_representation",
    "login_event_to_representation",
]
