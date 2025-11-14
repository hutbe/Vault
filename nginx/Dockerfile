# FROM nginx:1.27-alpine

FROM nginx:1.28.0-alpine-slim

# 安装 openssl 工具
RUN apk update && apk add --no-cache openssl

# 创建必要的目录
RUN mkdir -p /usr/share/nginx/www \
             /var/log/nginx \
             /etc/nginx/conf.d \
             /etc/nginx/certs \
             /usr/share/nginx/shared_data/uploads/images

# 声明卷挂载点，docker-compose 可以实际挂载这些卷
VOLUME ["/usr/share/nginx/www"]
VOLUME ["/var/log/nginx"]
VOLUME ["/etc/nginx/conf.d"]
VOLUME ["/etc/nginx/certs"]
VOLUME ["/usr/share/nginx/shared_data"]

# 复制配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
COPY snippets/ /etc/nginx/snippets/
COPY templates/ /etc/nginx/templates/
COPY docker-entrypoint.d/ /docker-entrypoint.d/

# 复制SSL证书（如果有的话）
# COPY certs/ /etc/nginx/certs/


# 可选：静态文件（如果不从 Flask 提供，直接 COPY）
# COPY ../www/dist/ /usr/share/nginx/www/

RUN chmod +x /docker-entrypoint.d/*.sh

EXPOSE 80 443 8000 8010 9000

CMD ["nginx", "-g", "daemon off;"]