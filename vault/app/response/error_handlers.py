# utils/error_handlers.py
from flask import jsonify, request
from datetime import datetime, timezone
from .exceptions import APIException
from .error_codes import ErrorCodes, ERROR_MESSAGES
from loguru import logger


def register_global_error_handlers(app):
    """注册全局错误处理器"""

    @app.errorhandler(APIException)
    def handle_api_exception(e):
        """处理自定义API异常"""
        logger.warning(f"API异常: {e.error_code} - {e.message}", extra={
            'error_code': e.error_code,
            'url': request.url,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent'),
            'ip': request.remote_addr
        })

        response = {
            'success': False,
            'message': e.message,
            'error_code': e.error_code,
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': request.headers.get('X-Request-ID')  # 如果有的话
        }

        # 添加详细错误信息（仅在开发环境或特定情况下）
        # if app.debug or e.details:
        #     response['details'] = e.details

        return jsonify(response), e.http_code

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES[ErrorCodes.RESOURCE_NOT_FOUND],
            'error_code': ErrorCodes.RESOURCE_NOT_FOUND,
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器内部错误: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES[ErrorCodes.INTERNAL_ERROR],
            'error_code': ErrorCodes.INTERNAL_ERROR,
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

    @app.errorhandler(400)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES[ErrorCodes.RESOURCE_NOT_FOUND],
            'error_code': ErrorCodes.RESOURCE_NOT_FOUND,
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(f"未处理的异常: {str(error)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': ERROR_MESSAGES[ErrorCodes.INTERNAL_ERROR],
            'error_code': ErrorCodes.INTERNAL_ERROR,
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500