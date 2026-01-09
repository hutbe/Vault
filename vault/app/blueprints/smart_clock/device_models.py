from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, JSON, ForeignKey, Enum, create_engine, Numeric
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone
import enum

Base = declarative_base()

class DeviceType(enum.IntEnum):
    """设备类型枚举"""
    RASPBERRY_PI_PICO_W = 1
    RASPBERRY_PI = 2
    ESP32 = 3
    ESP8266 = 4
    ARDUINO = 5
    STM32 = 6
    LINUX_SERVER = 7
    WINDOWS_PC = 8
    MACOS = 9
    ANDROID = 10
    IOS = 11
    OTHER = 99

class ResetType(enum.IntEnum):
    """设备复位类型枚举"""
    PWRON_RESET = 0 # 上电复位
    WDT_RESET = 1 # 看门狗复位
    OTHER_RESET = 9

class SystemDevice(Base):
    """设备基础信息表"""
    __tablename__ = 'system_devices'

    # MySQL表配置：使用InnoDB引擎，UTF8MB4字符集
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 设备基本信息（注意：MySQL索引字段长度限制）
    unique_id = Column(String(191), unique=True, nullable=False, index=True)  # 191字符限制
    device_type = Column(Integer, nullable=False, index=True, comment='设备类型:  1=Pico W, 2=树莓派, 3=ESP32.. .')
    device_name = Column(String(191), nullable=True)
    description = Column(String(500), nullable=True)

    # 设备位置/分组
    location = Column(String(191), nullable=True)
    group_name = Column(String(100), nullable=True, index=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    last_seen = Column(DateTime, default=datetime.now(timezone.utc), nullable=False, index=True)

    # 设备状态
    is_active = Column(Integer, default=1)  # 1=活跃, 0=停用

    # 关联的快照记录
    snapshots = relationship("SystemDeviceSnapshot", back_populates="device", cascade="all, delete-orphan")

    @property
    def device_type_enum(self):
        """获取设备类型枚举对象"""
        try:
            return DeviceType(self.device_type)
        except ValueError:
            return None

    @property
    def device_type_name(self):
        """获取设备类型名称"""
        enum_obj = self.device_type_enum
        return enum_obj.name if enum_obj else "UNKNOWN"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'unique_id': self.unique_id,
            'device_type': self.device_type,
            'device_type_name': self.device_type_name,
            'device_name': self.device_name,
            'description': self.description,
            'location': self.location,
            'group_name': self.group_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f"<SystemDevice(id={self.id}, name='{self.device_name}', type='{self.device_type.value}')>"

class SystemDeviceSnapshot(Base):
    """设备状态快照表（时序数据）"""
    __tablename__ = 'system_device_snapshots'

    # MySQL表配置
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey('system_devices.id', ondelete='CASCADE', name='fk_system_device_snapshot_device'), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), nullable=False, index=True)

    # 系统信息
    platform = Column(String(100), nullable=True)
    os_version = Column(String(191), nullable=True)
    cpu_frequency_mhz = Column(Integer, nullable=True)

    # 传感器/温度
    cpu_temperature = Column(Numeric(5, 2), nullable=True)

    # 存储信息
    total_storage_bytes = Column(BigInteger, nullable=True, comment='总存储空间（字节）')
    used_storage_bytes = Column(BigInteger, nullable=True, comment='已用存储（字节）')
    free_storage_bytes = Column(BigInteger, nullable=True, comment='剩余存储（字节）')
    storage_usage_percent = Column(Float, nullable=True, comment='存储使用率（%）')

    # 内存信息 - 使用 BIGINT 存储字节数
    total_memory_bytes = Column(BigInteger, nullable=True, comment='总内存（字节）')
    used_memory_bytes = Column(BigInteger, nullable=True, comment='已用内存（字节）')
    free_memory_bytes = Column(BigInteger, nullable=True, comment='剩余内存（字节）')
    memory_usage_percent = Column(Float, nullable=True, comment='内存使用率（%）')

    # 电源/运行时间
    uptime_seconds = Column(BigInteger, nullable=True)
    reset_reason = Column(Integer, nullable=False, index=True, comment='设备类型:  0=上电复位, 1=看门狗复位....')
    battery_level_percent = Column(Float, nullable=True)

    # 网络信息
    ip = Column(String(45), nullable=True)  # IPv6最长45字符
    mac = Column(String(17), nullable=True, index=True)
    subnet = Column(String(45), nullable=True, index=True)
    dns = Column(String(45), nullable=True, index=True)
    gateway = Column(String(45), nullable=True, index=True)

    rssi = Column(Integer, nullable=True)

    # 扩展字段（MySQL 5.7.8+ 支持JSON类型）
    extra_data = Column(JSON, nullable=True)

    # 关联设备
    device = relationship("SystemDevice", back_populates="snapshots")

    @property
    def reset_reason_enum(self):
        try:
            return ResetType(self.reset_reason)
        except ValueError:
            return None

    @property
    def reset_reason_name(self):
        enum_obj = self.reset_reason_enum
        return enum_obj.name if enum_obj else "UNKNOWN"

    def __repr__(self):
        return f"<SystemDeviceSnapshot(id={self.id}, device_id={self.device_id}, timestamp='{self.timestamp}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'platform': self.platform,
            'os_version': self.os_version,
            'cpu_frequency_mhz': self.cpu_frequency_mhz,
            'cpu_temperature': self.cpu_temperature,
            'total_storage_bytes': self.total_storage_bytes,
            'used_storage_bytes': self.used_storage_bytes,
            'free_storage_bytes': self.free_storage_bytes,
            'storage_usage_percent': self.storage_usage_percent,
            'total_memory_bytes': self.total_memory_bytes,
            'used_memory_bytes': self.used_memory_bytes,
            'free_memory_bytes': self.free_memory_bytes,
            'memory_usage_percent': self.memory_usage_percent,
            'uptime_seconds': self.uptime_seconds,
            'reset_reason': self.reset_reason,
            'reset_reason_name': self.reset_reason_name,
            'battery_level_percent': self.battery_level_percent,
            'ip': self.ip,
            'mac': self.mac,
            'subnet': self.subnet,
            'dns': self.dns,
            'gateway': self.gateway,
            'rssi': self.rssi,
            'extra_data': self.extra_data
        }

# 使用示例
if __name__ == '__main__':
    # MySQL 数据库连接配置
    # 方式1: 使用 pymysql（纯Python实现）
    # pip install pymysql
    DB_CONFIG = {
        'host': 'xxxxxx',
        'port': 3306,
        'user': 'root',
        'password': 'xxxxx',
        'database': 'xxxxxx',
        'charset': 'utf8mb4'
    }

    # 创建连接字符串
    connection_string = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        f"?charset={DB_CONFIG['charset']}"
    )

    # 方式2: 使用 mysqlclient（更快但需要编译）
    # pip install mysqlclient
    # connection_string = (
    #     f"mysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    #     f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    #     f"?charset={DB_CONFIG['charset']}"
    # )

    # 创建数据库引擎
    engine = create_engine(
        connection_string,
        echo=True,  # 开发时可以看到SQL语句
        pool_size=10,  # 连接池大小
        pool_recycle=3600,  # 连接回收时间（秒）
        pool_pre_ping=True,  # 使用前检查连接是否有效
        connect_args={
            'connect_timeout': 10  # 连接超时时间
        }
    )

    # 创建所有表
    Base.metadata.create_all(engine)

    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 添加 Raspberry Pi Pico W 设备
        pico_device = SystemDevice(
            unique_id='e6632c8593745230',
            device_type=0,
            device_name='Raspberry Pi Pico W',
            description='温度监控节点',
            location='实验室A',
            group_name='物联网传感器'
        )
        session.add(pico_device)
        session.commit()

        # 添加快照数据
        # pico_snapshot = SystemDeviceSnapshot(
        #     device_id=pico_device.id,
        #     platform='rp2',
        #     os_version='MicroPython v1.23. 0 on 2024-06-02',
        #     cpu_frequency_mhz=125,
        #     cpu_temperature=28.45,
        #     total_storage_bytes=84800,
        #     used_storage_bytes=32133,
        #     free_storage_bytes = 66800,
        #     storage_usage_percent = 21.2,
        #     total_memory_bytes = 191424,
        #     used_memory_bytes = 43808,
        #     free_memory_bytes = 147616,
        #     memory_usage_percent = 22.9,
        #     uptime_seconds = 11414,
        #     reset_reason = 0,
        #     extra_data = {
        #         'micropython_version': '3.4.0',
        #         'board': 'Raspberry Pi Pico W'
        #     }
        # )
        # session.add(pico_snapshot)
        # session.commit()

        # 查询示例
        print("\n=== 所有设备 ===")
        devices = session.query(SystemDevice).all()
        for device in devices:
            print(f"{device.device_name} ({device.device_type_name}) - 最后在线: {device.last_seen}")

        print("\n=== Pico W 的所有快照 ===")
        pico_snapshots = session.query(SystemDeviceSnapshot).filter_by(device_id=pico_device.id).all()
        for snapshot in pico_snapshots:
            print(
                f"时间: {snapshot.timestamp}, CPU温度:  {snapshot.cpu_temperature}°C, 内存使用:  {snapshot.memory_usage_percent}%")

    except Exception as e:
        print(f"错误: {e}")
        session.rollback()
    finally:
        session.close()