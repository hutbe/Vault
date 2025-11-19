from loguru import logger
import os

def env_bool(name: str, default: bool = False):
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


class BaseConfig:
    # logger.info("所有环境变量名:")
    # for key, value in os.environ.items():
    #     logger.info(f"{key}={value}")

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
    JSON_SORT_KEYS = False
    # 数据库 / 其他外部服务（默认 None 或开发兜底）
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ENABLE_FEATURE_X = env_bool("ENABLE_FEATURE_X", default=False)

    # 数据库配置
    DB_USER = os.getenv("DB_USER", "root")  # 生产必须提供
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", 3306)
    DB_DATABASE = os.getenv("DB_DATABASE", "vault_db")

    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              (
                                f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
                                f"@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
                            )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 目录相关
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.getenv("SHARED_DATA_PATH", "./shared_data/uploads")

    # 上传配置
    IMAGE_UPLOAD_FOLDER = os.path.join(BASE_DIR, f'{UPLOAD_FOLDER}/image')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 限制上传文件大小为 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

    # 权限配置
    IMAGE_SERVICE_AUTH_CODE = "HappyImage2024!"
    # 图片服务配置
    IMAGE_URL_PREFIX = '/image'
    THUMBNAIL_SIZE = (300, 300)

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"
    # 开发专用默认（如使用本地 sqlite）
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    ENV = "testing"
    # 测试数据库可单独用独立库 v
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    # 强制要求某些变量存在
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required in production")
    if os.getenv("SECRET_KEY") in (None, "dev-insecure-key"):
        raise RuntimeError("SECRET_KEY must be set securely in production")