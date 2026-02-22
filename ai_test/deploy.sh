#!/bin/bash
set -e

echo "========================================="
echo "  AiProtect 智能测试平台 - 一键部署脚本"
echo "========================================="

# -------- 1. 检查 Docker --------
if ! command -v docker &> /dev/null; then
    echo "[1/4] Docker 未安装，正在安装..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo "Docker 安装完成"
else
    echo "[1/4] Docker 已安装: $(docker --version)"
fi

if ! docker compose version &> /dev/null; then
    echo "错误: docker compose 插件未安装，请手动安装 docker-compose-plugin"
    exit 1
fi

# -------- 2. 检查端口 80 是否被占用 --------
if ss -tlnp | grep -q ':80 '; then
    echo "警告: 端口 80 已被占用，可能需要先停止占用的服务（如 nginx、apache）"
    echo "占用情况:"
    ss -tlnp | grep ':80 '
    read -p "是否继续部署？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# -------- 3. 构建并启动 --------
echo "[2/4] 开始构建 Docker 镜像（首次约 5-10 分钟）..."
docker compose up -d --build

# -------- 4. 等待服务就绪 --------
echo "[3/4] 等待服务启动..."
max_retries=30
counter=0
while ! docker exec py_mysql mysqladmin ping -h localhost -u root -p123456py --silent 2>/dev/null; do
    counter=$((counter + 1))
    if [ $counter -ge $max_retries ]; then
        echo "MySQL 启动超时，请检查日志: docker logs py_mysql"
        exit 1
    fi
    echo "  等待 MySQL 就绪... ($counter/$max_retries)"
    sleep 3
done
echo "  MySQL 已就绪"

sleep 5

# -------- 5. 检查服务状态 --------
echo "[4/4] 检查服务状态..."
echo ""
docker compose ps
echo ""
echo "========================================="
echo "  部署完成！"
echo ""
echo "  访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '你的服务器IP')"
echo "  登录账号: admin"
echo "  登录密码: 123456"
echo ""
echo "  常用命令:"
echo "    查看日志:   docker compose logs -f"
echo "    重启服务:   docker compose restart"
echo "    停止服务:   docker compose down"
echo "    重新构建:   docker compose up -d --build"
echo "========================================="
