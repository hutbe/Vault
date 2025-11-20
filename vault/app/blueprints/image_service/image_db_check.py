from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy import inspect, func, text

import os

from image_db import db_manager


def get_database_info(a_session):
    # 获取 engine
    engine = a_session.get_bind()

    print("=== 数据库连接信息 ===")
    print(f"数据库URL: {engine.url}")
    print(f"数据库驱动: {engine.driver}")
    print(f"数据库名称: {engine.url.database}")
    print(f"主机地址: {engine.url.host}")
    print(f"端口: {engine.url.port}")
    print(f"用户名: {engine.url.username}")


def get_all_tables(session):
    """获取数据库中所有表名称"""
    inspector = inspect(session.get_bind())
    tables = inspector.get_table_names()

    print("=== 数据库表列表 ===")
    for i, table_name in enumerate(tables, 1):
        print(f"{i}. {table_name}")

    return tables


def get_sqlite_database_info(a_session):
    """获取 SQLite 数据库的详细信息"""
    engine = a_session.get_bind()
    inspector = inspect(engine)

    print("=== SQLite 数据库详细信息 ===")
    print(f"数据库文件: {engine.url.database}")
    print(f"文件路径: {os.path.abspath(engine.url.database)}")
    print(f"文件大小: {get_file_size(engine.url.database)}")
    print(f"SQLite 版本: {get_sqlite_version(a_session)}")

    # 获取所有表
    tables = inspector.get_table_names()
    print(f"\n数据库中的表 ({len(tables)} 个):")
    for i, table in enumerate(tables, 1):
        print(f"  {i}. {table}")

    return tables


def get_sqlite_version(a_session):
    """获取 SQLite 版本"""
    try:
        result = a_session.execute(text("SELECT sqlite_version()"))
        return result.scalar()
    except:
        return "未知"


def get_file_size(db_path):
    """获取数据库文件大小"""
    try:
        size_bytes = os.path.getsize(db_path)
        size_mb = size_bytes / (1024 * 1024)
        return f"{size_mb:.2f} MB ({size_bytes} 字节)"
    except:
        return "未知"


print('--- Image Info ---')

# image = session.query(Image).filter_by(
#     uuid_filename='acead0c0e3fc4d75b5fed8d79d61a461.jpg',
#     is_deleted=False
# ).first()

# image = session.query(Image).filter(id=='5').one()
with db_manager.session_scope() as session:
    print('--- Database Status ---')
    get_database_info(session)

    print('--- Table Info ---')
    get_all_tables(session)

    print('---SQLite Database Status ---')
    get_sqlite_database_info(session)

    # print(image.to_dict() if image else "Image not found")
