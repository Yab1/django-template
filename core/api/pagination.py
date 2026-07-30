"""
Pagination utilities for list APIs.

Use get_paginated_response with a LimitOffsetPagination
subclass so the API handles pagination while the selector returns the queryset.
"""

from collections import OrderedDict

from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination as _LimitOffsetPagination
from rest_framework.response import Response


def get_paginated_response(*, pagination_class, serializer_class, queryset, request, view):
    """
    Paginate a queryset and return a Response with limit/offset/count/next/previous/results.

    If the request has no limit/offset (or pagination is disabled), returns the full
    queryset serialized without pagination metadata.
    """
    paginator = pagination_class()

    page = paginator.paginate_queryset(queryset, request, view=view)

    if page is not None:
        serializer = serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = serializer_class(queryset, many=True)

    return Response(data=serializer.data, status=status.HTTP_200_OK)


class LimitOffsetPagination(_LimitOffsetPagination):
    """
    Limit/offset pagination that returns limit and offset in the response
    so the frontend can build next/previous links.
    """

    default_limit = 10
    max_limit = 50

    def get_paginated_data(self, data):
        return OrderedDict([
            ("limit", self.limit),
            ("offset", self.offset),
            ("count", self.count),
            ("next", self.get_next_link()),
            ("previous", self.get_previous_link()),
            ("results", data),
        ])

    def get_paginated_response(self, data):
        return Response(
            OrderedDict([
                ("limit", self.limit),
                ("offset", self.offset),
                ("count", self.count),
                ("next", self.get_next_link()),
                ("previous", self.get_previous_link()),
                ("results", data),
            ])
        )
