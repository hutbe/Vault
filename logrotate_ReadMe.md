## 日志轮转工具 logrotate



# 创建非 root 用户

Swift MQTT 服务的Docker容器中创建了一个mqtt_client用户:
`RUN useradd -u 1100 -m -s /bin/bash mqtt_client`

在 Linux 系统中创建一个 UID 为 1100 的用户 mqtt_client 让系统有权限通过logrotate操作mqtt_client服务挂的日志目录`mqtt_client/logs`:

`sudo useradd -u 1100 -m -s /bin/bash mqtt_client`



文件`logrotate_vault_mqtt_client`和`logrotate_vault_mosquitto`为日志转轮工具的配置文件，将这两个文件放置到目录`/etc/logrotate.d/`下

logrotate 是 Linux 系统中用于自动轮转、压缩、删除和邮寄日志文件的工具。它通常由系统的 cron 任务每天执行一次（例如 /etc/cron.daily/logrotate），从而防止日志文件无限增大，耗尽磁盘空间，同时保留历史日志以备查询。

logrotate 本身是一个命令行工具，由 cron 定期调用。执行流程：

**工作原理:**

1. 读取主配置文件 /etc/logrotate.conf
2. 读取 /etc/logrotate.d/ 目录下的所有配置文件 
3. 对每个配置段检查日志文件是否需要轮转（基于时间、大小等条件）
4. 若需要，则执行轮转操作：重命名旧文件、压缩、创建新文件、执行 postrotate 脚本等
5. 更新状态文件 /var/lib/logrotate/status，记录最后一次轮转时间

在正式运行前，可以用调试模式测试（不会实际轮转）：
`sudo logrotate -d /etc/logrotate.conf`

或者只测试某个配置文件：
`sudo logrotate -d /etc/logrotate.d/logrotate_vault_mosquitto`

手动强制轮转
`sudo logrotate -f /etc/logrotate.d/myapp`

加上 -v 可以获得详细输出：
`sudo logrotate -fv /etc/logrotate.d/myapp`

**查看轮转状态:**

logrotate 将每个日志的最后轮转时间记录在 `/var/lib/logrotate/status` 中。可以查看该文件确认状态，或使用：

`sudo logrotate -v /etc/logrotate.d/myapp`
会显示“上次轮转时间”等信息。