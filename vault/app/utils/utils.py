from datetime import datetime
from typing import Optional, Union
import re
from loguru import logger

def is_date_format_valid(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        return True
    except ValueError:
        return False

def is_valid_utc_time(time_string: str) -> bool:
    """
    判断字符串是否为合法的UTC时间格式

    Args:
        time_string: 待验证的时间字符串

    Returns:
        bool: 如果是合法的UTC时间格式返回True，否则返回False
    """
    utc_formats = [
        '%Y-%m-%dT%H:%M:%SZ',  # 2024-01-05T12:30:45Z
        '%Y-%m-%dT%H:%M:%S.%fZ',  # 2024-01-05T12:30:45.123456Z
        '%Y-%m-%d %H:%M:%S',  # 2024-01-05 12:30:45
        '%Y-%m-%d %H:%M:%S.%f',  # 2024-01-05 12:30:45.123456
        '%Y-%m-%dT%H:%M:%S',  # 2024-01-05T12:30:45
        '%Y-%m-%dT%H:%M:%S.%f',  # 2024-01-05T12:30:45.123456
        '%Y-%m-%d',  # 2024-01-05
    ]

    for fmt in utc_formats:
        try:
            datetime.strptime(time_string, fmt)
            return True
        except ValueError:
            continue

    # 处理带时区偏移的ISO 8601格式 (例如:  2024-01-05T12:30:45+00:00)
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?([+-]\d{2}:\d{2}|Z)?$'
    if re.match(iso_pattern, time_string):
        try:
            datetime.fromisoformat(time_string.replace('Z', '+00:00'))
            return True
        except ValueError:
            pass

    return False


def parse_utc_time(time_string: str) -> Optional[datetime]:
    """
    将UTC时间字符串转换为datetime对象

    Args:
        time_string: UTC时间字符串

    Returns:
        datetime对象，如果解析失败返回None
    """
    utc_formats = [
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d',
    ]

    # 尝试标准格式
    for fmt in utc_formats:
        try:
            return datetime.strptime(time_string, fmt)
        except ValueError:
            continue

    # 尝试ISO 8601格式
    try:
        return datetime.fromisoformat(time_string.replace('Z', '+00:00'))
    except ValueError:
        pass

    return None


def validate_and_parse_utc(time_string: str) -> Union[datetime, None]:
    """
    验证并解析UTC时间字符串的组合函数

    Args:
        time_string: 待验证和解析的时间字符串

    Returns:
        datetime对象，如果不是合法的UTC时间格式返回None
    """
    if is_valid_utc_time(time_string):
        return parse_utc_time(time_string)
    return None


# 使用示例
if __name__ == "__main__":
    test_strings = [
        "2024-01-05T12:30:45Z",
        "2024-01-05T12:30:45.123456Z",
        "2024-01-05 12:30:45",
        "2024-01-05",
        "2024-01-05T12:30:45+00:00",
        "2026-01-05T17:14:51+08:00",
        "invalid-date",
        "2024-13-45",  # 无效的月份和日期
    ]

    print("测试UTC时间字符串验证和转换：\n")
    for test_str in test_strings:
        is_valid = is_valid_utc_time(test_str)
        parsed_time = parse_utc_time(test_str)

        print(f"字符串: {test_str}")
        print(f"  是否合法: {is_valid}")
        print(f"  解析结果: {parsed_time}")
        print(f"  类型: {type(parsed_time)}")
        print()