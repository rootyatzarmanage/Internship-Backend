from typing import Any, Dict, Optional  # noqa: UP035


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str | None = None,
        details: Optional[Any] = None,
    ):
        self.messAny = None
        self.messAny | None
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        return f"{self.error_code}: {self.message}"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"status_code={self.status_code}, "
            f"error_code='{self.error_code}')"
        )


# ── 4xx ───────────────────────────────────────────────────────────────────────

class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message, 400, "VALIDATION_ERROR", details)


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request", details: Optional[Any] = None):
        super().__init__(message, 400, "BAD_REQUEST", details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized access", details: Optional[Any] = None):
        super().__init__(message, 401, "UNAUTHORIZED", details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden", details: Optional[Any] = None):
        super().__init__(message, 403, "FORBIDDEN", details)


class PermissionDeniedException(ForbiddenException):
    def __init__(self, message: str = "Permission denied", details: Optional[Any] = None):
        super().__init__(message, details)


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        if resource:
            details["resource"] = resource
        super().__init__(message, 404, "NOT_FOUND", details)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource conflict", details: Optional[Any] = None):
        super().__init__(message, 409, "CONFLICT", details)


class UnprocessableEntityException(AppException):
    def __init__(self, message: str = "Unprocessable entity", details: Optional[Any] = None):
        super().__init__(message, 422, "UNPROCESSABLE_ENTITY", details)


class TooManyRequestsException(AppException):
    def __init__(
        self,
        message: str = "Too many requests",
        retry_after: Optional[int] = None,
        details: Optional[Any] = None,
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, 429, "RATE_LIMIT_EXCEEDED", details)


# ── 5xx ───────────────────────────────────────────────────────────────────────

class InternalServerException(AppException):
    def __init__(self, message: str = "Internal server error", details: Optional[Any] = None):
        super().__init__(message, 500, "INTERNAL_SERVER_ERROR", details)


class DatabaseException(AppException):
    def __init__(self, message: str = "Database error occurred", details: Optional[Any] = None):
        super().__init__(message, 500, "DATABASE_ERROR", details)


class StorageException(AppException):
    def __init__(self, message: str = "Storage error occurred", details: Optional[Any] = None):
        super().__init__(message, 500, "STORAGE_ERROR", details)


class FileUploadException(AppException):
    def __init__(self, message: str = "File upload failed", details: Optional[Any] = None):
        super().__init__(message, 400, "FILE_UPLOAD_ERROR", details)


class ExternalServiceException(AppException):
    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        details = details or {}
        if service_name:
            details["service"] = service_name
        super().__init__(message, 502, "EXTERNAL_SERVICE_ERROR", details)


class ServiceUnavailableException(AppException):
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None,
        details: Optional[Any] = None,
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, 503, "SERVICE_UNAVAILABLE", details)


class GatewayTimeoutException(AppException):
    def __init__(self, message: str = "Gateway timeout", details: Optional[Any] = None):
        super().__init__(message, 504, "GATEWAY_TIMEOUT", details)


# ── Business logic ─────────────────────────────────────────────────────────────

class BusinessLogicException(AppException):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        super().__init__(message, status_code, error_code or "BUSINESS_LOGIC_ERROR", details)


class InsufficientPermissionsException(BusinessLogicException):
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        details = details or {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message, 403, "INSUFFICIENT_PERMISSIONS", details)


class ResourceLockedException(BusinessLogicException):
    def __init__(self, message: str = "Resource is locked", details: Optional[Any] = None):
        super().__init__(message, 409, "RESOURCE_LOCKED", details)


class QuotaExceededException(BusinessLogicException):
    def __init__(
        self,
        message: str = "Quota exceeded",
        quota_type: Optional[str] = None,
        current: Optional[int] = None,
        limit: Optional[int] = None,
        details: Optional[Any] = None,
    ):
        details = details or {}
        if quota_type:
            details["quota_type"] = quota_type
        if current is not None:
            details["current"] = current
        if limit is not None:
            details["limit"] = limit
        super().__init__(message, 429, "QUOTA_EXCEEDED", details)