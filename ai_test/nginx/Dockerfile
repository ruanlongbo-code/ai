# 第一阶段：构建前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# 复制前端项目文件
COPY frontend/package.json frontend/package-lock.json* ./

# 安装依赖
RUN npm install --registry=https://registry.npmmirror.com

# 复制前端源码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 第二阶段：nginx服务
FROM nginx:1.27.1-alpine

# 从构建阶段复制dist文件
COPY --from=frontend-builder /app/dist /usr/share/nginx/html/dist/

# 复制nginx配置
COPY nginx/default.conf /etc/nginx/conf.d/

# 挂载日志
VOLUME /var/log/

# 挂载端口
EXPOSE 80 81
