from flask import Blueprint

from ...response import (
    ApiResponse,
    register_global_error_handlers,
    ValidationException,
    ResourceNotFoundException,
    BusinessRuleException,
    ErrorCodes
)

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/health', methods=['GET'])
def api_health():
    return ApiResponse.success(message="You got me, I'm api, and I'm health")