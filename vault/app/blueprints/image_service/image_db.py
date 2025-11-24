import os
from datetime import datetime
from functools import wraps

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session, relationship, declarative_base
from sqlalchemy import inspect, func, text
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from loguru import logger

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
        'database': os.getenv('DB_DATABASE_IMAGE', 'image_db')
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

# 创建基础模型类
Base = declarative_base()

# 定义系统字典表模型
class ImageType(Base):
    __tablename__ = "image_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_id = Column(Integer, unique=True, nullable=False)    # -- 类型ID
    type_name = Column(String(255), nullable=False)   # -- 类型名称
    description = Column(String(255), nullable=False)   # -- 类型描述
    created_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 建立反向关系（方便从 ImageTypes 查到所有 Image）
    # ORM关系 - 提供对象导航 是SQLAlchemy的ORM关系属性 存在于Python对象中，不在数据库中
    # relationship 对象，指向 ImageTypes 模型实例
    # 用于面向对象编程中的关联访问
    # 可以不需要显式定义，但定义后可以通过 image_type.images 访问关联的图片列表
    # 如果需要通过 image_type.images 访问关联的图片列表，可以打开下面的代码，sqlalchemy会自动处理关联
    # 只定义单向关系注释掉下面的代码，如果是双向关系则保留
    # images = relationship("Image", back_populates="image_type")

    def to_dict(self):
        return {
            'type_id': self.type_id,
            'type_name': self.type_name,
            'description': self.description
        }

    def __repr__(self):
        return f'<SystemDict {self.key}>'

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 数据库字段 - 存储实际的ID值 外键：关联 image_types 表中的 type_id 存储在 images 表中
    type_id = Column(Integer, ForeignKey('image_types.type_id'))
    uuid_filename = Column(String(100), unique=True, nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    md5_hash = Column(String(32), index=True)
    width = Column(Integer)  # 图片宽度
    height = Column(Integer)  # 图片高度
    mime_type = Column(String(50))
    user_id = Column(Integer)
    upload_time = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)  # 插入时设置
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    description = Column(Text)  # 可选：图片描述
    is_deleted = Column(Boolean, default=False)  # 软删除标记
    tags = Column(String(255))  # 可选：标签，逗号分隔

    # 建立与 ImageTypes 的关联关系
    # ORM关系 - 提供对象导航 是SQLAlchemy的ORM关系属性 存在于Python对象中，不在数据库中
    # relationship 对象，指向 ImageTypes 模型实例
    # 用于面向对象编程中的关联访问
    # 可通过 image.image_type 访问关联的图片类型
    # 定义双向关系时使用下面的代码
    # image_type = relationship("ImageTypes", back_populates="images")
    # 只定义单向关系
    # image_type = relationship("ImageType")
    # 方式1: 使用 lazy='joined' 总是预加载
    image_type = relationship('ImageType', lazy='joined')

    def __repr__(self):
        return f'<Image {self.uuid_filename}>'

    def to_dict(self):
        folder_name = "0_others"
        if self.image_type is not None:
            folder_name = f"{self.image_type.type_id}_{self.image_type.type_name}"
        url_str = f"/images/{folder_name}/{self.uuid_filename}"

        return {
            'id': self.id,
            'type_id': self.type_id,
            'tags': self.tags,
            'filename': self.uuid_filename,
            'original_name': self.original_filename,
            'url': url_str,
            'thumbnail_url': f"/images/thumbnails/{self.uuid_filename}",
            'size': self.file_size,
            'md5_hash': self.md5_hash,
            'size_human': self._format_size(self.file_size),
            'mime_type': self.mime_type,
            'dimensions': {
                'width': self.width,
                'height': self.height
            } if self.width and self.height else None,
            'description': self.description
        }

    @staticmethod
    def _format_size(size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @classmethod
    def get_database_status(cls):
        """获取数据库状态信息"""
        try:
            with db_manager.session_scope() as session:
                # 基础统计
                total_count = session.query(func.count(cls.id)).scalar() or 0
                active_count = session.query(func.count(cls.id)).filter_by(is_deleted=False).scalar() or 0
                deleted_count = session.query(func.count(cls.id)).filter_by(is_deleted=True).scalar() or 0

                # 存储统计
                total_size = session.query(func.sum(cls.file_size)).filter_by(is_deleted=False).scalar() or 0
                deleted_size = session.query(func.sum(cls.file_size)).filter_by(is_deleted=True).scalar() or 0

                # 文件类型统计
                mime_stats = session.query(
                    cls.mime_type,
                    func.count(cls.id).label('count')
                ).filter_by(is_deleted=False).group_by(cls.mime_type).all()

                # 最近上传
                latest_upload = session.query(cls).filter_by(is_deleted=False).order_by(cls.upload_time.desc()).first()
                oldest_upload = session.query(cls).filter_by(is_deleted=False).order_by(cls.upload_time.asc()).first()

                return {
                    'total_images': total_count,
                    'active_images': active_count,
                    'deleted_images': deleted_count,
                    'storage': {
                        'total_size': total_size,
                        'total_size_human': cls._format_size(total_size),
                        'deleted_size': deleted_size,
                        'deleted_size_human': cls._format_size(deleted_size)
                    },
                    'mime_types': {mime: count for mime, count in mime_stats},
                    'latest_upload': latest_upload.upload_time.isoformat() if latest_upload else None,
                    'oldest_upload': oldest_upload.upload_time.isoformat() if oldest_upload else None
                }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }

    @classmethod
    def get_table_info(cls):
        """获取表结构信息"""
        try:
            inspector = inspect(db_manager.engine)
            columns = inspector.get_columns(cls.__tablename__)
            indexes = inspector.get_indexes(cls.__tablename__)

            return {
                'table_name': cls.__tablename__,
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': str(col['default']) if col['default'] else None,
                        'primary_key': col.get('primary_key', False)
                    }
                    for col in columns
                ],
                'indexes': [
                    {
                        'name': idx['name'],
                        'columns': idx['column_names'],
                        'unique': idx['unique']
                    }
                    for idx in indexes
                ]
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'error'
            }

if __name__ == "__main__":
    # 创建所有表
    tableinof = Image.get_database_status()
    print(tableinof)