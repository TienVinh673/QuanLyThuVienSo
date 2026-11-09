class AppError(Exception):
    """Lỗi nghiệp vụ có thể hiển thị trực tiếp cho người dùng."""

    status_code = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status_code = 400


class AuthError(AppError):
    status_code = 401


class PermissionDenied(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class BusinessRuleError(AppError):
    status_code = 409


class UnsupportedDocumentError(ValidationError):
    pass
