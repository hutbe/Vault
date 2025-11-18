from flask import Blueprint

from ...response import (
    ApiResponse,
    register_global_error_handlers,
    ValidationException,
    ResourceNotFoundException,
    BusinessRuleException,
    ErrorCodes
)

clock_bp = Blueprint('smart_clock', __name__, url_prefix='/smart-clock')

@clock_bp.route('/health', methods=['GET'])
def api_test():
    return ApiResponse.success(message="You got me, I'm Clock, And I'm health")