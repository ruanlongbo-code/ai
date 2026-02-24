# 从python镜像开始构建
FROM python:3.11-alpine
# 注释标签
LABEL maintainer='peiyu'
LABEL description='Fastapi project'

# 创建/app目录并切换到该目录下
WORKDIR /app

# 先拷贝依赖文件，利用Docker缓存层
COPY requirements.txt .

# 安装系统依赖
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.ustc.edu.cn/g' /etc/apk/repositories && \
    apk update && \
    apk upgrade && \
    apk add --no-cache tzdata mariadb-dev gcc libc-dev && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 升级pip并安装主依赖（独立缓存层）
RUN python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip && \
    pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 安装raganything（可选，失败不影响主服务）
RUN pip install --no-cache-dir --no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple raganything || true

# 拷贝代码到镜像中
COPY . .
RUN chmod 755 ./entrypoint.sh

# 创建日志挂载点避免容器越来越大
VOLUME /app/logs/

# 挂载端口，非端口映射，只是说明该镜像的挂载端口
EXPOSE 8000

# 启动容器后会执行entrypoint.sh的命令
ENTRYPOINT [ "./entrypoint.sh" ]
