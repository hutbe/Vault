






## nginx自动处理环境变量的限制

### 1. 只处理特定目录的模板文件

nginx官方镜像(1.19+)只会自动处理 `/etc/nginx/templates/` 目录下以 `.template` 结尾的文件：

```bash
# nginx自动处理（有限制）
/etc/nginx/templates/nginx.conf.template  ✅ 会被自动处理
/etc/nginx/templates/default.conf.template  ✅ 会被自动处理

# 这些不会被自动处理
/etc/nginx/nginx.conf.template  ❌ 不会被处理
/tmp/custom.conf.template  ❌ 不会被处理
/app/config/app.conf.template  ❌ 不会被处理
```

### 2. 输出路径固定

nginx自动处理时，输出文件路径是固定的：
- `/etc/nginx/templates/nginx.conf.template` → `/etc/nginx/nginx.conf`
- `/etc/nginx/templates/conf.d/default.conf.template` → `/etc/nginx/conf.d/default.conf`

如果你需要自定义输出路径，就必须手动使用`envsubst`。

### 3. 无法控制处理时机

nginx的自动处理在容器启动的特定阶段进行，如果你需要在其他时机处理模板（比如在其他初始化步骤之后），就需要手动控制。

## 实际应用场景对比

让我用具体例子说明什么时候需要手动使用`envsubst`：

### 场景1：nginx自动处理就够了

```yaml name=docker-compose.yaml
services:
  nginx:
    image: nginx:1.25
    volumes:
      # 放在templates目录，nginx会自动处理
      - ./nginx/default.conf.template:/etc/nginx/templates/default.conf.template
    environment:
      - API_HOST=backend
      - API_PORT=3000
```

```nginx name=nginx/default.conf.template
server {
    listen 80;
    location /api/ {
        proxy_pass http://${API_HOST}:${API_PORT}/;
    }
}
```

这种情况下，nginx启动时会自动将模板处理成 `/etc/nginx/conf.d/default.conf`。

### 场景2：需要手动使用envsubst

```bash name=docker-entrypoint.d/01-init-config.sh
#!/bin/bash
set -e

echo "Processing custom configuration templates..."

# 场景2.1: 处理非标准路径的模板
envsubst '${API_HOST} ${API_PORT} ${DB_HOST}' < /tmp/app.conf.template > /etc/nginx/conf.d/app.conf

# 场景2.2: 处理主配置文件（nginx.conf）
envsubst '${WORKER_PROCESSES} ${WORKER_CONNECTIONS}' < /tmp/nginx.conf.template > /etc/nginx/nginx.conf

# 场景2.3: 根据条件生成不同配置
if [ "${SSL_ENABLED}" = "true" ]; then
    envsubst '${SSL_CERT_PATH} ${SSL_KEY_PATH}' < /tmp/ssl.conf.template > /etc/nginx/conf.d/ssl.conf
else
    envsubst '${HTTP_PORT}' < /tmp/http.conf.template > /etc/nginx/conf.d/default.conf
fi

# 场景2.4: 处理应用配置文件（非nginx）
envsubst '${DB_HOST} ${DB_PORT} ${REDIS_HOST}' < /app/config/app.yml.template > /app/config/app.yml

# 场景2.5: 动态生成配置
BACKEND_LIST=""
IFS=',' read -ra BACKENDS <<< "${BACKEND_SERVERS}"
for backend in "${BACKENDS[@]}"; do
    BACKEND_LIST="${BACKEND_LIST}    server ${backend};\n"
done

# 将动态生成的内容注入模板
export BACKEND_LIST
envsubst '${BACKEND_LIST}' < /tmp/upstream.conf.template > /etc/nginx/conf.d/upstream.conf
```

### 场景3：混合使用

```yaml name=docker-compose.yaml
services:
  nginx:
    image: nginx:1.25
    volumes:
      # nginx自动处理的模板
      - ./nginx/templates/:/etc/nginx/templates/
      # 手动处理的模板
      - ./templates/nginx.conf.template:/tmp/nginx.conf.template:ro
      - ./templates/ssl.conf.template:/tmp/ssl.conf.template:ro
      - ./docker-entrypoint.d/:/docker-entrypoint.d/:ro
    environment:
      - API_HOST=backend
      - API_PORT=3000
      - WORKER_PROCESSES=auto
      - WORKER_CONNECTIONS=1024
      - SSL_ENABLED=true
      - SSL_CERT_PATH=/etc/ssl/certs/server.crt
```

## 为什么选择手动envsubst的原因

### 1. 更大的灵活性
```bash
# 可以控制哪些变量被替换
envsubst '${API_HOST} ${API_PORT}' < template.conf > output.conf

# 而不是替换所有${}变量
envsubst < template.conf > output.conf
```

### 2. 复杂的逻辑处理
```bash name=docker-entrypoint.d/02-complex-config.sh
#!/bin/bash
set -e

# 根据环境动态选择模板
if [ "${ENVIRONMENT}" = "production" ]; then
    TEMPLATE_FILE="/tmp/nginx-prod.conf.template"
elif [ "${ENVIRONMENT}" = "staging" ]; then
    TEMPLATE_FILE="/tmp/nginx-staging.conf.template"
else
    TEMPLATE_FILE="/tmp/nginx-dev.conf.template"
fi

# 处理选定的模板
envsubst '${API_HOST} ${API_PORT}' < "${TEMPLATE_FILE}" > /etc/nginx/conf.d/default.conf
```

### 3. 处理主配置文件
nginx自动处理不会覆盖主配置文件 `/etc/nginx/nginx.conf`，如果需要模板化主配置，必须手动处理：

```bash
# 必须手动处理nginx.conf
envsubst '${WORKER_PROCESSES} ${WORKER_CONNECTIONS}' < /tmp/nginx.conf.template > /etc/nginx/nginx.conf
```

### 4. 配置验证
```bash name=docker-entrypoint.d/03-validate-config.sh
#!/bin/bash
set -e

# 处理配置
envsubst < /tmp/nginx.conf.template > /etc/nginx/nginx.conf

# 立即验证配置
if nginx -t; then
    echo "Nginx configuration is valid"
else
    echo "Nginx configuration is invalid, using fallback"
    cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf
    exit 1
fi
```

## 总结

**使用nginx自动处理的情况：**
- 简单的虚拟主机配置
- 模板文件可以放在 `/etc/nginx/templates/` 目录
- 不需要复杂的条件逻辑
- 输出路径符合nginx默认规则

**使用手动envsubst的情况：**
- 需要处理主配置文件 (`nginx.conf`)
- 模板文件在非标准路径
- 需要条件逻辑或复杂的生成规则
- 需要处理非nginx配置文件
- 需要在特定时机处理模板
- 需要配置验证和错误处理

在实际项目中，经常是两种方式结合使用，简单的配置让nginx自动处理，复杂的配置用`docker-entrypoint.d/`脚本手动处理。