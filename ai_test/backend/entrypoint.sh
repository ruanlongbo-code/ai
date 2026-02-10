#!/bin/sh

echo "等待MySQL启动..."

# 等待MySQL就绪
max_retries=30
counter=0
while ! python -c "import pymysql; pymysql.connect(host='mysql', port=3306, user='root', password='123456py', database='fastapi')" 2>/dev/null; do
    counter=$((counter + 1))
    if [ $counter -ge $max_retries ]; then
        echo "MySQL连接超时，退出"
        exit 1
    fi
    echo "等待MySQL就绪... ($counter/$max_retries)"
    sleep 2
done

echo "MySQL已就绪，启动gunicorn服务..."

# 启动gunicorn服务
exec gunicorn main:app -c gunicorn.py
