import os


def env_bool(name: str, default: bool = False):
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "on")


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")
    JSON_SORT_KEYS = False
    # 数据库 / 其他外部服务（默认 None 或开发兜底）
    DATABASE_URL = os.getenv("DATABASE_URL")  # 生产必须提供
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ENABLE_FEATURE_X = env_bool("ENABLE_FEATURE_X", default=False)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"
    # 开发专用默认（如使用本地 sqlite）
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    ENV = "testing"
    # 测试数据库可单独用独立库
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    # 强制要求某些变量存在
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is required in production")
    if os.getenv("SECRET_KEY") in (None, "dev-insecure-key"):
        raise RuntimeError("SECRET_KEY must be set securely in production")