from venv import logger

from .home_db import db_manager
from .home_model import HomeClimate, Fridge

import pytz

from sqlalchemy import text
from sqlalchemy import func, literal, cast
from sqlalchemy.types import DateTime

from datetime import timedelta

from ...utils import get_param, is_date_format_valid

from loguru import logger

def read_home_climate_last_records_with_minutes(minutes):
    total_count = minutes // 5

    with db_manager.session_scope() as session:
        try:
            # 取最新 10 条记录（按 id 倒序）
            records = session.query(HomeClimate) \
                .order_by(HomeClimate.id.desc()) \
                .limit(total_count) \
                .all()

            temperatures = [record.temperature for record in records]
            humidities = [record.humidity for record in records]
            cup_temps = [record.cup_temp for record in records]
            cpu_used_rates = [record.cpu_used_rate for record in records]
            createDates = [record.create_date.strftime("%H:%M") for record in records]
            outdoors_temp = [record.outdoors_temp for record in records]

            return {
                "labels": createDates,
                "temp": temperatures,
                "humi": humidities,
                "cuptemp": cup_temps,
                "cpu_used_rates": cpu_used_rates,
                "outdoors_temp": outdoors_temp
            }
        except Exception as e:
            raise e

def read_home_climate_last_records_with_period(start_date, end_date):
    # 计算偏移量（+8小时）时区
    offset = timedelta(hours=8)
    with db_manager.session_scope() as session:
        try:
            records = session.query(HomeClimate) \
                    .filter(
                    func.datetime(HomeClimate.create_date, 'localtime') + offset >= start_date,
                    func.datetime(HomeClimate.create_date, 'localtime') + offset <= end_date
                ) \
                    .order_by(HomeClimate.create_date) \
                    .limit(1) \
                    .all()

            # 使用原生 SQL
            # from sqlalchemy import text
            # records = session.query(HomeClimate).from_statement(
            #     text("""
            #     SELECT *
            #     FROM (
            #         SELECT *, DATETIME(createDate, '+8 hours') AS localTime
            #         FROM home_climate
            #     )
            #     WHERE localTime BETWEEN :start_date AND :end_date
            #     ORDER BY createDate
            #     LIMIT 1
            #     """)
            # ).params(start_date=start_date, end_date=end_date).all()

        except Exception as e:
            raise e

def read_home_climate_records_with_period(startDate, endDate):
    """
    根据时间周期读取环境数据记录

    Args:
        startDate: 开始日期 (格式: YYYY-MM-DD HH:MM:SS)
        endDate: 结束日期 (格式: YYYY-MM-DD HH:MM:SS)

    Returns:
        包含标签和各项数据的字典
    """
    if not is_date_format_valid(startDate) or not is_date_format_valid(endDate):
        return {
            "labels": [],
            "temp": [],
            "humi": [],
            "cuptemp": [],
            "cpu_used_rates": [],
            "outdoors_temp": []
        }

    try:
        with db_manager.session_scope() as session:
            # 使用 SQLAlchemy 查询，计算本地时间（+8小时）
            # 注意：MySQL 使用 DATE_ADD 或 TIMESTAMPADD 函数来添加时间偏移
            local_time = func.date_add(
                HomeClimate.create_date,
                text("INTERVAL 8 HOUR")
            )

            datas = session.query(HomeClimate) \
                .filter(
                local_time >= startDate,
                local_time <= endDate
            ) \
                .order_by(HomeClimate.create_date) \
                .all()

            # 如果没有数据，返回空结果
            if not datas:
                return {
                    "labels": [],
                    "temp": [],
                    "humi": [],
                    "cuptemp": [],
                    "cpu_used_rates": [],
                    "outdoors_temp": []
                }

            # 处理数据和时区转换
            processed_datas = []
            utc_timezone = pytz.utc
            target_timezone = pytz.timezone('Asia/Shanghai')

            for data in datas:
                item_dic = {
                    'temperature': data.temperature,
                    'humidity': data.humidity,
                    'cup_temp': data.cup_temp,
                    'cpu_used_rate': data.cpu_used_rate,
                    'outdoors_temp': data.outdoors_temp,
                    'create_date': data.create_date
                }

                # 处理时区转换
                time_obj = data.create_date

                # 如果 create_date 是 naive datetime（无时区信息）
                if time_obj.tzinfo is None:
                    # 假设数据库中的时间是 UTC 时间
                    utc_datetime = utc_timezone.localize(time_obj)
                else:
                    # 如果已有时区信息，先转换为 UTC
                    utc_datetime = time_obj.astimezone(utc_timezone)

                # 转换为上海时区
                local_time = utc_datetime.astimezone(target_timezone)
                item_dic['create_date'] = local_time

                processed_datas.append(item_dic)

            # 提取数据到各个列表
            temperatures = [item['temperature'] for item in processed_datas]
            humidities = [item['humidity'] for item in processed_datas]
            cup_temps = [item['cup_temp'] for item in processed_datas]
            cpu_used_rates = [item['cpu_used_rate'] for item in processed_datas]
            create_dates = [item['create_date'].strftime("%H:%M") for item in processed_datas]
            outdoors_temp = [item['outdoors_temp'] for item in processed_datas]

            return {
                "labels": create_dates,
                "temp": temperatures,
                "humi": humidities,
                "cuptemp": cup_temps,
                "cpu_used_rates": cpu_used_rates,
                "outdoors_temp": outdoors_temp
            }

    except Exception as e:
        print(f"读取数据出错: {e}")
        return {
            "labels": [],
            "temp": [],
            "humi": [],
            "cuptemp": [],
            "cpu_used_rates": [],
            "outdoors_temp": []
        }


def read_home_fridge_records_with_period(startDate, endDate):
    """
    根据时间周期读取环境数据记录

    Args:
        startDate: 开始日期 (格式: YYYY-MM-DD HH:MM:SS)
        endDate: 结束日期 (格式: YYYY-MM-DD HH:MM:SS)

    Returns:
        包含标签和各项数据的字典
    """
    if not is_date_format_valid(startDate) or not is_date_format_valid(endDate):
        return []

    try:
        with db_manager.session_scope() as session:
            # 使用 SQLAlchemy 查询，计算本地时间（+8小时）
            # 注意：MySQL 使用 DATE_ADD 或 TIMESTAMPADD 函数来添加时间偏移
            local_time = func.date_add(
                Fridge.create_date,
                text("INTERVAL 8 HOUR")
            )

            datas = session.query(Fridge) \
                .filter(
                local_time >= startDate,
                local_time <= endDate
            ) \
                .order_by(Fridge.create_date) \
                .all()

            # 如果没有数据，返回空结果
            if not datas:
                return []

            # 处理数据和时区转换
            processed_datas = []
            utc_timezone = pytz.utc
            target_timezone = pytz.timezone('Asia/Shanghai')

            for data in datas:
                # info_keys = ["id", "tag", "temperature", "humidity", "createDate"];
                item_dic = {
                    "id": data.id,
                    "tag": data.tag,
                    "temperature": data.temperature,
                    "humidity": data.humidity
                }

                # 处理时区转换
                time_obj = data.create_date

                # 如果 create_date 是 naive datetime（无时区信息）
                if time_obj.tzinfo is None:
                    # 假设数据库中的时间是 UTC 时间
                    utc_datetime = utc_timezone.localize(time_obj)
                else:
                    # 如果已有时区信息，先转换为 UTC
                    utc_datetime = time_obj.astimezone(utc_timezone)

                # 转换为上海时区
                local_time = utc_datetime.astimezone(target_timezone)
                item_dic['create_date'] = local_time

                processed_datas.append(item_dic)

            # 提取数据到各个列表
            # temperatures = [item['temperature'] for item in processed_datas]
            # humidities = [item['humidity'] for item in processed_datas]

            # info_keys = ["id", "tag", "temperature", "humidity", "createDate"];
            return processed_datas

    except Exception as e:
        print(f"读取数据出错: {e}")
        return []
