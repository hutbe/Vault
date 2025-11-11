import os
from importlib import import_module
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

def load_env():
    """
    分层加载环境变量：
    1. 基础 .env（可选）
    2. 按 APP_ENV 选择 .env.{env_name}
    3. 可选 .env.local 覆盖个人配置
    加载顺序后面的会覆盖前面的同名变量。
    """
    base_dir = Path(__file__).resolve().parent
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


# def register_blueprints(app: Flask):
#     from .blueprints.main import bp as main_bp
#     app.register_blueprint(main_bp)
#
#     from .blueprints.api import bp as api_bp
#     app.register_blueprint(api_bp, url_prefix="/api/v1")


def create_app(config_class=None) -> Flask:
    load_env()

    app = Flask(__name__)

    # 允许两种方式：
    # 1) 直接传 config_class
    # 2) 通过环境变量 CONFIG_CLASS（优先级更低）
    if config_class is None:
        config_path = os.getenv("CONFIG_CLASS", "config.DevelopmentConfig")
        config_obj = _resolve_config(config_path)
    else:
        config_obj = config_class

    app.config.from_object(config_obj)

    # 可选：让 Vault.config 再读取“动态值型”变量（不想写入类里）
    # Vault.config['SOME_RUNTIME_FLAG'] = os.getenv('SOME_RUNTIME_FLAG', 'off')

    @app.get("/health")
    def healthz():
        return {"status": "ok", "env": app.config.get("ENV")}, 200

    return app

if __name__ == '__main__':
    app = create_app(config_class="config.DevelopmentConfig")
    app.run(host='0.0.0.0', port=8080, debug=True)