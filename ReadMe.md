* `docker compose up`
* `docker compose up -d`
* `docker compose down`
* `mariadb -h 127.0.0.1 -P 3306 -u root -p`
* `docker exec -it mariadb-server bash`

待做

- 1. 是否添加 Content-Security-Policy (CSP) 取决于你的具体需求和风险承受能力。
  * nginx中的security.conf配置
- 2. UID 和 GID 是 Linux/Unix 系统中用户和组身份的核心标识符。
    * docker与系统UID/GID的关系
- 3. 配置 跨域资源共享（Cross-origin resource sharing)
- 4. Strict-Transport-Security header

在使用Docker部署MariaDB时，通过挂载这三个文件夹是业界最佳实践，可以实现数据持久化、配置自定义和初始化自动化。下面详细解释这三个文件夹的作用：

## 1. `~/mariadb/data` - 数据目录

**作用：存储数据库的实际数据文件**

这是**最重要**的挂载目录，用于数据持久化。

- **包含内容：**
  - 数据库表结构和数据文件（.frm, .ibd文件）
  - 系统表（mysql、information_schema等）
  - 二进制日志（binlog）
  - 事务日志（redo/undo logs）
  - 用户账户和权限信息

- **为什么需要挂载：**
  - 如果容器被删除，这个目录中的数据会保留
  - 方便备份和恢复（直接备份这个文件夹）
  - 支持容器迁移（在新容器中挂载相同的数据目录）

- **如果没有挂载：**
  - 数据将存储在容器内部，容器删除后所有数据丢失
  - 无法进行有效的数据管理

## 2. `~/mariadb/config` - 配置目录

**作用：存放MariaDB的自定义配置文件**

- **包含内容：**
  - `my.cnf` 或 `*.cnf` 配置文件
  - 自定义字符集、时区、缓冲池大小等设置
  - 性能调优参数
  - 安全相关配置

- **典型配置文件示例：**

```ini
# ~/mariadb/config/my.cnf
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
default-time-zone = '+08:00'
innodb_buffer_pool_size = 1G
max_connections = 200

[client]
default-character-set = utf8mb4
```

- **为什么需要挂载：**
  - 覆盖默认配置，适应特定需求
  - 便于版本控制和配置管理
  - 无需重新构建镜像即可修改配置

## 3. `~/mariadb/initdb` - 初始化脚本目录

**作用：存放数据库首次启动时执行的初始化脚本**

- **包含内容：**
  - `.sql` 文件：SQL脚本
  - `.sh` 文件：Shell脚本
  - 按文件名顺序执行（字母顺序）

- **典型用途：**
  - 创建业务数据库和用户
  - 初始化表结构和基础数据
  - 设置存储过程、函数、触发器
  - 导入初始数据

- **示例初始化脚本：**

```sql
-- ~/mariadb/initdb/01-create-databases.sql
CREATE DATABASE IF NOT EXISTS myapp;
CREATE USER 'appuser'@'%' IDENTIFIED BY 'securepassword';
GRANT ALL PRIVILEGES ON myapp.* TO 'appuser'@'%';

-- ~/mariadb/initdb/02-create-tables.sql
USE myapp;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);
```

## 完整的Docker运行示例

```bash
# 创建目录结构
mkdir -p ~/mariadb/{data,config,initdb}

# 创建自定义配置文件
cat > ~/mariadb/config/my.cnf << EOF
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
default-time-zone = '+08:00'

[client]
default-character-set = utf8mb4
EOF

# 创建初始化脚本
cat > ~/mariadb/initdb/01-init.sql << EOF
CREATE DATABASE IF NOT EXISTS myapp;
CREATE USER 'appuser'@'%' IDENTIFIED BY 'mypassword';
GRANT ALL PRIVILEGES ON myapp.* TO 'appuser'@'%';
FLUSH PRIVILEGES;
EOF

# 运行容器
docker run -d \
  --name mariadb \
  -p 3306:3306 \
  -v ~/mariadb/data:/var/lib/mysql \
  -v ~/mariadb/config:/etc/mysql/conf.d \
  -v ~/mariadb/initdb:/docker-entrypoint-initdb.d \
  -e MYSQL_ROOT_PASSWORD=myrootpassword \
  mariadb:latest
```

## 工作流程总结

1. **首次启动时：**
   - 检查 `/var/lib/mysql` 是否为空
   - 如果为空，初始化系统数据库
   - 执行 `/docker-entrypoint-initdb.d/` 下的所有脚本
   - 启动MariaDB服务

2. **后续启动时：**
   - 检测到数据目录已有数据，跳过初始化
   - 直接启动服务，保留所有数据

3. **配置加载：**
   - 容器启动时自动加载 `/etc/mysql/conf.d/` 下的配置文件

这种三目录分离的设计确保了数据安全、配置灵活和部署自动化，是生产环境部署的推荐做法。


## 日志轮转工具 logrotate

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

logrotate 将每个日志的最后轮转时间记录在 /var/lib/logrotate/status 中。可以查看该文件确认状态，或使用：

`sudo logrotate -v /etc/logrotate.d/myapp`
会显示“上次轮转时间”等信息。