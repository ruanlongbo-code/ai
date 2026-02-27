## 本地项目：ruanlongbo-ai

此项目代码来自 GitHub 仓库 [ruanlongbo-code/ai](https://github.com/ruanlongbo-code/ai)，已在你的 `PycharmProjects` 下创建为 `ruanlongbo-ai/`。

### 目录说明

- `ai_test/backend/`: FastAPI 后端（Tortoise ORM + MySQL）
- `ai_test/frontend/`: Vue3 + Vite 前端
- `ai_test/docker-compose.yml`: Docker 一键启动（包含 MySQL + 后端 + Nginx(前端)）

### 推荐：Docker 一键启动（最快）

在项目根目录执行：

```bash
cd ai_test
cp .env.example .env
docker compose up -d --build
```

访问：

- 前端：`http://localhost`（宿主机 80 端口）
- 后端 Swagger：`http://localhost/api/swagger`
- 后端 ReDoc：`http://localhost/api/redoc`

说明：

- 你需要在 `ai_test/.env` 里配置 LLM 相关参数（如 `BASE_URL`、`API_KEY`、`LLM_MODEL`）。示例见 `ai_test/.env.example`
- 后端默认会在启动时初始化数据库并创建管理员账号（用户名/密码由环境变量控制，见 `.env.example`）

### 非 Docker（本地调试后端）

如果你希望直接用本机 Python 跑后端：

```bash
cd ai_test/backend
cp .env.example .env
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements_core.txt
python main.py
```

