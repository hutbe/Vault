# utils/exceptions.py
from .error_codes import ErrorCodes, ERROR_MESSAGES


class APIException(Exception):
    """自定义API异常基类"""

    def __init__(self, error_code=None, message=None, details=None, http_code=400):
        self.error_code = error_code or ErrorCodes.INTERNAL_ERROR
        self.message = message or ERROR_MESSAGES.get(self.error_code, "未知错误")
        self.details = details or {}
        self.http_code = http_code
        super().__init__(self.message)


class ValidationException(APIException):
    """数据验证异常"""

    def __init__(self, message=None, field_errors=None, error_code=None):
        super().__init__(
            error_code=error_code or ErrorCodes.VALIDATION_FAILED,
            message=message,
            details={'field_errors': field_errors or []},
            http_code=400
        )


class AuthenticationException(APIException):
    """认证异常"""

    def __init__(self, error_code=ErrorCodes.AUTH_REQUIRED, message=None):
        super().__init__(
            error_code=error_code,
            message=message,
            http_code=401
        )


class AuthorizationException(APIException):
    """授权异常"""

    def __init__(self, error_code=ErrorCodes.PERMISSION_DENIED, message=None):
        super().__init__(
            error_code=error_code,
            message=message,
            http_code=403
        )


class ResourceNotFoundException(APIException):
    """资源不存在异常"""

    def __init__(self, resource_type="资源", resource_id=None):
        message = f"{resource_type}不存在"
        if resource_id:
            message += f" (ID: {resource_id})"

        super().__init__(
            error_code=ErrorCodes.RESOURCE_NOT_FOUND,
            message=message,
            details={'resource_type': resource_type, 'resource_id': resource_id},
            http_code=404
        )


class BusinessRuleException(APIException):
    """业务规则异常"""

    def __init__(self, error_code=ErrorCodes.BUSINESS_RULE_VIOLATION, message=None, details=None):
        super().__init__(
            error_code=error_code,
            message=message,
            details=details,
            http_code=422
        )