#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将 SQLite 数据库数据迁移到 MariaDB。
前提：
- 目标库的表结构已通过 Alembic/Flask-Migrate 或 Base.metadata.create_all 在 MariaDB 上创建好。
- 你的 SQLAlchemy 模型定义了完整的类型与外键约束。
使用：
  python scripts/migrate_sqlite_to_mariadb.py \
    --sqlite sqlite:///app.db \
    --mariadb mysql+pymysql://user:pass@host:3306/dbname \
    --batch-size 2000
"""

import argparse
from contextlib import contextmanager

from sqlalchemy import create_engine, MetaData, Table, select, text
from sqlalchemy.orm import Session

# TODO: 修改为你项目中 Base 的实际导入路径
# 例如：from app.extensions import db; Base = db.Model  或  from app.models import Base
from app.models import Base  # noqa: F401  # Base.metadata 将用于排序和表名参考
from app.models import Base as AppBase  # 为了清晰引用

DEFAULT_BATCH_SIZE = 2000


def parse_args():
    parser = argparse.ArgumentParser(description="Migrate data from SQLite to MariaDB.")
    parser.add_argument("--sqlite", required=True, help="SQLite SQLAlchemy URL, e.g. sqlite:///app.db")
    parser.add_argument("--mariadb", required=True, help="MariaDB URL, e.g. mysql+pymysql://user:pass@host:3306/dbname")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Batch size per insert")
    parser.add_argument("--skip-tables", nargs="*", default=[], help="Table names to skip")
    parser.add_argument("--only-tables", nargs="*", default=[], help="If set, migrate only these tables")
    parser.add_argument("--truncate-target", action="store_true", help="Truncate target tables before load")
    return parser.parse_args()


@contextmanager
def engine_connect(url, **kwargs):
    eng = create_engine(url, pool_pre_ping=True, future=True, **kwargs)
    try:
        with eng.connect() as conn:
            yield conn
    finally:
        eng.dispose()


def sorted_tables():
    # 依赖模型中的外键信息进行拓扑排序
    return list(AppBase.metadata.sorted_tables)


def reflect_table(conn, table_name):
    # 仅用于读取源（SQLite）数据
    meta = MetaData()
    return Table(table_name, meta, autoload_with=conn)


def migrate_table(src_conn, dst_conn, table, batch_size, truncate=False):
    """
    table: sqlalchemy Table (from Base.metadata.sorted_tables) 用于名称与顺序
    从 SQLite 反射 source_table，再批量 select + insert 到目标 MariaDB。
    """
    table_name = table.name
    source_table = reflect_table(src_conn, table_name)
    target_table = table  # 目标端结构以模型为准

    if truncate:
        dst_conn.execute(text(f"TRUNCATE TABLE `{table_name}`"))

    total_rows = 0
    result = src_conn.execute(select(source_table))
    while True:
        rows = result.fetchmany(batch_size)
        if not rows:
            break

        # 将 RowMapping 转换为 dict，确保只包含目标表的列，避免 SQLite 多余列/隐含列
        dicts = []
        tgt_cols = set(c.name for c in target_table.columns)
        for r in rows:
            d = {k: r[k] for k in r.keys() if k in tgt_cols}
            dicts.append(d)

        dst_conn.execute(target_table.insert(), dicts)
        total_rows += len(dicts)
    return total_rows


def main():
    args = parse_args()

    tables = sorted_tables()

    if args.only_tables:
        only = set(args.only_tables)
        tables = [t for t in tables if t.name in only]

    if args.skip_tables:
        skip = set(args.skip_tables)
        tables = [t for t in tables if t.name not in skip]

    # 连接源与目标
    with engine_connect(args.sqlite) as src_conn, engine_connect(args.mariadb) as dst_conn:
        # 提升导入性能：禁用外键/唯一检查（导入结束后恢复）
        dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        dst_conn.execute(text("SET UNIQUE_CHECKS=0"))

        try:
            # 可选：开启一个整体事务
            with dst_conn.begin():
                migrated_counts = {}
                for t in tables:
                    cnt = migrate_table(src_conn, dst_conn, t, args.batch_size, truncate=args.truncate_target)
                    migrated_counts[t.name] = cnt
                    print(f"[OK] {t.name}: migrated {cnt} rows")

        finally:
            dst_conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
            dst_conn.execute(text("SET UNIQUE_CHECKS=1"))

    print("Migration completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
