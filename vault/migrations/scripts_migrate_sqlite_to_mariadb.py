import os
import sqlite3

from datetime import datetime
from loguru import logger

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker,scoped_session

from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# 更改下面为目标数据库
MARIADB_DB_URL = "mysql+pymysql://hut:hut123456@127.0.0.1:3306/vault_db" # mariadb连接
SQLITE_DB_FILE_PATH = "./migrations/vault.db"      # sqlite直接连接，读取数据用

SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILE_PATH}"  # sqlalchemy 读取表结构用
BATCH_SIZE = 2000

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
            echo_pool=False,  # 生产环境设为 False
            echo=False,  # 生产环境设为 False

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

# 创建数据库引擎
db_manager = DatabaseManager(MARIADB_DB_URL)

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


def sqlite_type_to_mysql(sqlite_type, col_name=''):
    """将 SQLite 类型转换为 MySQL 类型"""
    if not sqlite_type:
        return 'TEXT'

    sqlite_type = sqlite_type.upper()

    # 特殊处理：如果是时间相关的 INTEGER 字段，使用 BIGINT
    if 'INT' in sqlite_type:
        # 检查字段名是否包含时间相关的关键词
        time_keywords = ['id', 'birthday', 'left_day', 'leaveday']
        if any(keyword in col_name.lower() for keyword in time_keywords):
            return 'BIGINT'  # 使用 BIGINT 存储 Unix 时间戳
        return 'INT'
    elif 'CHAR' in sqlite_type or 'CLOB' in sqlite_type:
        return 'TEXT'
    elif 'TEXT' in sqlite_type:
        return 'TEXT'
    elif 'BLOB' in sqlite_type:
        return 'BLOB'
    elif 'REAL' in sqlite_type or 'FLOA' in sqlite_type or 'DOUB' in sqlite_type:
        return 'DOUBLE'
    elif 'DATE' in sqlite_type or 'TIME' in sqlite_type:
        return 'DATETIME'
    else:
        return 'VARCHAR(255)'


def convert_default_value(default_value, col_type, col_name):
    """转换 SQLite 默认值为 MySQL 兼容格式"""
    if default_value is None:
        return None

    # 转换为字符串进行处理
    default_str = str(default_value).strip().strip("'\"")

    # 处理日期时间相关的默认值
    datetime_keywords = [
        'CURRENT_TIMESTAMP',
        'CURRENT_DATE',
        'CURRENT_TIME',
        "datetime('now')",
        "date('now')",
        "time('now')",
        'now()',
        '(datetime(\'now\'))',
        '(CURRENT_TIMESTAMP)'
    ]

    # 检查是否是日期时间函数
    for keyword in datetime_keywords:
        if keyword.upper() in default_str.upper():
            return 'CURRENT_TIMESTAMP'

    # 如果是数字类型
    if col_type in ['INT', 'DOUBLE', 'FLOAT']:
        try:
            # 尝试转换为数字
            if '.' in default_str:
                return float(default_str)
            else:
                return int(default_str)
        except ValueError:
            return None

    # 字符串类型
    return f"'{default_value}'"


def create_mysql_tables_from_sqlite(sqlite_db_path, mysql_session, table_names):
    """使用原生 SQL 在 MySQL 中创建表"""
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    cursor = sqlite_conn.cursor()

    try:
        for table_name in table_names:
            logger.info(f"正在创建表: {table_name}")

            # 获取 SQLite 表结构
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns_info = cursor.fetchall()

            if not columns_info:
                logger.warning(f"警告：表 {table_name} 没有列信息，跳过")
                continue

            logger.debug(f"表 {table_name} 的列信息: {columns_info}")

            # 构建 MySQL CREATE TABLE 语句
            column_definitions = []
            primary_keys = []

            for col in columns_info:
                col_id, col_name, col_type, not_null, default_value, is_pk = col

                # 转换类型
                mysql_type = sqlite_type_to_mysql(col_type, col_name)

                # 构建列定义
                col_def = f"`{col_name}` {mysql_type}"

                # 处理默认值
                converted_default = convert_default_value(default_value, mysql_type, col_name)

                # 添加 NOT NULL
                if not_null and not is_pk:
                    col_def += " NOT NULL"

                # 添加默认值
                if converted_default is not None:
                    if converted_default == 'CURRENT_TIMESTAMP':
                        col_def += " DEFAULT CURRENT_TIMESTAMP"
                    elif isinstance(converted_default, (int, float)):
                        col_def += f" DEFAULT {converted_default}"
                    else:
                        col_def += f" DEFAULT {converted_default}"

                column_definitions.append(col_def)

                if is_pk:
                    primary_keys.append(f"`{col_name}`")

            # 添加主键约束
            if primary_keys:
                column_definitions.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

            # 创建表的 SQL
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                {', '.join(column_definitions)}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """

            logger.debug(f"执行 SQL: {create_table_sql}")

            # 执行创建表
            mysql_session.execute(text(create_table_sql))
            mysql_session.commit()
            logger.info(f"表 {table_name} 创建成功")

    except Exception as e:
        logger.error(f"创建表时发生错误: {e}")
        mysql_session.rollback()
        raise

    finally:
        cursor.close()
        sqlite_conn.close()
        logger.debug("SQLite 表结构读取连接已关闭")

def main():
    # 创建数据库引擎
    engine = create_engine(SQLITE_DB_URL)
    # 创建 Inspector 对象
    inspector = inspect(engine)
    # 获取所有表名
    table_names = inspector.get_table_names()
    logger.info(f"所有的SQLite数据库表名： {table_names}")

    with db_manager.session_scope() as session:
        # 第一步：创建表
        logger.info("========== 开始创建表结构 ==========")
        # create_mysql_tables_from_sqlite(SQLITE_DB_FILE_PATH, session, table_names)
        logger.info("========== 表结构创建完成 ==========\n")

        sqlite_conn = sqlite3.connect(SQLITE_DB_FILE_PATH)
        sqlite_conn.row_factory = sqlite3.Row

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
    raise SystemExit(main())