# utils/error_codes.py
class ErrorCodes:
    """错误代码定义"""

    # 通用错误 (1000-1999)
    INTERNAL_ERROR = "E1000"
    INVALID_REQUEST = "E1001"
    INVALID_PARAMETER = "E1002"
    MISSING_PARAMETER = "E1003"
    RATE_LIMIT_EXCEEDED = "E1004"

    # 认证相关错误 (2000-2999)
    AUTH_REQUIRED = "E2000"
    AUTH_INVALID_TOKEN = "E2001"
    AUTH_TOKEN_EXPIRED = "E2002"
    AUTH_INVALID_CREDENTIALS = "E2003"
    AUTH_ACCOUNT_LOCKED = "E2004"
    AUTH_ACCOUNT_DISABLED = "E2005"

    # 授权相关错误 (3000-3999)
    PERMISSION_DENIED = "E3000"
    INSUFFICIENT_PRIVILEGES = "E3001"
    RESOURCE_ACCESS_DENIED = "E3002"
    OPERATION_NOT_ALLOWED = "E3003"

    # 资源相关错误 (4000-4999)
    RESOURCE_NOT_FOUND = "E4000"
    RESOURCE_ALREADY_EXISTS = "E4001"
    RESOURCE_CONFLICT = "E4002"
    RESOURCE_GONE = "E4003"

    # 数据验证错误 (5000-5999)
    VALIDATION_FAILED = "E5000"
    INVALID_EMAIL_FORMAT = "E5001"
    INVALID_PHONE_FORMAT = "E5002"
    PASSWORD_TOO_WEAK = "E5003"
    INVALID_DATE_FORMAT = "E5004"
    FIELD_REQUIRED = "E5005"
    FIELD_TOO_LONG = "E5006"
    FIELD_TOO_SHORT = "E5007"

    # 业务逻辑错误 (6000-6999)
    BUSINESS_RULE_VIOLATION = "E6000"
    INSUFFICIENT_BALANCE = "E6001"
    ORDER_CANNOT_BE_CANCELLED = "E6002"
    PRODUCT_OUT_OF_STOCK = "E6003"

    # 外部服务错误 (7000-7999)
    EXTERNAL_SERVICE_ERROR = "E7000"
    PAYMENT_SERVICE_ERROR = "E7001"
    EMAIL_SERVICE_ERROR = "E7002"
    SMS_SERVICE_ERROR = "E7003"

    # 数据库相关错误 (8000-8999)
    DATABASE_ERROR = "E8000"
    DATABASE_CONNECTION_ERROR = "E8001"
    DATABASE_CONSTRAINT_ERROR = "E8002"
    DATABASE_TIMEOUT = "E8003"


# 错误码与消息的映射
ERROR_MESSAGES = {
    ErrorCodes.INTERNAL_ERROR: "服务器内部错误",
    ErrorCodes.INVALID_REQUEST: "请求格式错误",
    ErrorCodes.INVALID_PARAMETER: "参数格式错误",
    ErrorCodes.MISSING_PARAMETER: "缺少必需参数",
    ErrorCodes.RATE_LIMIT_EXCEEDED: "请求频率超限",

    ErrorCodes.AUTH_REQUIRED: "需要身份认证",
    ErrorCodes.AUTH_INVALID_TOKEN: "无效的访问令牌",
    ErrorCodes.AUTH_TOKEN_EXPIRED: "访问令牌已过期",
    ErrorCodes.AUTH_INVALID_CREDENTIALS: "用户名或密码错误",
    ErrorCodes.AUTH_ACCOUNT_LOCKED: "账户已被锁定",
    ErrorCodes.AUTH_ACCOUNT_DISABLED: "账户已被禁用",

    ErrorCodes.PERMISSION_DENIED: "权限不足",
    ErrorCodes.INSUFFICIENT_PRIVILEGES: "权限级别不够",
    ErrorCodes.RESOURCE_ACCESS_DENIED: "无权访问该资源",
    ErrorCodes.OPERATION_NOT_ALLOWED: "不允许执行该操作",

    ErrorCodes.RESOURCE_NOT_FOUND: "请求的资源不存在",
    ErrorCodes.RESOURCE_ALREADY_EXISTS: "资源已存在",
    ErrorCodes.RESOURCE_CONFLICT: "资源冲突",
    ErrorCodes.RESOURCE_GONE: "资源已被删除",

    ErrorCodes.VALIDATION_FAILED: "数据验证失败",
    ErrorCodes.INVALID_EMAIL_FORMAT: "邮箱格式错误",
    ErrorCodes.INVALID_PHONE_FORMAT: "手机号格式错误",
    ErrorCodes.PASSWORD_TOO_WEAK: "密码强度不够",
    ErrorCodes.INVALID_DATE_FORMAT: "日期格式错误",
    ErrorCodes.FIELD_REQUIRED: "字段不能为空",
    ErrorCodes.FIELD_TOO_LONG: "字段长度超限",
    ErrorCodes.FIELD_TOO_SHORT: "字段长度不足",

    ErrorCodes.BUSINESS_RULE_VIOLATION: "违反业务规则",
    ErrorCodes.INSUFFICIENT_BALANCE: "余额不足",
    ErrorCodes.ORDER_CANNOT_BE_CANCELLED: "订单无法取消",
    ErrorCodes.PRODUCT_OUT_OF_STOCK: "商品库存不足",

    ErrorCodes.EXTERNAL_SERVICE_ERROR: "外部服务错误",
    ErrorCodes.PAYMENT_SERVICE_ERROR: "支付服务错误",
    ErrorCodes.EMAIL_SERVICE_ERROR: "邮件服务错误",
    ErrorCodes.SMS_SERVICE_ERROR: "短信服务错误",

    ErrorCodes.DATABASE_ERROR: "数据库操作错误",
    ErrorCodes.DATABASE_CONNECTION_ERROR: "数据库连接错误",
    ErrorCodes.DATABASE_CONSTRAINT_ERROR: "数据库约束违反",
    ErrorCodes.DATABASE_TIMEOUT: "数据库操作超时",
}

# 错误码与消息的映射
ERROR_MESSAGES_zh = {
    ErrorCodes.INTERNAL_ERROR: "服务器内部错误",
    ErrorCodes.INVALID_REQUEST: "请求格式错误",
    ErrorCodes.INVALID_PARAMETER: "参数格式错误",
    ErrorCodes.MISSING_PARAMETER: "缺少必需参数",
    ErrorCodes.RATE_LIMIT_EXCEEDED: "请求频率超限",

    ErrorCodes.AUTH_REQUIRED: "需要身份认证",
    ErrorCodes.AUTH_INVALID_TOKEN: "无效的访问令牌",
    ErrorCodes.AUTH_TOKEN_EXPIRED: "访问令牌已过期",
    ErrorCodes.AUTH_INVALID_CREDENTIALS: "用户名或密码错误",
    ErrorCodes.AUTH_ACCOUNT_LOCKED: "账户已被锁定",
    ErrorCodes.AUTH_ACCOUNT_DISABLED: "账户已被禁用",

    ErrorCodes.PERMISSION_DENIED: "权限不足",
    ErrorCodes.INSUFFICIENT_PRIVILEGES: "权限级别不够",
    ErrorCodes.RESOURCE_ACCESS_DENIED: "无权访问该资源",
    ErrorCodes.OPERATION_NOT_ALLOWED: "不允许执行该操作",

    ErrorCodes.RESOURCE_NOT_FOUND: "请求的资源不存在",
    ErrorCodes.RESOURCE_ALREADY_EXISTS: "资源已存在",
    ErrorCodes.RESOURCE_CONFLICT: "资源冲突",
    ErrorCodes.RESOURCE_GONE: "资源已被删除",

    ErrorCodes.VALIDATION_FAILED: "数据验证失败",
    ErrorCodes.INVALID_EMAIL_FORMAT: "邮箱格式错误",
    ErrorCodes.INVALID_PHONE_FORMAT: "手机号格式错误",
    ErrorCodes.PASSWORD_TOO_WEAK: "密码强度不够",
    ErrorCodes.INVALID_DATE_FORMAT: "日期格式错误",
    ErrorCodes.FIELD_REQUIRED: "字段不能为空",
    ErrorCodes.FIELD_TOO_LONG: "字段长度超限",
    ErrorCodes.FIELD_TOO_SHORT: "字段长度不足",

    ErrorCodes.BUSINESS_RULE_VIOLATION: "违反业务规则",
    ErrorCodes.INSUFFICIENT_BALANCE: "余额不足",
    ErrorCodes.ORDER_CANNOT_BE_CANCELLED: "订单无法取消",
    ErrorCodes.PRODUCT_OUT_OF_STOCK: "商品库存不足",

    ErrorCodes.EXTERNAL_SERVICE_ERROR: "外部服务错误",
    ErrorCodes.PAYMENT_SERVICE_ERROR: "支付服务错误",
    ErrorCodes.EMAIL_SERVICE_ERROR: "邮件服务错误",
    ErrorCodes.SMS_SERVICE_ERROR: "短信服务错误",

    ErrorCodes.DATABASE_ERROR: "数据库操作错误",
    ErrorCodes.DATABASE_CONNECTION_ERROR: "数据库连接错误",
    ErrorCodes.DATABASE_CONSTRAINT_ERROR: "数据库约束违反",
    ErrorCodes.DATABASE_TIMEOUT: "数据库操作超时",
}