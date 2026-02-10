#!/bin/sh
# 前端部署
/usr/local/nginx/sbin/nginx && echo 启动nginx部署前端

# 删除gunicorn进程pid
rm -rf /opt/agent/backend/logs/gunicorn.pid
echo 删除gunicorn.pid文件

# 后端部署
cd /opt/agent/backend && echo 切换到后端项目目录
gunicorn main:app -c gunicorn.py
