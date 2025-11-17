from flask import jsonify
from datetime import datetime, timezone

class ApiResponse:
    @staticmethod
    def success(data=None, message="操作成功", code=200):
        return jsonify({
            'success': True,
            'message': message,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'code': code
        }), code

    @staticmethod
    def error(message="操作失败", code=400, error_code=None):
        return jsonify({
            'success': False,
            'message': message,
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'code': code,
            'error_code': error_code
        }), code

    @staticmethod
    def not_found(error):
        return jsonify({
            'success': False,
            'message': "请求的资源不存在",
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'code': 404
        }), 404

    @staticmethod
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': "服务器内部错误",
            'data': None,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'code': 500
        }), 500

    @staticmethod
    def validation_error(error):
        return jsonify({
            'success': False,
            'message': "数据验证失败",
            'data': None,
            'errors': error.messages,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'code': 400
        }), 400