import os
import sqlite3

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from ..app.blueprints.image_service.image_db_initializer import init_db, add_image_types
from ..app.blueprints.image_service.image_db import db_manager



# 方案1：让 python-dotenv 自动向上寻找 .env（当前工作目录为执行命令所在目录）
# load_dotenv()  # 如果你从项目根目录执行：python scripts/task_a.py

# 方案2：指定路径，避免因为“在其他目录执行”找不到
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

def print_current_env():
    print("DB_HOST =", os.getenv("DB_HOST"))
    print("DB_PORT =", os.getenv("DB_PORT"))
    print("DB_ROOT_PASSWORD =", os.getenv("DB_ROOT_PASSWORD"))

    print("DB_DATABASE =", os.getenv("DB_DATABASE"))
    print("DB_USER =", os.getenv("DB_USER"))
    print("DB_PASSWORD =", os.getenv("DB_PASSWORD"))

SQLITE_DB = 'images.db'
TABLES = ['users', 'orders']  # 或动态获取
BATCH_SIZE = 1000

maria_conf = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'maria_user',
    'password': 'secret',
    'database': 'mydb',
    'charset': 'utf8mb4'
}

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

def main():
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_conn.row_factory = sqlite3.Row
    maria_conn = mysql.connector.connect(**maria_conf)
    maria_cur = maria_conn.cursor()

    for table in TABLES:
        # 获取列名
        cur = sqlite_conn.execute(f'SELECT * FROM {table} LIMIT 0')
        columns = [d[0] for d in cur.description]
        placeholders = ','.join(['%s'] * len(columns))
        insert_sql = f'INSERT INTO {table} ({",".join(columns)}) VALUES ({placeholders})'
        offset = 0
        while True:
            rows = sqlite_conn.execute(f'SELECT * FROM {table} LIMIT {BATCH_SIZE} OFFSET {offset}').fetchall()
            if not rows:
                break
            batch = [convert_row(table, tuple(r), columns) for r in rows]
            maria_cur.executemany(insert_sql, batch)
            maria_conn.commit()
            offset += BATCH_SIZE
            print(f'Table {table}: imported {offset}')
    maria_cur.close()
    maria_conn.close()
    sqlite_conn.close()

if __name__ == '__main__':
    print_current_env()
    # main()