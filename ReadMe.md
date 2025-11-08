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