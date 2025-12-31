from sqlalchemy import create_engine, Column, Integer,BigInteger, Float, String, DateTime, ForeignKey, Text, Index, Numeric
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime, timezone

# 创建基类
Base = declarative_base()

class SunriseSunset(Base):
    """城市日出日落信息表 - 只由实时天气数据接口填充"""
    # https://api.openweathermap.org/data/2.5/weather?lat=22.63404&lon=113.81842&appid=your_code&lang=zh
    # [实时天气信息 - 接口说明文档](https: // openweathermap.org / current)
    __tablename__ = 'weather_sunrise_sunset'
    id = Column(Integer, primary_key=True,  autoincrement=True, comment='ID')
    city_id = Column(Integer, ForeignKey('weather_cities.id', ondelete='CASCADE', name='fk_weather_sunrise_sunset_city'),
                     nullable=False, index=True, comment='城市ID外键')
    sunrise = Column(Integer, comment='日出时间戳')
    sunset = Column(Integer, comment='日落时间戳')

    # 时间信息
    dt = Column(BigInteger, nullable=False, index=True, comment='数据计算时间戳')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment='记录创建时间')

    """
    # 方式1: 定义单向关系使用 lazy='joined' 总是预加载
    测试数据量：小数据（<1000行）joined可能更快
    大数据集：优先selectin（避免JOIN膨胀）
    """
    # 定义正向关系
    city = relationship('City', back_populates='sunrise_sunset_records', lazy='joined')

    # 添加唯一约束，防止同一城市同一时间重复记录
    __table_args__ = (
        Index('city_id', 'dt', unique=True),
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

    # 时间信息
    dt = Column(BigInteger, nullable=False, index=True, comment='数据计算时间戳')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment='记录创建时间')

    # 主要天气数据
    temp = Column(Numeric(5, 2), comment='温度(°C)')
    feels_like = Column(Numeric(5, 2), comment='体感温度(°C)')
    temp_min = Column(Numeric(5, 2), comment='最低温度(°C)')
    temp_max = Column(Numeric(5, 2), comment='最高温度(°C)')
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

    city_id = Column(
        Integer, 
        ForeignKey('weather_cities.id', ondelete='CASCADE', name='fk_weather_realtime_city'),
        nullable=False, 
        index=True, 
        comment='城市ID外键'
    )
    
    weather_type_id = Column(
        Integer, 
        ForeignKey('weather_types.id', name='fk_weather_realtime_weather_type'), 
        comment='天气状况ID外键'
    )

    # 关系
    city = relationship('City', back_populates='weather_realtime')
    weather_type = relationship('WeatherType', lazy='joined')

    def __repr__(self):
        return f"<WeatherRealtime(id={self.id}, city_id={self.city_id}, dt={self.dt}, temp={self.temp})>"


class WeatherForecast(Base):
    """天气预报主表"""
    __tablename__ = 'weather_forecasts'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 时间信息
    forecast_dt = Column(BigInteger, nullable=False, index=True, comment='记录预报时间')
    forecast_dt_txt = Column(String(50), comment='记录预报时间文本')

    dt = Column(BigInteger, nullable=False, index=True, comment='预报时间戳')
    dt_txt = Column(String(50), comment='预报时间文本')

    # 主要天气数据
    temp = Column(Numeric(5, 2), comment='温度(°C)')
    feels_like = Column(Numeric(5, 2), comment='体感温度(°C)')
    temp_min = Column(Numeric(5, 2), comment='最低温度(°C)')
    temp_max = Column(Numeric(5, 2), comment='最高温度(°C)')
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

    city_id = Column(
        Integer, 
        ForeignKey('weather_cities.id', ondelete='CASCADE', name='fk_weather_forecast_city'),
        nullable=False, 
        index=True, 
        comment='城市ID外键'
    )
    
    weather_type_id = Column(
        Integer, 
        ForeignKey('weather_types.id', name='fk_weather_forecast_weather_type'), 
        comment='天气状况ID外键'
    )

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

def main():
    from sqlalchemy import create_engine
    # Create engine for MariaDB
    engine = create_engine('mysql+pymysql://root:xxxxxx@127.0.0.1:3306/home_db')

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
