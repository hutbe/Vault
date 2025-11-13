# FROM nginx:1.27-alpine

FROM nginx:1.28.0-alpine-slim

# 创建必要的目录
RUN mkdir -p /usr/share/nginx/html \
             /var/log/nginx \
             /etc/nginx/conf.d \
             /etc/nginx/certs

# 声明卷挂载点，docker-compose 可以实际挂载这些卷
VOLUME ["/usr/share/nginx/html"]
VOLUME ["/var/log/nginx"]
VOLUME ["/etc/nginx/conf.d"]
VOLUME ["/etc/nginx/certs"]

# 删除默认配置
# RUN rm /etc/nginx/conf.d/default.conf
#
# # 复制默认配置
COPY conf.d/ /etc/nginx/conf.d/
COPY snippets/ /etc/nginx/snippets/
COPY templates/ /etc/nginx/templates/
# COPY index.html /usr/share/nginx/html/
#
# # 拷贝我们自己的配置
# COPY default.conf /etc/nginx/conf.d/default.conf

# 复制配置文件
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
COPY snippets/ /etc/nginx/snippets/
COPY templates/ /etc/nginx/templates/

# 复制SSL证书（如果有的话）
# COPY certs/ /etc/nginx/certs/



# 可选：静态文件（如果不从 Flask 提供，直接 COPY）
# COPY ../frontend/dist/ /usr/share/nginx/html/

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]