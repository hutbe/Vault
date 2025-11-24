import os
import sqlite3

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

from sqlalchemy import create_engine, inspect, text

# 环境配置
# 方案1：让 python-dotenv 自动向上寻找 .env（当前工作目录为执行命令所在目录）
# load_dotenv()  # 如果你从项目根目录执行：python scripts/task_a.py

# 方案2：指定路径，避免因为“在其他目录执行”找不到
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

def print_current_env():
    print("DB_HOST =", os.getenv("DB_HOST"))
    print("DB_PORT =", os.getenv("DB_PORT"))
    print("DB_ROOT_PASSWORD =", os.getenv("DB_ROOT_PASSWORD"))

    print("DB_DATABASE =", os.getenv("DB_DATABASE_IMAGE"))
    print("DB_USER =", os.getenv("DB_USER"))
    print("DB_PASSWORD =", os.getenv("DB_PASSWORD"))

# 把包所在的父目录临时加入 sys.path，然后按包名正常 import。
import sys
sys.path.insert(0, "/Users/hut/Desktop/Vault/vault")   # 加入父目录（不是包目录本身）

from app.blueprints.image_service.image_db_initializer import init_db, add_image_types
from app.blueprints.image_service.image_db import db_manager

# 使用完后可以移除以避免污染全局
sys.path.pop(0)

SQLITE_DB_URL = "sqlite:///./migrations/images.db"
SQLITE_DB_ABS_PATH = "./migrations/images.db"
TABLES = ['users', 'orders']  # 或动态获取
BATCH_SIZE = 1000

def convert_row(table, row, columns):
    # 针对特定列做转换示例
    converted = []
    for col, val in zip(columns, row):
        if val is None:
            converted.append(None)
            continue
        if col == 'created_at':
            # SQLite 里可能是 '2024-05-01 13:20:11' 或时间戳
            if isinstance(val, str):
                converted.append(val)  # 直接用 DATETIME 格式
            else:
                converted.append(datetime.fromtimestamp(val).strftime('%Y-%m-%d %H:%M:%S'))
        elif col == 'is_active':
            converted.append(int(val))  # 确保是 0/1
        else:
            converted.append(val)
    return converted

def sqlite_type_to_mysql(sqlite_type):
    """将 SQLite 类型转换为 MySQL 类型"""
    sqlite_type = sqlite_type.upper()

    if 'INT' in sqlite_type:
        return 'INT'
    elif 'CHAR' in sqlite_type or 'CLOB' in sqlite_type:
        return 'TEXT'
    elif 'TEXT' in sqlite_type:
        return 'TEXT'
    elif 'BLOB' in sqlite_type:
        return 'BLOB'
    elif 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
        return 'DOUBLE'
    elif 'DATE' in sqlite_type:
        return 'DATETIME'
    elif 'TIME' in sqlite_type:
        return 'DATETIME'
    else:
        return 'VARCHAR(255)'

def create_mysql_tables_from_sqlite(sqlite_conn, session, table_names):
    """使用原生 SQL 在 MySQL 中创建表"""
    cursor = sqlite_conn.cursor()

    for table_name in table_names:
        logger.info(f"正在创建表: {table_name}")

        # 获取 SQLite 表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()

        # 构建 MySQL CREATE TABLE 语句
        column_definitions = []
        for col in columns_info:
            col_id, col_name, col_type, not_null, default_value, is_pk = col

            # 转换类型
            mysql_type = sqlite_type_to_mysql(col_type)

            # 构建列定义
            col_def = f"`{col_name}` {mysql_type}"

            if not_null:
                col_def += " NOT NULL"

            if is_pk:
                col_def += " PRIMARY KEY"

            if default_value is not None:
                col_def += f" DEFAULT {default_value}"

            column_definitions.append(col_def)

        # 创建表的 SQL
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            {', '.join(column_definitions)}
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """

        # 执行创建表
        session.execute(text(create_table_sql))
        session.commit()
        logger.info(f"表 {table_name} 创建成功")

def main():
    # 创建数据库引擎
    engine = create_engine(SQLITE_DB_URL)
    # 创建 Inspector 对象
    inspector = inspect(engine)
    # 获取所有表名
    table_names = inspector.get_table_names()
    logger.info(f"所有的SQLite数据库表名： {table_names}")


    sqlite_conn = sqlite3.connect(SQLITE_DB_ABS_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    with db_manager.session_scope() as session:
        # 第一步：创建表
        logger.info("========== 开始创建表结构 ==========")
        create_mysql_tables_from_sqlite(sqlite_conn, session, table_names)
        logger.info("========== 表结构创建完成 ==========\n")

        # 第二步：导入数据
        logger.info("========== 开始导入数据 ==========")
        for table in table_names:
            # 获取列名
            cur = sqlite_conn.execute(f'SELECT * FROM {table} LIMIT 0')
            columns = [d[0] for d in cur.description]

            # 使用命名参数
            placeholders = ','.join([f':{col}' for col in columns])
            insert_sql = f'INSERT INTO {table} ({",".join(columns)}) VALUES ({placeholders})'

            offset = 0
            while True:
                rows = sqlite_conn.execute(f'SELECT * FROM {table} LIMIT {BATCH_SIZE} OFFSET {offset}').fetchall()
                if not rows:
                    break

                # 关键修改：转换为字典列表
                batch = []
                for r in rows:
                    converted_row = convert_row(table, tuple(r), columns)
                    # 将转换后的 tuple/list 组合成字典
                    row_dict = dict(zip(columns, converted_row))
                    batch.append(row_dict)

                # 执行批量插入
                session.execute(text(insert_sql), batch)
                session.commit()

                offset += BATCH_SIZE
                print(f'Table {table}: imported {offset}')

        sqlite_conn.close()

if __name__ == '__main__':
    print_current_env()
    # init_db()
    main()