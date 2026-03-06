from datetime import datetime, timezone

from zoneinfo import ZoneInfo

# Python 3.9 及以上版本可用
created_at1 = datetime.now(ZoneInfo("Asia/Shanghai"))

created_at2 = datetime.now(timezone.utc)

print(created_at1)
print(created_at2)