import os
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from loguru import logger
from .vault_models import *

class DatabaseManager:
    def __init__(self, connection_url):
        self.engine = create_engine(
            connection_url,
            # 连接池配置
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,

            # 性能配置
            echo_pool=True,  # 生产环境设为 False
            echo=True,  # 生产环境设为 False

            # 连接参数
            connect_args={
                'connect_timeout': 10,
                'read_timeout': 60,
                'write_timeout': 60,
                'charset': 'utf8mb4'
            }
        )

        # 线程安全的会话
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        self.ScopedSession = scoped_session(self.session_factory)


    @contextmanager
    def session_scope(self):
        """提供事务范围的会话上下文"""
        session = self.ScopedSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            self.ScopedSession.remove()

    def get_connection_stats(self):
        """获取连接池详细状态"""
        pool = self.engine.pool

        status = {
            "pool_class": type(pool).__name__,
            "pool_size": pool.size(),  # 连接池配置大小
            "checked_out": pool.checkedout(),  # 已签出的连接数
            "available": pool.size() - pool.checkedout(),  # 可用连接数
            "overflow": pool.overflow(),  # 当前溢出连接数
            "max_overflow": pool._max_overflow,  # 最大溢出数
            "total_connections": pool.size() + pool.overflow(),  # 总连接数
        }

        return status

# 创建数据库引擎
def create_engine_from_env():
    # 从环境变量读取配置
    db_config = {
        'username': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '3306'),
        'database': os.getenv('DB_DATABASE', 'vault_db')
    }
    # 构建连接字符串
    connection_string = (
        f"mysql+pymysql://{db_config['username']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )

    logger.info(f"connection_string: ${connection_string}")

    return DatabaseManager(connection_string)

db_manager = create_engine_from_env()

def get_db():
    """依赖项：为每个请求提供数据库会话"""
    with db_manager.session_scope() as session:
        yield session

def with_session(function):
    """自动管理数据库会话的装饰器"""
    @wraps(function)
    def wrapper(*args, **kwargs):
        with db_manager.session_scope() as session:
            # 将会话作为第一个参数注入
            return function(session, *args, **kwargs)
    return wrapper