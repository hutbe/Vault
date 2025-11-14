FROM python:3.13-slim

WORKDIR /app

# 创建必要的目录
# 相对于WORKDIR的相对路径,即/app/shared_data
RUN mkdir -p shared_data/uploads/images

# 声明挂载目录
# 一定要使用绝对路径,VOLUME永远都是绝对路径
VOLUME ["/app/shared_data"]

# Install system dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     default-libmysqlclient-dev \
#     pkg-config \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 9090

# Run gunicorn
CMD ["gunicorn", "--config", "gunicorn.config.py", "app:app"]