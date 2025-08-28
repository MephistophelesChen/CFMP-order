FROM python:3.11.10-slim-bookworm

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 复制公共模块
COPY ../common /app/common

# 暴露端口
EXPOSE 8002

# 设置环境变量
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]
