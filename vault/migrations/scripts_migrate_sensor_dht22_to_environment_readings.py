import sys
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# 保持与现有迁移脚本一致：临时加入项目根目录以导入业务 db_manager
sys.path.insert(0, str(ROOT_DIR))
from app.blueprints.smart_clock.home_db import db_manager
sys.path.pop(0)

SOURCE_TABLE = "sensor_dht22"
TARGET_TABLE = "environment_readings"
BATCH_SIZE = 2000

SENSOR_MAPPING = {
    10: {"location_root_id": 2, "location_id": 3, "sensor_id": 2, "sensor_type": 3},
    100: {"location_root_id": 2, "location_id": 3, "sensor_id": 7, "sensor_type": 5},
    2: {"location_root_id": 2, "location_id": 13, "sensor_id": 2, "sensor_type": 3},
    3: {"location_root_id": 2, "location_id": 14, "sensor_id": 3, "sensor_type": 3},
    4: {"location_root_id": 2, "location_id": 9, "sensor_id": 3, "sensor_type": 3},
}

DEFAULT_MAPPING = {"location_root_id": 1, "location_id": 1, "sensor_id": 1, "sensor_type": 1}


def resolve_target_sensor_info(source_sensor_id):
    return SENSOR_MAPPING.get(source_sensor_id, DEFAULT_MAPPING)


def build_target_row(source_row):
    target_sensor_info = resolve_target_sensor_info(source_row["sensor_id"])
    return {
        "location_root_id": target_sensor_info["location_root_id"],
        "location_id": target_sensor_info["location_id"],
        "sensor_id": target_sensor_info["sensor_id"],
        "sensor_type": target_sensor_info["sensor_type"],
        "temperature": source_row["temperature"],
        "humidity": source_row["humidity"],
        "created_at": source_row["created_at"],
        "created_at_iso": source_row["created_at_iso"],
        "received_at": source_row["received_at"],
    }


def migrate_data():
    select_sql = text(
        f"""
        SELECT id, sensor_id, temperature, humidity, created_at, created_at_iso, received_at
        FROM {SOURCE_TABLE}
        WHERE id > :last_id
        ORDER BY id ASC
        LIMIT :batch_size
        """
    )

    insert_sql = text(
        f"""
        INSERT INTO {TARGET_TABLE} (
            location_root_id,
            location_id,
            sensor_id,
            sensor_type,
            temperature,
            humidity,
            created_at,
            created_at_iso,
            received_at
        ) VALUES (
            :location_root_id,
            :location_id,
            :sensor_id,
            :sensor_type,
            :temperature,
            :humidity,
            :created_at,
            :created_at_iso,
            :received_at
        )
        """
    )

    total_migrated = 0
    last_id = 0
    source_sensor_stats = defaultdict(int)
    target_sensor_stats = defaultdict(int)

    with db_manager.session_scope() as session:
        logger.info("========== 开始迁移 sensor_dht22 -> environment_readings ==========")

        while True:
            rows = session.execute(
                select_sql, {"last_id": last_id, "batch_size": BATCH_SIZE}
            ).mappings().all()

            if not rows:
                break

            batch = []
            for row in rows:
                source_sensor_stats[row["sensor_id"]] += 1
                mapped = resolve_target_sensor_info(row["sensor_id"])
                target_key = (
                    mapped["location_root_id"],
                    mapped["location_id"],
                    mapped["sensor_id"],
                    mapped["sensor_type"],
                )
                target_sensor_stats[target_key] += 1
                batch.append(build_target_row(row))

            session.execute(insert_sql, batch)
            session.commit()

            last_id = rows[-1]["id"]
            total_migrated += len(rows)
            logger.info(
                "已迁移 {} 行，当前处理到 source id={}",
                total_migrated,
                last_id,
            )

    logger.success("迁移完成，总共迁移 {} 行", total_migrated)
    logger.info("源表 sensor_id 分布: {}", dict(sorted(source_sensor_stats.items())))
    logger.info("目标映射分布: {}", dict(sorted(target_sensor_stats.items())))


def main():
    migrate_data()


if __name__ == "__main__":
    raise SystemExit(main())
