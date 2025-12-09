
传感器数据
sensor/dht22/1/data
sensor/dht22/2/data
sensor/dht22/10/data

device id:

`specific`          : 0
`livingroom`        : 1
`fridge`            : 2
`ffice`             : 10

笔记
note/0/home
note/${user_id}/home/

note id:

`notification`      : 0
`user_id`           : 2

信息
message/home

`sensor/dht22/+/data`: 订阅所有的dht22传感器数据
`note/+/home`: 订阅所有的hom笔记

note/${user_id}/home/
chat/user/${user_id}/inbox
chat/group/${group_id}/inbox
chat/notification


home/sensor/livingroom/data          # 完整JSON数据
home/sensor/livingroom/temperature   # 仅温度值（可选）
home/sensor/livingroom/humidity      # 仅湿度值（可选）

home/sensor/livingroom/data          # 完整JSON数据
home/sensor/livingroom/temperature   # 仅温度值（可选）
home/sensor/livingroom/humidity      # 仅湿度值（可选）

home/screen/livingroom/stata


{
  "temperature": 23.5,
  "humidity": 65.2,
  "timestamp": "2025-12-06T02:30:00Z"  // UTC时间
}


## MQTT 主题通配符（MQTT Wildcards）

### 单层通配符

加号 (“+” U+002B) 是用于单个主题层级匹配的通配符。在使用单层通配符时，单层通配符必须占据整个层级，例如：

`home/sensor/+/temperature`

加号 (“+” U+002B) 是用于单个主题层级匹配的通配符。在使用单层通配符时，单层通配符必须占据整个层级，例如：

```
+ 有效
sensor/+ 有效
sensor/+/temperature 有效
sensor+ 无效（没有占据整个层级）

```

如果客户端订阅了主题 sensor/+/temperature，将会收到以下主题的消息：

```
sensor/1/temperature
sensor/2/temperature
...
sensor/n/temperature
```

但是不会匹配以下主题：

```
sensor/temperature
sensor/bedroom/1/temperature
```

### 多层通配符

井字符号（“#” U+0023）是用于匹配主题中任意层级的通配符。多层通配符表示它的父级和任意数量的子层级，在使用多层通配符时，它必须占据整个层级并且必须是主题的最后一个字符，例如：

```
# 有效，匹配所有主题
sensor/# 有效
sensor/bedroom# 无效（没有占据整个层级）
sensor/#/temperature 无效（不是主题最后一个字符）
```

如果客户端订阅主题 senser/#，它将会收到以下主题的消息：

```
sensor
sensor/temperature
sensor/1/temperature
```

### 以 $ 开头的主题

系统主题


chat/user/${user_id}/inbox
chat/group/${group_id}/inbox
req/user/${user_id}/add
resp/user/${user_id}/add
user/${user_id}/state

sensor/2/temperature
sensor/bedroom/1/temperature
myhome/kitchen/humidity

* 不建议使用 # 订阅所有主题；
不建议主题以 / 开头或结尾，例如 /chat 或 chat/；
不建议在主题里添加空格及非 ASCII 特殊字符；
同一主题层级内建议使用下划线 _ 或横杆 - 连接单词（或者使用驼峰命名）；
尽量使用较少的主题层级；
当使用通配符时，将唯一值的主题层（例如设备号）越靠近第一层越好。例如，device/00000001/command/# 比device/command/00000001/# 更好。
