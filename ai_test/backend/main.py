from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import os
from dotenv import load_dotenv
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, get_redoc_html
from starlette.staticfiles import StaticFiles
from tortoise import Tortoise
from tortoise.context import TortoiseContext
from service.user.models import User
from utils.auth import AuthUtils
import logging
import logging.handlers
# 导入并注册各模块的路由
from service.user.api import router as user_router
from service.project.api import router as project_router
from service.test_environment.api import router as test_environment_router
from service.functional_test.api import router as functional_test_router
from service.api_test.api import router as api_test_router
from service.test_management.api import router as test_management_router
from service.test_execution.api import router as test_execution_router
from service.schedule.api import router as schedule_router
import uvicorn

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 平台数据库连接配置（使用离散环境变量拼接）
db_host = os.getenv("DATA_BASE_HOST", "localhost")
db_port = os.getenv("DATA_BASE_PORT", "3306")
db_user = os.getenv("DATA_BASE_USER", "root")
db_password = os.getenv("DATA_BASE_PASSWORD", "123456py")
db_name = os.getenv("DATA_BASE_NAME", "ai_test")
DATABASE_URL = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL
    },
    "apps": {
        "models": {
            "models": [
                "service.user.models",
                "service.project.models",
                "service.test_environment.models",
                "service.functional_test.models",
                "service.api_test.models",
                "service.test_execution.models",
                "service.test_management.models",
                "service.schedule.models",
            ],
            "default_connection": "default",
        }
    },
}

# 数据库初始化和关闭函数
async def init_db():
    # _enable_global_fallback=True 确保全局上下文在所有 asyncio task 中可用
    await Tortoise.init(config=TORTOISE_ORM, _enable_global_fallback=True)
    await Tortoise.generate_schemas()
    # 初始化管理员账号
    await init_admin_user()


async def init_admin_user():
    """初始化管理员账号"""
    try:
        # 从环境变量获取管理员配置
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "123456")
        # 原子化创建管理员，避免并发启动时的重复插入
        hashed_password = AuthUtils.get_password_hash(admin_password)
        admin_user, created = await User.get_or_create(
            username=admin_username,
            defaults={
                "password": hashed_password,
                "email": f"{admin_username}@admin.com",
                "real_name": "系统管理员",
                "is_active": True,
                "is_superuser": True,
            },
        )
        if created:
            logger.info(f"管理员账号创建成功: {admin_username}")
        else:
            logger.info(f"管理员账号已存在: {admin_username}")

    except Exception as e:
        logger.error(f"初始化管理员账号失败: {str(e)}")
        raise e


async def close_db():
    await Tortoise.close_connections()


# 创建生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    # 获取日志记录器
    logger = logging.getLogger("uvicorn.access")
    # 创建滚动文件处理器，最大文件大小为10MB
    handler = logging.handlers.RotatingFileHandler("logs/py.log", mode="a", maxBytes=100 * 1024)
    # 设置日志格式
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    # 添加处理器到记录器
    logger.addHandler(handler)
    yield
    # 关闭时清理数据库连接
    await close_db()
    for handler in logger.handlers:
        logger.removeHandler(handler)
        handler.close()


# 创建FastAPI应用实例
app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, title="智能测试平台后端",
              description="v0.1.0版接口文档", version="0.1.0", summary="这个是由fastapi生成的智能测试平台接口文档")


# 接口文档
@app.get("/swagger", include_in_schema=False)
async def custom_swagger_ui_html():
    """swagger接口文档静态文件"""
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " - Swagger UI",
                               oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                               swagger_js_url="/static/swagger-ui-bundle.js",
                               swagger_css_url="/static/swagger-ui.css")


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    """swagger接口文档"""
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """redoc接口文档"""
    return get_redoc_html(openapi_url=app.openapi_url, title=app.title + " - ReDoc",
                          redoc_js_url="/static/redoc.standalone.js")


# 接口文档的静态文件路径
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置中间件
# 注意：不再使用 TortoiseContextMiddleware，因为 Tortoise.init(_enable_global_fallback=True)
# 已经设置了全局上下文，TortoiseContext() 会创建空的隔离上下文覆盖全局配置
app.add_middleware(
    CORSMiddleware,
    # 指定前端调试来源，避免凭证模式与通配符冲突
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 注册路由
@app.get("/")
async def root():
    return {"message": "AI测试平台API服务正在运行"}

app.include_router(user_router, prefix="/user", tags=["用户管理"])
app.include_router(project_router, prefix="/project", tags=["项目管理"])
app.include_router(test_environment_router, prefix="/test_environment", tags=["测试环境"])
app.include_router(functional_test_router, prefix="/functional_test", tags=["功能测试"])
app.include_router(api_test_router, prefix="/api_test", tags=["接口测试"])
app.include_router(test_management_router, prefix="/test_management", tags=["测试管理"])
app.include_router(test_execution_router, prefix="/test_execution", tags=["测试执行"])
app.include_router(schedule_router, prefix="/schedule", tags=["测试排期管理"])

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
