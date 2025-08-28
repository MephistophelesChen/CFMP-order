FROM python:3.11.10-slim-bookworm

# 设置工作目录
WORKDIR /app
RUN rm -rf /etc/apt/sources.list.d/* && \
    rm -f /etc/apt/sources.list
# 更换APT源为USTC镜像
RUN echo "deb https://mirrors.ustc.edu.cn/debian/ bookworm main non-free non-free-firmware contrib" > /etc/apt/sources.list \
    && echo "deb-src https://mirrors.ustc.edu.cn/debian/ bookworm main non-free non-free-firmware contrib" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.ustc.edu.cn/debian-security/ bookworm-security main" >> /etc/apt/sources.list \
    && echo "deb-src https://mirrors.ustc.edu.cn/debian-security/ bookworm-security main" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.ustc.edu.cn/debian/ bookworm-updates main non-free non-free-firmware contrib" >> /etc/apt/sources.list \
    && echo "deb-src https://mirrors.ustc.edu.cn/debian/ bookworm-updates main non-free non-free-firmware contrib" >> /etc/apt/sources.list \
    && echo "deb https://mirrors.ustc.edu.cn/debian/ bookworm-backports main non-free non-free-firmware contrib" >> /etc/apt/sources.list \
    && echo "deb-src https://mirrors.ustc.edu.cn/debian/ bookworm-backports main non-free non-free-firmware contrib" >> /etc/apt/sources.list \
    && apt-get update

# 安装系统依赖
RUN apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 注意：公共模块将通过Docker构建上下文复制
# 在运行时通过环境变量PYTHONPATH或sys.path.insert来访问

# 暴露端口
EXPOSE 8003

# 设置环境变量
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=config.settings

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8003"]
