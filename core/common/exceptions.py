class ServiceError(Exception):
    """Domain error. The API handler maps ``code`` and ``status_code`` to HTTP."""

    code = "common_error"
    status_code = 400

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(ServiceError):
    code = "not_found"
    status_code = 404


class ConflictError(Exception):
    """Domain conflict. Product APIs and ``@idempotent`` map this to HTTP 409."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class IdempotencyConflictError(Exception):
    """Same Idempotency-Key was reused with a different request. HTTP 409."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
