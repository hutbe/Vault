import os
from importlib import import_module
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv
from loguru import logger

from .blueprints import register_blueprints
from .response import register_global_error_handlers

def load_env():
    """
    分层加载环境变量：
    1. 基础 .env（可选）
    2. 按 APP_ENV 选择 .env.{env_name}
    3. 可选 .env.local 覆盖个人配置
    加载顺序后面的会覆盖前面的同名变量。
    """
    base_dir = Path(__file__).resolve().parent.parent
    # 1) 通用
    load_dotenv(base_dir / ".env", override=False)
    # 2) 环境专用
    app_env = os.getenv("APP_ENV", "development").lower()
    load_dotenv(base_dir / f".env.{app_env}", override=True)
    # 3) 个人本地覆盖（不要提交到版本库）
    # load_dotenv(base_dir / ".env.local", override=True)

def _resolve_config(config_path: str):
    module_path, class_name = config_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)


# def register_blueprints(flask_app: Flask):
#     from .blueprints.image_service.api import image_bp
#     flask_app.register_blueprint(image_bp)
#
#     from .blueprints.api import api_bp
#     flask_app.register_blueprint(api_bp, url_prefix="/api/v1")

def create_app(config_class=None) -> Flask:
    load_env()

    flask_app = Flask(__name__)

    # 允许两种方式：
    # 1) 直接传 config_class
    # 2) 通过环境变量 CONFIG_CLASS（优先级更低）
    if config_class is None:
        config_path = os.getenv("CONFIG_CLASS", "config.DevelopmentConfig")
        config_obj = _resolve_config(config_path)
    else:
        config_obj = config_class

    flask_app.config.from_object(config_obj)

    # 可选：让 vault.config 再读取“动态值型”变量（不想写入类里）
    # vault.config['SOME_RUNTIME_FLAG'] = os.getenv('SOME_RUNTIME_FLAG', 'off')

    # 全局错误处理，对所有blueprint都生效
    register_global_error_handlers(flask_app)

    register_blueprints(flask_app)

    @flask_app.get("/health")
    def healthz():
        return {"status": "ok", "env": flask_app.config.get("ENV")}, 200

    return flask_app

if __name__ == '__main__':
    app = create_app(config_class="config.DevelopmentConfig")
    app.run(host='0.0.0.0', port=9090, debug=True)