
# vault.db 原始数据有问题,先修复数据库
# UPDATE movie SET id = id + 10 WHERE id < 10;
# update recommendations set reference_movie_id=0 where reference_movie_id='hut';

import os
import sqlite3

from datetime import datetime
from loguru import logger

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session

from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# 更改下面为目标数据库
MARIADB_DB_URL = "mysql+pymysql://hut:hut123456@127.0.0.1:3306/vault_db"  # mariadb连接
SQLITE_DB_FILE_PATH = "./migrations/vault.db"  # sqlite直接连接,读取数据用

SQLITE_DB_URL = f"sqlite:///{SQLITE_DB_FILE_PATH}"  # sqlalchemy 读取表结构用
BATCH_SIZE = 2000

# ========== 关键修改：定义表的插入顺序 ==========
# 按照外键依赖关系排序，父表在前，子表在后
TABLE_INSERT_ORDER = [
    # 第0层：完全独立的表（无外键依赖）
    'area',
    'type',
    'tag',
    'language',
    'celebrity',
    'movie_brief',

    # 第1层：依赖第0层的表
    'movie',  # 注意：movie虽然有多对多关系，但主表本身不依赖外键

    # 第2层：多对多关联表（依赖movie和其他表）
    'celebrity_area',  # 依赖 celebrity, area
    'movie_director',  # 依赖 movie, celebrity
    'movie_actor',  # 依赖 movie, celebrity
    'movie_scenarist',  # 依赖 movie, celebrity
    'movie_area',  # 依赖 movie, area
    'movie_type',  # 依赖 movie, type
    'movie_tag',  # 依赖 movie, tag
    'movie_language',  # 依赖 movie, language

    # 第3层：依赖movie和其他表的子表
    'best_movies',  # 依赖 celebrity, movie_brief
    'recommendations',  # 依赖 movie, movie_brief
    'hot_comment',  # 依赖 movie
    'review',  # 依赖 movie
]


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
        if col == 'created_at' or col == 'create_date':
            # SQLite 里可能是 '2024-05-01 13:20:11' 或时间戳
            if isinstance(val, str):
                converted.append(val)  # 直接用 DATETIME 格式
            else:
                converted.append(datetime.fromtimestamp(val).strftime('%Y-%m-%d %H:%M:%S'))
        elif col == 'is_active' or col.startswith('is_'):
            converted.append(int(val) if val else 0)  # 确保是 0/1
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


def get_ordered_table_names(all_tables):
    """
    根据预定义的顺序和实际存在的表，返回有序的表名列表

    Args:
        all_tables: 实际存在的所有表名

    Returns:
        按依赖顺序排列的表名列表
    """
    # 转换为集合便于查找
    existing_tables = set(all_tables)

    # 按顺序筛选出实际存在的表
    ordered_tables = [t for t in TABLE_INSERT_ORDER if t in existing_tables]

    # 检查是否有未在顺序列表中的表
    unordered_tables = existing_tables - set(TABLE_INSERT_ORDER)

    if unordered_tables:
        logger.warning(f"⚠️  警告：以下表未在插入顺序列表中，将追加到末尾: {unordered_tables}")
        ordered_tables.extend(sorted(unordered_tables))

    return ordered_tables


def truncate_all_tables(session, table_names):
    """
    按逆序清空所有表（避免外键约束问题）

    Args:
        session: MariaDB会话
        table_names: 按依赖顺序排列的表名列表
    """
    logger.info("========== 开始清空已有数据 ==========")

    try:
        # 禁用外键检查
        session.execute(text("SET FOREIGN_KEY_CHECKS=0"))

        # 按逆序清空（子表先清空）
        for table in reversed(table_names):
            try:
                session.execute(text(f"TRUNCATE TABLE `{table}`"))
                logger.info(f"  ✓ 已清空表: {table}")
            except Exception as e:
                logger.warning(f"  ⚠️  表 {table} 不存在或清空失败: {e}")

        # 恢复外键检查
        # session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        session.commit()
        logger.info("========== 数据清空完成 ==========\n")

    except Exception as e:
        logger.error(f"清空表时发生错误: {e}")
        session.rollback()
        raise


def migrate_table_data(table, sqlite_conn, session):
    """
    迁移单个表的数据

    Args:
        table: 表名
        sqlite_conn: SQLite连接
        session: MariaDB会话
    """
    try:
        # 获取列名
        cur = sqlite_conn.execute(f'SELECT * FROM {table} LIMIT 0')
        columns = [d[0] for d in cur.description]

        if 'createDate' in columns:
            # 将原来的SQLite数据库中的createDate字段替换成create_date字段，转到mysql中
            columns = [col.replace('createDate', 'create_date') for col in columns]

        # 检查是否有 id 列
        has_id_column = 'id' in columns

        # ========== 关键修复：插入前禁用自增 ==========
        if has_id_column:
            try:
                # 查询当前表的列信息，检查 id 是否有 AUTO_INCREMENT
                check_sql = f"""
                SELECT EXTRA FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = '{table}' 
                AND COLUMN_NAME = 'id'
                """
                result = session.execute(text(check_sql)).fetchone()
                has_auto_increment = result and 'auto_increment' in str(result[0]).lower()

                if has_auto_increment:
                    # 禁用外键检查
                    session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                    # 临时移除 AUTO_INCREMENT 属性
                    session.execute(text(f"ALTER TABLE `{table}` MODIFY `id` BIGINT NOT NULL"))
                    # 恢复外键检查
                    # session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                    session.commit()
                    logger.debug(f"  已临时移除表 {table} 的 AUTO_INCREMENT 属性")
            except Exception as e:
                logger.warning(f"  检查/移除自增属性失败: {e}")
                session.rollback()

        target_table = table
        if table == 'surroundings':
            # 将原来的SQLite数据库中的surroundings表, 映射到新数据库的home_climate表
            target_table = 'home_climate'

        # 使用命名参数
        placeholders = ','.join([f':{col}' for col in columns])
        insert_sql = f'INSERT INTO {target_table} ({",".join(columns)}) VALUES ({placeholders})'

        offset = 0
        total_rows = 0
        max_id = 0  # 记录最大的 id 值

        while True:
            rows = sqlite_conn.execute(
                f'SELECT * FROM {table} LIMIT {BATCH_SIZE} OFFSET {offset}'
            ).fetchall()

            if not rows:
                break

            # 转换为字典列表
            batch = []
            for r in rows:
                converted_row = convert_row(table, tuple(r), columns)
                row_dict = dict(zip(columns, converted_row))
                batch.append(row_dict)

                # 记录最大的 id 值
                if has_id_column and row_dict.get('id') is not None:
                    max_id = max(max_id, int(row_dict['id']))

            # 执行批量插入
            session.execute(text(insert_sql), batch)
            session.commit()

            offset += BATCH_SIZE
            total_rows += len(rows)

            # 只在导入大量数据时显示进度
            if total_rows % (BATCH_SIZE * 5) == 0:
                logger.info(f'  ... 表 {table}: 已导入 {total_rows} 行')

        # ========== 关键修复：插入后恢复自增并重置计数器 ==========
        if has_id_column and max_id >= 0:
            try:
                # 禁用外键检查
                session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
                # 恢复 AUTO_INCREMENT 属性并设置起始值
                restore_sql = f"ALTER TABLE `{table}` MODIFY `id` BIGINT NOT NULL AUTO_INCREMENT, AUTO_INCREMENT = {max_id + 1}"
                session.execute(text(restore_sql))
                # 恢复外键检查
                # session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
                session.commit()
                logger.debug(f"  恢复表 {table} 的 AUTO_INCREMENT，起始值为 {max_id + 1}")
            except Exception as e:
                logger.warning(f"  恢复自增属性失败: {e}")
                session.rollback()

        if total_rows > 0:
            logger.success(f'✅ 表 {table}: 共导入 {total_rows} 行数据 (max_id={max_id})')
        else:
            logger.info(f'ℹ️  表 {table}: 无数据')

        return total_rows

    except Exception as e:
        logger.error(f'❌ 表 {table} 导入失败: {e}')
        raise


def main():
    # 创建数据库引擎
    engine = create_engine(SQLITE_DB_URL)
    # 创建 Inspector 对象
    inspector = inspect(engine)
    # 获取所有表名
    all_table_names = inspector.get_table_names()
    logger.info(f"📚 SQLite数据库中的所有表: {all_table_names}")

    # ========== 关键修改：按依赖顺序排序表 ==========
    ordered_table_names = get_ordered_table_names(all_table_names)
    logger.info(f"📋 按依赖顺序排列的表: {ordered_table_names}")

    with db_manager.session_scope() as session:
        # 第一步：创建表（按依赖顺序）
        logger.info("\n========== 开始创建表结构 ==========")
        # create_mysql_tables_from_sqlite(SQLITE_DB_FILE_PATH, session, ordered_table_names)
        logger.info("========== 表结构创建完成 ==========\n")

        # ========== 新增：清空已有数据 ==========
        truncate_all_tables(session, ordered_table_names)

        # 第二步：导入数据（按依赖顺序）
        logger.info("========== 开始导入数据 ==========")
        sqlite_conn = sqlite3.connect(SQLITE_DB_FILE_PATH)
        sqlite_conn.row_factory = sqlite3.Row

        total_migrated = 0
        failed_tables = []

        # ========== 关键修改：使用排序后的表列表 ==========
        for idx, table in enumerate(ordered_table_names, 1):
            logger.info(f"\n[{idx}/{len(ordered_table_names)}] 正在迁移表: {table}")

            try:
                rows_count = migrate_table_data(table, sqlite_conn, session)
                total_migrated += rows_count
            except Exception as e:
                failed_tables.append(table)
                logger.error(f"表 {table} 迁移失败: {str(e)[:200]}")
                logger.error(f"继续下一个表...")
                continue

        sqlite_conn.close()

        # 恢复外键检查
        session.execute(text("SET FOREIGN_KEY_CHECKS=1"))

        # 迁移总结
        logger.info("\n" + "=" * 50)
        logger.info("========== 数据迁移完成 ==========")
        logger.info(f"✅ 成功迁移表数量: {len(ordered_table_names) - len(failed_tables)}/{len(ordered_table_names)}")
        logger.info(f"📊 总共迁移数据行数: {total_migrated}")

        if failed_tables:
            logger.warning(f"⚠️  失败的表 ({len(failed_tables)}): {failed_tables}")
        else:
            logger.success("🎉 所有表迁移成功！")

        logger.info("=" * 50)


if __name__ == '__main__':
    raise SystemExit(main())