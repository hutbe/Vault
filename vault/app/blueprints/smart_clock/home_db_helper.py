
from .home_db import db_manager
from .home_model import HomeClimate, Fridge, SensorDHT22
from .weather_models import WeatherRealtime, WeatherForecast
from .device_models import SystemDeviceSnapshot

import pytz

from sqlalchemy import text
from sqlalchemy import func

from datetime import timedelta, datetime

from ...utils import get_param, is_date_format_valid, validate_and_parse_utc

from loguru import logger

def read_current_climate(location_id):
    """
    Args:
        location_id: 位置id

    Returns:
        包含标签和各项数据的字典
    """
    # 获取当前 UTC 时间
    current_utc = datetime.now(pytz.utc)

    # for testing
    # time_str = "2026-01-05 08:55:02.000"
    # dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
    # current_utc = dt.replace(tzinfo=pytz.utc)

    # 获取 30 分钟前的 UTC 时间
    minutes_ago_utc = current_utc - timedelta(minutes=30)

    sensor_id = location_id
    device_id = location_id
    city_id = 6958812

    # location_id 1 pi 客厅对应device_id为1
    # location_id 2 和 3 共用同一个设备, pico 冰箱 
    if location_id in (2, 3):
        device_id = 2
    elif location_id == 1:
        device_id = 1
    elif location_id == 4:
        pass
    else:
        pass

    try:
        with db_manager.session_scope() as session:
            dht22 = session.query(SensorDHT22).filter(
                SensorDHT22.created_at >= minutes_ago_utc,
                SensorDHT22.created_at <= current_utc,
                SensorDHT22.sensor_id == sensor_id
            ).order_by(
                SensorDHT22.created_at.desc()
            ).first()

            weather = session.query(WeatherRealtime).filter(
                WeatherRealtime.created_at >= minutes_ago_utc,
                WeatherRealtime.created_at <= current_utc,
                WeatherRealtime.city_id == city_id
            ).order_by(
                WeatherRealtime.created_at.desc()
            ).first()

            sys_device = session.query(SystemDeviceSnapshot).filter(
                SystemDeviceSnapshot.timestamp >= minutes_ago_utc,
                SystemDeviceSnapshot.timestamp <= current_utc,
                SystemDeviceSnapshot.device_id == device_id
            ).order_by(
                SystemDeviceSnapshot.timestamp.desc()
            ).first()

            client_timezone = pytz.timezone('Asia/Shanghai') # pytz.utc
            utc_timezone = pytz.utc

            dht22_date = utc_timezone.localize(dht22.created_at) if dht22 else None
            weather_date = utc_timezone.localize(weather.created_at) if weather else None
            device_date = utc_timezone.localize(sys_device.timestamp) if sys_device else None
            dht22_date_str = dht22_date.astimezone(client_timezone).isoformat() if dht22_date else  ""
            weather_date_str = weather_date.astimezone(client_timezone).isoformat() if weather_date else  ""
            device_date_str = device_date.astimezone(client_timezone).isoformat() if device_date else  ""

            res_dic = {"temperature": "",
                       "humidity": "",
                       "weather": "",
                       "weather_code": "",
                       "weather_des": "",
                       "weather_icon": "",
                       "outdoors_temp": "",
                       "outdoors_feels_like": "",
                       "outdoors_humidity": "",
                       "wind_deg": "",
                       "time_sensor": dht22_date_str,
                       "time_weather": weather_date_str,
                       "time_system_device": device_date_str,
                       "cup_temp": ""
                       }
            if dht22:
                res_dic["temperature"] = dht22.temperature
                res_dic["humidity"] = dht22.humidity

            if weather:
                res_dic["weather"] = weather.weather_type.main
                res_dic["weather_code"] = weather.weather_type.weather_id
                res_dic["weather_des"] = weather.weather_type.description
                res_dic["weather_icon"] = weather.weather_type.icon


                res_dic["outdoors_temp"] = weather.temp
                res_dic["outdoors_feels_like"] = weather.feels_like
                res_dic["outdoors_humidity"] = weather.humidity
                res_dic["wind_deg"] = weather.wind_deg

            if sys_device:
                res_dic["cup_temp"] = sys_device.cpu_temperature
                res_dic["memory_usage_percent"] = sys_device.memory_usage_percent
                res_dic["storage_usage_percent"] = sys_device.storage_usage_percent
                res_dic["uptime_seconds"] = sys_device.uptime_seconds

            return res_dic
    except Exception as e:
        raise ValueError(f"查询错误{e}")


def read_home_climate_records(location_id, start_date, end_date, timezone='Asia/Shanghai'):
    """
    Args:
        location_id: 位置id
        start_date: 开始日期 (格式: YYYY-MM-DD HH:MM:SS)
        end_date: 结束日期 (格式: YYYY-MM-DD HH:MM:SS)
        timezone: IANA 时区标识符,默认为中国上海,eg:Asia/Shanghai,Asia/Hong_Kong,Asia/Taipei,Africa/Cairo,America/New_York,Pacific/Auckland

    Returns:
        包含标签和各项数据的字典
    """

    start_datetime = validate_and_parse_utc(start_date)
    end_datetime = validate_and_parse_utc(end_date)

    # start_datetime_utc_string = start_datetime.astimezone(pytz.utc).isoformat()
    # logger.info(f"start_datetime_utc_string: {start_datetime_utc_string}")

    if not start_datetime or not end_datetime:
        raise ValueError("时间参数格式错误")

    if start_datetime > end_datetime:
        start_datetime, end_datetime = end_datetime, start_datetime

    # 计算时间差
    diff = end_datetime - start_datetime
    is_over_24h = diff > timedelta(hours=24)
    if is_over_24h:
        raise IndexError("查询记录的跨度不能超过24小时")

    # 获取时区信息
    utc_timezone = pytz.utc
    client_timezone = start_datetime.tzinfo
    if client_timezone is None:
        client_timezone = pytz.timezone(timezone)

    #logger.info(f'B start_date: {start_datetime.isoformat()} end_date: {end_datetime.isoformat()} client_timezone: {utc_timezone}')

    start_datetime_utc = start_datetime.astimezone(utc_timezone)
    end_datetime_utc = end_datetime.astimezone(utc_timezone)

    #logger.info(f'A start_date: {start_datetime_utc.isoformat()} end_date: {end_datetime_utc.isoformat()} client_timezone: {client_timezone}')

    sensor_id = location_id
    try:
        with db_manager.session_scope() as session:
            datas = session.query(SensorDHT22).filter(
                SensorDHT22.created_at >= start_datetime_utc,
                SensorDHT22.created_at <= end_datetime_utc,
                SensorDHT22.sensor_id == sensor_id
            ).order_by(
                SensorDHT22.created_at
            ).all()

            # 处理数据和时区转换
            processed_datas = []
            processed_data2 = []
            for data in datas:
                item_dic = {}
                # 处理时区转换
                create_time_obj = data.created_at
                # 如果 create_date 是 naive datetime（无时区信息）
                if create_time_obj.tzinfo is None:
                    # 给create_time_obj添加时区信息
                    utc_datetime = utc_timezone.localize(create_time_obj)
                # 将utc_datetime转换到client_timezone时区
                local_time = utc_datetime.astimezone(client_timezone)

                local_timestamps = local_time.strftime("%H:%M")
                # logger.info(f"local_time: {local_time} local_timestamps: {local_timestamps}")
                item_dic = {"time":local_timestamps, "temp": data.temperature, "hum": data.humidity}
                processed_data2.append(item_dic)

            return {"records": processed_data2,
                    "timezone": client_timezone.tzname(None)}

    except Exception as e:
        raise ValueError(f"查询错误{e}")

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
            # createDates = [record.create_date.strftime("%H:%M") for record in records]
            outdoors_temp = [record.outdoors_temp for record in records]

            utc_timezone = pytz.utc
            shanghai_tz = pytz.timezone('Asia/Shanghai')
            createDates = [
                record.create_date.replace(tzinfo=utc_timezone)
                .astimezone(shanghai_tz)
                .strftime("%H:%M")
                for record in records
            ]

            temperatures.reverse()
            humidities.reverse()
            cup_temps.reverse()
            cpu_used_rates.reverse()
            createDates.reverse()
            outdoors_temp.reverse()

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
