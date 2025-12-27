from datetime import datetime
from sqlalchemy import Column, Integer, BIGINT, String, Float, Text, Numeric, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship
from typing import Dict, Any

# 创建基类
Base = declarative_base()


class MqttMessage(Base):
    __tablename__ = 'mqtt_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(255), nullable=False, index=True)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, comment='记录接收时间')

    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'payload': self.payload,
            'created_at': self.create_date.isoformat() if self.create_date else None,
        }
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}
    )

class SensorDHT22(Base):
    __tablename__ = 'sensor_dht22'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(Integer, nullable=False)
    temperature = Column(Numeric(5, 2), comment='温度(°C)')
    humidity = Column(Numeric(5, 2), comment='湿度')
    created_at = Column(DateTime, nullable=False)
    created_at_iso = Column(String(33), nullable=False)
    received_at = Column(DateTime, default=datetime.now, comment='记录接收时间')

    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Note(Base):
    __tablename__ = 'note'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(Text, nullable=False)
    received_at = Column(DateTime, default=datetime.now, comment='记录接收时间')




class HomeClimate(Base):
    """环境信息表 - 对应 surroundings 表"""
    __tablename__ = 'home_climate'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(50))
    temperature = Column(Float)
    humidity = Column(Float)
    cup_temp = Column(Float)
    cpu_used_rate = Column(Float)
    sys_uptime = Column(String(50))
    sys_runtime = Column(Integer)
    weather = Column(String(50))
    weather_code = Column(Integer)
    weather_des = Column(String(50))
    weather_icon = Column(String(10))
    outdoors_temp = Column(Float)
    outdoors_feels_like = Column(Float)
    outdoors_temp_min = Column(Float)
    outdoors_temp_max = Column(Float)
    outdoors_pressure = Column(Float)
    outdoors_humidity = Column(Float)
    create_date = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'cup_temp': self.cup_temp,
            'cpu_used_rate': self.cpu_used_rate,
            'sys_uptime': self.sys_uptime,
            'sys_runtime': self.sys_runtime,
            'weather': self.weather,
            'weather_code': self.weather_code,
            'weather_des': self.weather_des,
            'weather_icon': self.weather_icon,
            'outdoors_temp': self.outdoors_temp,
            'outdoors_feels_like': self.outdoors_feels_like,
            'outdoors_temp_min': self.outdoors_temp_min,
            'outdoors_temp_max': self.outdoors_temp_max,
            'outdoors_pressure': self.outdoors_pressure,
            'outdoors_humidity': self.outdoors_humidity,
            'create_date': self.create_date.isoformat() if self.create_date else None,
        }

class AirConditioner(Base):
    """空调表 - 对应 airconditioner 表"""
    __tablename__ = 'airconditioner'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(50))
    temperature = Column(Float)
    model = Column(Integer)
    description = Column(String(50))
    create_date = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'temperature': self.temperature,
            'model': self.model,
            'description': self.description,
            'create_date': self.create_date.isoformat() if self.create_date else None,
        }


class HomePod(Base):
    """HomePod 表 对应 homepod.db 中的 sensor 表"""
    __tablename__ = 'homepod_sensor'

    id = Column(Integer, primary_key=True, autoincrement=True)
    temperature = Column(Float)
    humidity = Column(Float)
    create_date = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'create_date': self.create_date.isoformat() if self.create_date else None,
        }

class ScreenLog(Base):
    """屏幕日志表"""
    __tablename__ = 'screen_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(Boolean)
    create_date = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'create_date': self.create_date.isoformat() if self.create_date else None,
        }

class Fridge(Base):
    """冰箱表"""
    __tablename__ = 'fridge'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag = Column(String(50))
    temperature = Column(Float)
    humidity = Column(Float)
    create_date = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'tag': self.tag,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'create_date': self.create_date.isoformat() if self.create_date else None,
        }


def main():
    from sqlalchemy import create_engine
    # Create engine for MariaDB
    engine = create_engine('mysql+pymysql://hut:hut123456@127.0.0.1:3306/home_db')

    # Create all tables
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    raise SystemExit(main())