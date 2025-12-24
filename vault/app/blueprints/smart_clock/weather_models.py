from sqlalchemy import create_engine, Column, Integer,BigInteger, Float, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

# 创建基类
Base = declarative_base()

class SunriseSunset(Base):
    """城市日出日落信息表 - 只由实时天气数据接口填充"""
    # https://api.openweathermap.org/data/2.5/weather?lat=22.63404&lon=113.81842&appid=your_code&lang=zh
    # [实时天气信息 - 接口说明文档](https: // openweathermap.org / current)
    __tablename__ = 'weather_sunrise_sunset'
    id = Column(Integer, primary_key=True,  autoincrement=True, comment='ID')
    city_id = Column(Integer, ForeignKey('weather_cities.id', ondelete='CASCADE'),
                     nullable=False, index=True, comment='城市ID外键')
    sunrise = Column(Integer, comment='日出时间戳')
    sunset = Column(Integer, comment='日落时间戳')

    # 时间信息
    dt = Column(BigInteger, nullable=False, index=True, comment='数据计算时间戳')
    created_at = Column(DateTime, default=datetime.now, comment='记录创建时间')

    """
    # 方式1: 定义单向关系使用 lazy='joined' 总是预加载
    测试数据量：小数据（<1000行）joined可能更快
    大数据集：优先selectin（避免JOIN膨胀）
    """
    # 定义正向关系
    city = relationship('City', back_populates='sunrise_sunset_records', lazy='joined')

    # 添加唯一约束，防止同一城市同一时间重复记录
    __table_args__ = (
        Index('idx_city_dt', 'city_id', 'dt', unique=True),
    )


class City(Base):
    """城市信息表 - 只由实时天气数据接口填充"""
    # https://api.openweathermap.org/data/2.5/forecast?lat=22.63404&lon=113.81842&appid=your_code&cnt=40&lang=zh
    # [5天内，每3个小时的预报 - 接口说明文档](https: // openweathermap.org / forecast5)
    __tablename__ = 'weather_cities'

    id = Column(Integer, primary_key=True, comment='城市ID')
    name = Column(String(100), nullable=False, comment='城市名称')
    country = Column(String(10), comment='国家代码')
    latitude = Column(Float, comment='纬度')
    longitude = Column(Float, comment='经度')
    population = Column(Integer, comment='人口')
    timezone = Column(Integer, comment='时区偏移(秒)')

    # 定义反向关系：一个城市可以有多条历史日出日落记录
    sunrise_sunset_records = relationship(
        'SunriseSunset',
        back_populates='city',
        lazy='noload', # 'selectin'用于大数据集查询 dynamic 适合偶尔需要查询, noload 访问时返回空列表 []，不会触发数据库查询 需要时可以手动查询
        order_by='desc(SunriseSunset.dt)',  # 按时间倒序
        cascade='all, delete-orphan'  # 删除城市时级联删除记录
    )

    # 关系：一个城市有多条天气预报
    forecasts = relationship('WeatherForecast', back_populates='city', cascade='all, delete-orphan')
    # 关系：一个城市有多条实时天气记录
    weather_realtime = relationship('WeatherRealtime', back_populates='city', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<City(id={self.id}, name='{self.name}', country='{self.country}')>"


class WeatherRealtime(Base):
    """实时天气数据表"""
    __tablename__ = 'weather_realtime'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    city_id = Column(Integer, ForeignKey('weather_cities.id', ondelete='CASCADE'),
                     nullable=False, index=True, comment='城市ID外键')

    # 时间信息
    dt = Column(BigInteger, nullable=False, index=True, comment='数据计算时间戳')
    created_at = Column(DateTime, default=datetime.now, comment='记录创建时间')

    # 主要天气数据
    temp = Column(Float, comment='温度(K)')
    feels_like = Column(Float, comment='体感温度(K)')
    temp_min = Column(Float, comment='最低温度(K)')
    temp_max = Column(Float, comment='最高温度(K)')
    pressure = Column(Integer, comment='气压(hPa)')
    sea_level = Column(Integer, comment='海平面气压(hPa)')
    grnd_level = Column(Integer, comment='地面气压(hPa)')
    humidity = Column(Integer, comment='湿度(%)')

    # 云量信息
    clouds_all = Column(Integer, comment='云量(%)')

    # 风力信息
    wind_speed = Column(Float, comment='风速(m/s)')
    wind_deg = Column(Integer, comment='风向(度)')
    wind_gust = Column(Float, comment='阵风速度(m/s)')

    # 其他信息
    visibility = Column(Integer, comment='能见度(米)')
    base = Column(String(50), comment='数据来源基站')

    # 降雨/降雪信息(可选)
    rain_1h = Column(Float, comment='过去1小时降雨量(mm)')
    rain_3h = Column(Float, comment='过去3小时降雨量(mm)')
    snow_1h = Column(Float, comment='过去1小时降雪量(mm)')
    snow_3h = Column(Float, comment='过去3小时降雪量(mm)')

    # 系统信息
    sys_type = Column(Integer, comment='系统类型')
    sys_id = Column(Integer, comment='系统ID')
    sys_country = Column(String(10), comment='国家代码')
    sys_sunrise = Column(Integer, comment='日出时间戳')
    sys_sunset = Column(Integer, comment='日落时间戳')

    # 城市信息补充
    timezone = Column(Integer, comment='时区偏移(秒)')
    cod = Column(Integer, comment='响应代码')

    weather_type_id = Column(Integer, ForeignKey('weather_types.id'), comment='天气状况ID外键')

    # 关系
    city = relationship('City', back_populates='weather_realtime')
    weather_type = relationship('WeatherType', lazy='joined')

    def __repr__(self):
        return f"<WeatherRealtime(id={self.id}, city_id={self.city_id}, dt={self.dt}, temp={self.temp})>"


class WeatherForecast(Base):
    """天气预报主表"""
    __tablename__ = 'weather_forecasts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    city_id = Column(Integer, ForeignKey('weather_cities.id', ondelete='CASCADE'),
                     nullable=False, index=True, comment='城市ID外键')

    # 时间信息
    forecast_dt = Column(BigInteger, nullable=False, index=True, comment='记录预报时间')
    forecast_dt_txt = Column(String(50), comment='记录预报时间文本')

    dt = Column(BigInteger, nullable=False, index=True, comment='预报时间戳')
    dt_txt = Column(String(50), comment='预报时间文本')

    # 主要天气数据
    temp = Column(Float, comment='温度(K)')
    feels_like = Column(Float, comment='体感温度(K)')
    temp_min = Column(Float, comment='最低温度(K)')
    temp_max = Column(Float, comment='最高温度(K)')
    pressure = Column(Integer, comment='气压(hPa)')
    sea_level = Column(Integer, comment='海平面气压(hPa)')
    grnd_level = Column(Integer, comment='地面气压(hPa)')
    humidity = Column(Integer, comment='湿度(%)')
    temp_kf = Column(Float, comment='温度校正系数')

    # 云量信息
    clouds_all = Column(Integer, comment='云量(%)')

    # 风力信息
    wind_speed = Column(Float, comment='风速(m/s)')
    wind_deg = Column(Integer, comment='风向(度)')
    wind_gust = Column(Float, comment='阵风速度(m/s)')

    # 其他信息
    visibility = Column(Integer, comment='能见度(米)')
    pop = Column(Float, comment='降水概率(0-1)')
    sys_pod = Column(String(10), comment='白天/夜晚标识(d/n)')

    # 降雨/降雪信息(可选)
    rain_3h = Column(Float, comment='过去3小时降雨量(mm)')
    snow_3h = Column(Float, comment='过去3小时降雪量(mm)')
    weather_type_id = Column(Integer, ForeignKey('weather_types.id'), comment='天气状况ID外键')

    # 关系
    city = relationship('City', back_populates='forecasts')
    weather_type = relationship('WeatherType', lazy='joined')

    def __repr__(self):
        return f"<WeatherForecast(id={self.id}, city_id={self.city_id}, dt={self.dt}, temp={self.temp})>"


class WeatherType(Base):
    """天气状况详情表（通用，支持预报和实时天气）"""
    __tablename__ = 'weather_types'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    weather_id = Column(Integer, comment='天气状况ID')
    main = Column(String(50), comment='天气主要状况')
    description = Column(String(200), comment='天气描述')
    icon = Column(String(10), comment='天气图标代码')

    def __repr__(self):
        return f"<WeatherType(id={self.id}, main='{self.main}', description='{self.description}')>"

def insert_weather_data(session, weather_json):
    """
    将天气预报JSON数据插入数据库

    Args:
        session: SQLAlchemy会话对象
        weather_json: 天气预报API返回的JSON数据
    """
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
    for forecast_item in weather_json['list']:
        # 检查是否已存在相同的预报记录
        existing_forecast = session.query(WeatherForecast).filter_by(
            city_id=city.id,
            dt=forecast_item['dt']
        ).first()

        if existing_forecast:
            continue  # 跳过已存在的记录

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
    dt_value = current_weather_json['dt']
    existing_sunrise_sunset = session.query(SunriseSunset).filter_by(
        city_id=city.id,
        dt=dt_value
    ).first()

    if not existing_sunrise_sunset:
        sunrise_sunset = SunriseSunset(
            city_id=city.id,
            sunrise=current_weather_json['sys']['sunrise'],
            sunset=current_weather_json['sys']['sunset'],
            dt=dt_value
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
    print(f"✓ 成功插入城市 {city.name} 的实时天气数据 (温度: {current_weather.temp - 273.15:.1f}°C)")


def main():
    from sqlalchemy import create_engine
    # Create engine for MariaDB
    engine = create_engine('mysql+pymysql://root:xxxx@xxxx.local:3306/home_db')

    # 示例使用
    print("创建数据库和表结构...")

    # Create all tables
    Base.metadata.create_all(engine)

    print("\n数据库表创建成功！")
    print("表结构：")
    print("1. weather_cities - 城市信息表")
    print("2. weather_sunrise_sunset - 日出日落信息表")
    print("3. weather_forecasts - 天气预报主表")
    print("4. weather_realtime - 实时天气主表")
    print("5. weather_conditions - 天气状况详情表（统一）")

if __name__ == '__main__':
    raise SystemExit(main())
