import random
from datetime import datetime, timezone
from weather_api import WeatherAPI
from weather_config import API_KEY, CITIES, API_KEY2, API_KEY3
from weather_models import WeatherType, WeatherForecast, WeatherRealtime, City, SunriseSunset

from home_db import db_manager

def request_current_weather_data():
    # 创建API实例
    chosen_api_key = random.choice([API_KEY, API_KEY2, API_KEY3])
    api = WeatherAPI(chosen_api_key)

    # 获取天气
    city = CITIES["深圳"]
    #print("正在获取天气数据...")
    weather = api.get_current_weather(city["lat"], city["lon"])

    if weather:
        # print(f"温度: {weather.get('main', {}).get('temp')}°C")
        # print(f"天气: {weather.get('weather', [{}])[0].get('description')}")
        with db_manager.session_scope() as session:
            try:
                insert_current_weather_data(session, weather)
            except Exception as e:
                print(f"当前天气数据-写入数据库错误: {e}")

def request_weather_forecast_data():
    # 创建API实例
    chosen_api_key = random.choice([API_KEY, API_KEY2, API_KEY3])
    api = WeatherAPI(chosen_api_key)

    # 获取深圳天气
    city = CITIES["深圳"]
    #print("正在获取天气预报数据...")
    forecast = None
    forecast = api.get_forecast(city["lat"], city["lon"], cnt=40)

    if forecast:
        #print("未来天气预报:")
        for item in forecast.get('list', []):
            dt_txt = item.get('dt_txt')
            temp = item.get('main', {}).get('temp')
            description = item.get('weather', [{}])[0].get('description')
            #print(f"{dt_txt} - 温度: {temp}°C), 天气: {description}")
        with db_manager.session_scope() as session:
            try:
                insert_weather_forecast_data(session, forecast)
            except Exception as e:
                print(f"天气预报数据-写入数据库错误: {e}")

def insert_weather_forecast_data(session, weather_json):
    """
    将天气预报JSON数据插入数据库

    Args:
        session: SQLAlchemy会话对象
        weather_json: 天气预报API返回的JSON数据
    """

    """
    插入前检查是否已存在三个小时内的的预报记录，避免插入三个小时内的重复数据。增加120秒为接口请求时间
    """
    three_hours_ago = int((datetime.now(timezone.utc).timestamp()) - (3 * 3600) + 120)
    existing_forecast = session.query(WeatherForecast).filter(
        WeatherForecast.city_id == weather_json['city']['id'],
        WeatherForecast.forecast_dt >= three_hours_ago,
    ).first()
    if existing_forecast:
        print(f"✓ 城市 {weather_json['city']['name']} 已存在三个小时内的预报记录，跳过插入。")
        return

    # 1. 插入或更新城市信息
    city_data = weather_json['city']
    city = session.query(City).filter_by(id=city_data['id']).first()

    if not city:
        city = City(
            id=city_data['id'],
            name=city_data['name'],
            country=city_data['country'],
            latitude=city_data['coord']['lat'],
            longitude=city_data['coord']['lon'],
            population=city_data['population'],
            timezone=city_data['timezone']
        )
        session.add(city)

    # 2. 插入天气预报数据
    forecast_dt = int(datetime.now(timezone.utc).timestamp())
    forecast_dt_txt = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    for forecast_item in weather_json['list']:
        # 检查是否已存在相同的预报记录
        # existing_forecast = session.query(WeatherForecast).filter_by(
        #     city_id=city.id,
        #     dt=forecast_item['dt']
        # ).first()

        # if existing_forecast:
        #     continue  # 跳过已存在的记录
        # 2.1 获取或创建天气类型
        weather_type_id = None
        if forecast_item.get('weather') and len(forecast_item['weather']) > 0:
            weather_item = forecast_item['weather'][0]  # 取第一个天气状况
            weather_type = session.query(WeatherType).filter_by(
                weather_id=weather_item['id'],
                main=weather_item['main'],
                icon=weather_item['icon']
            ).first()

            if not weather_type:
                weather_type = WeatherType(
                    weather_id=weather_item['id'],
                    main=weather_item['main'],
                    description=weather_item['description'],
                    icon=weather_item['icon']
                )
                session.add(weather_type)
                session.flush()  # 立即获取生成的ID

            weather_type_id = weather_type.id

        # 创建预报记录
        forecast = WeatherForecast(
            city_id=city.id,
            forecast_dt = forecast_dt,
            forecast_dt_txt = forecast_dt_txt,
            dt=forecast_item['dt'],
            dt_txt=forecast_item['dt_txt'],
            temp=forecast_item['main']['temp'],
            feels_like=forecast_item['main']['feels_like'],
            temp_min=forecast_item['main']['temp_min'],
            temp_max=forecast_item['main']['temp_max'],
            pressure=forecast_item['main']['pressure'],
            sea_level=forecast_item['main']['sea_level'],
            grnd_level=forecast_item['main']['grnd_level'],
            humidity=forecast_item['main']['humidity'],
            temp_kf=forecast_item['main']['temp_kf'],
            clouds_all=forecast_item['clouds']['all'],
            wind_speed=forecast_item['wind']['speed'],
            wind_deg=forecast_item['wind']['deg'],
            wind_gust=forecast_item['wind'].get('gust'),
            visibility=forecast_item['visibility'],
            pop=forecast_item['pop'],
            sys_pod=forecast_item['sys']['pod'],
            rain_3h=forecast_item.get('rain', {}).get('3h'),
            snow_3h=forecast_item.get('snow', {}).get('3h'),
            weather_type_id=weather_type_id
        )
        session.add(forecast)

    # 提交事务
    session.commit()
    print(f"✓ 成功插入城市 {city.name} 的天气预报数据")


def insert_current_weather_data(session, current_weather_json):
    """
    将实时天气JSON数据插入数据库

    Args:
        session: SQLAlchemy会话对象
        current_weather_json: 实时天气API返回的JSON数据
    """

    """
    插入前检查是否已存在五分钟内的记录，避免插入五分钟内的重复数据。增加120秒为接口请求时间
    """
    six_minutes_ago = int((datetime.now(timezone.utc).timestamp()) - (5 * 60) + 120)
    existing_forecast = session.query(WeatherRealtime).filter(
        WeatherRealtime.city_id == current_weather_json['id'],
        WeatherRealtime.dt >= six_minutes_ago,
    ).first()
    if existing_forecast:
        print(f"✓ 城市 {current_weather_json['name']} 已存在五分钟内的天气记录，跳过插入。")
        return

    # 1. 插入或更新城市信息
    city_id = current_weather_json['id']
    city = session.query(City).filter_by(id=city_id).first()

    if not city:
        city = City(
            id=city_id,
            name=current_weather_json['name'],
            country=current_weather_json['sys']['country'],
            latitude=current_weather_json['coord']['lat'],
            longitude=current_weather_json['coord']['lon'],
            timezone=current_weather_json['timezone']
        )
        session.add(city)
    else:
        # 更新城市的时区（可能变化）
        city.timezone = current_weather_json['timezone']

    # 1.1 插入日出日落信息到SunriseSunset表
    # 相同城市一天内只插入一次日出日落信息
    dt_ordinal = datetime.now(timezone.utc).date().toordinal()
    existing_sunrise_sunset = session.query(SunriseSunset).filter_by(
        city_id=city.id,
        dt=dt_ordinal  # ← 使用序数查询
    ).first()

    if not existing_sunrise_sunset:
        sunrise_sunset = SunriseSunset(
            city_id=city.id,
            sunrise=current_weather_json['sys']['sunrise'],
            sunset=current_weather_json['sys']['sunset'],
            dt=dt_ordinal  # ← 使用序数插入
        )
        session.add(sunrise_sunset)

    # 1.2 获取或创建天气类型
    weather_type_id = None
    if current_weather_json.get('weather') and len(current_weather_json['weather']) > 0:
        weather_item = current_weather_json['weather'][0]  # 取第一个天气状况
        weather_type = session.query(WeatherType).filter_by(
            weather_id=weather_item['id'],
            main=weather_item['main'],
            icon=weather_item['icon']
        ).first()

        if not weather_type:
            weather_type = WeatherType(
                weather_id=weather_item['id'],
                main=weather_item['main'],
                description=weather_item['description'],
                icon=weather_item['icon']
            )
            session.add(weather_type)
            session.flush()  # 立即获取生成的ID

        weather_type_id = weather_type.id

    # 2. 插入实时天气数据
    current_weather = WeatherRealtime(
        city_id=city.id,
        dt=current_weather_json['dt'],
        temp=current_weather_json['main']['temp'],
        feels_like=current_weather_json['main']['feels_like'],
        temp_min=current_weather_json['main']['temp_min'],
        temp_max=current_weather_json['main']['temp_max'],
        pressure=current_weather_json['main']['pressure'],
        sea_level=current_weather_json['main'].get('sea_level'),
        grnd_level=current_weather_json['main'].get('grnd_level'),
        humidity=current_weather_json['main']['humidity'],
        clouds_all=current_weather_json['clouds']['all'],
        wind_speed=current_weather_json['wind']['speed'],
        wind_deg=current_weather_json['wind']['deg'],
        wind_gust=current_weather_json['wind'].get('gust'),
        visibility=current_weather_json['visibility'],
        base=current_weather_json['base'],
        rain_1h=current_weather_json.get('rain', {}).get('1h'),
        rain_3h=current_weather_json.get('rain', {}).get('3h'),
        snow_1h=current_weather_json.get('snow', {}).get('1h'),
        snow_3h=current_weather_json.get('snow', {}).get('3h'),
        sys_type=current_weather_json['sys'].get('type'),
        sys_id=current_weather_json['sys'].get('id'),
        sys_country=current_weather_json['sys']['country'],
        sys_sunrise=current_weather_json['sys']['sunrise'],
        sys_sunset=current_weather_json['sys']['sunset'],
        timezone=current_weather_json['timezone'],
        cod=current_weather_json['cod'],
        weather_type_id=weather_type_id
    )
    session.add(current_weather)

    # 提交事务
    session.commit()
    print(f"✓ 成功插入城市 {city.name} 的实时天气数据 (温度: {current_weather.temp}°C)")


def should_fetch_forecast():
    """判断是否需要获取天气预报（每3小时一次）"""
    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    # 将时间戳按3小时（10800秒）分段，检查是否在窗口的前5分钟内
    time_in_window = current_timestamp % (3 * 3600)  # 在当前3小时窗口内的秒数
    return time_in_window < 300  # 前5分钟（300秒）内执行


def main():
    # 每3小时获取一次天气预报数据
    if should_fetch_forecast():
        print("正在获取天气预报数据...")
        request_weather_forecast_data()

    request_current_weather_data()
    return 0

if __name__ == '__main__':
    raise SystemExit(main())