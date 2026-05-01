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

SOURCE_TABLE = "system_device_snapshots"
TARGET_TABLE = "edge_device_metric"
BATCH_SIZE = 2000

DEVICE_MAPPING = {
    1: {"location_root_id": 2, "location_id": 3, "device_id": 1},
    2: {"location_root_id": 2, "location_id": 3, "device_id": 2},
    4: {"location_root_id": 2, "location_id": 3, "device_id": 3},
}

DEFAULT_MAPPING = {"location_root_id": 1, "location_id": 1, "device_id": 1}


def resolve_target_device_info(source_device_id):
    return DEVICE_MAPPING.get(source_device_id, DEFAULT_MAPPING)


def build_target_row(source_row):
    target_device_info = resolve_target_device_info(source_row["device_id"])
    return {
        "location_root_id": target_device_info["location_root_id"],
        "location_id": target_device_info["location_id"],
        "device_id": target_device_info["device_id"],
        "created_at_iso": source_row["created_at_iso"],
        "timestamp": source_row["timestamp"],
        "platform": source_row["platform"],
        "os_version": source_row["os_version"],
        "cpu_frequency_mhz": source_row["cpu_frequency_mhz"],
        "cpu_temperature": source_row["cpu_temperature"],
        "total_storage_bytes": source_row["total_storage_bytes"],
        "used_storage_bytes": source_row["used_storage_bytes"],
        "free_storage_bytes": source_row["free_storage_bytes"],
        "storage_usage_percent": source_row["storage_usage_percent"],
        "total_memory_bytes": source_row["total_memory_bytes"],
        "used_memory_bytes": source_row["used_memory_bytes"],
        "free_memory_bytes": source_row["free_memory_bytes"],
        "memory_usage_percent": source_row["memory_usage_percent"],
        "uptime_seconds": source_row["uptime_seconds"],
        "reset_reason": source_row["reset_reason"],
        "battery_level_percent": source_row["battery_level_percent"],
        "ip": source_row["ip"],
        "mac": source_row["mac"],
        "subnet": source_row["subnet"],
        "dns": source_row["dns"],
        "gateway": source_row["gateway"],
        "rssi": source_row["rssi"],
        "extra_data": source_row["extra_data"],
    }


def migrate_data():
    select_sql = text(
        f"""
        SELECT
            id,
            device_id,
            created_at_iso,
            timestamp,
            platform,
            os_version,
            cpu_frequency_mhz,
            cpu_temperature,
            total_storage_bytes,
            used_storage_bytes,
            free_storage_bytes,
            storage_usage_percent,
            total_memory_bytes,
            used_memory_bytes,
            free_memory_bytes,
            memory_usage_percent,
            uptime_seconds,
            reset_reason,
            battery_level_percent,
            ip,
            mac,
            subnet,
            dns,
            gateway,
            rssi,
            extra_data
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
            device_id,
            created_at_iso,
            timestamp,
            platform,
            os_version,
            cpu_frequency_mhz,
            cpu_temperature,
            total_storage_bytes,
            used_storage_bytes,
            free_storage_bytes,
            storage_usage_percent,
            total_memory_bytes,
            used_memory_bytes,
            free_memory_bytes,
            memory_usage_percent,
            uptime_seconds,
            reset_reason,
            battery_level_percent,
            ip,
            mac,
            subnet,
            dns,
            gateway,
            rssi,
            extra_data
        ) VALUES (
            :location_root_id,
            :location_id,
            :device_id,
            :created_at_iso,
            :timestamp,
            :platform,
            :os_version,
            :cpu_frequency_mhz,
            :cpu_temperature,
            :total_storage_bytes,
            :used_storage_bytes,
            :free_storage_bytes,
            :storage_usage_percent,
            :total_memory_bytes,
            :used_memory_bytes,
            :free_memory_bytes,
            :memory_usage_percent,
            :uptime_seconds,
            :reset_reason,
            :battery_level_percent,
            :ip,
            :mac,
            :subnet,
            :dns,
            :gateway,
            :rssi,
            :extra_data
        )
        """
    )

    total_migrated = 0
    last_id = 0
    source_device_stats = defaultdict(int)
    target_device_stats = defaultdict(int)

    with db_manager.session_scope() as session:
        logger.info(
            "========== 开始迁移 system_device_snapshots -> edge_device_metric =========="
        )

        while True:
            rows = session.execute(
                select_sql, {"last_id": last_id, "batch_size": BATCH_SIZE}
            ).mappings().all()

            if not rows:
                break

            batch = []
            for row in rows:
                source_device_stats[row["device_id"]] += 1
                mapped = resolve_target_device_info(row["device_id"])
                target_key = (
                    mapped["location_root_id"],
                    mapped["location_id"],
                    mapped["device_id"],
                )
                target_device_stats[target_key] += 1
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
    logger.info("源表 device_id 分布: {}", dict(sorted(source_device_stats.items())))
    logger.info("目标映射分布: {}", dict(sorted(target_device_stats.items())))


def main():
    migrate_data()


if __name__ == "__main__":
    raise SystemExit(main())
