# 工作进程（暂时使用 1 个 worker 来避免数据库初始化问题）
workers = 1
# 设置守护进程 - Docker容器中必须为False，否则容器会退出
daemon = False
# 监听内网端口8000
bind = '0.0.0.0:8000'
# 设置为True，开发时用，代码修改会自动重启
reload = False
# gunicorn进程文件名。不能放在容器里面，防止文件存在
pidfile = '/tmp/gunicorn.pid'
# gunicorn日志文件
accesslog = '/app/logs/gunicorn_access.log'
errorlog = '/app/logs/gunicorn_error.log'
# 工作模式
worker_class = 'uvicorn.workers.UvicornWorker'
# 指定每个工作者的线程数
threads = 2
# 设置最大并发量
worker_connections = 2000
# 请求超时时间（秒）- AI处理可能耗时较长，设置为180秒
timeout = 180
# 优雅关闭超时
graceful_timeout = 60
# 错误日志的日志级别
loglevel = 'info'

# 在每个 worker 启动时初始化数据库
def on_starting(server):
    """主进程启动时执行"""
    pass

def when_ready(server):
    """所有 worker 启动完成时执行"""
    pass

def post_fork(server, worker):
    """每个 worker 进程启动时执行（数据库初始化由 FastAPI lifespan 统一管理）"""
    pass

def pre_fork(server, worker):
    """worker 进程 fork 之前执行"""
    pass
