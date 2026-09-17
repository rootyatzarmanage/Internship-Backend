from typing import Any

class AppException(Exception):
    def __init__(
            self,
            message : str,
            status_code : int = 500,
            error_code : str |None = None,
            details : Any = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(message)

class UnauthorizedException(AppException):
    def __init__(
            self, 
            message: str = "Unauthorized access"
        ):
        super().__init__(message, 401, "UNAUTHORIZED")

class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, 403, "FORBIDDEN")


class ConflictException(AppException):
    def __init__(
            self,
            message : str = "Resource_conflict"
    ):
        super().__init__(message,409,"CONFLICT")