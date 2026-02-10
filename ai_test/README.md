## 🌈 大模型项目开发环境部署

### 后端技术
- 基于 python3.11 + mysql8 + weaviate + langchain + langsmith + langgraph + lightrag
- 使用软件版本
- python 3.11.5
- mysql 8.0.23

### 🚧 目录结构说明

- `agents`: 提供 API 测试代理，支持意图识别和任务执行
- `api_auto_run`: 测试用例执行框架，包括测试用例运行、数据管理、日志记录等
- `rag`: 用于API文档解析和检索，支持OpenAPI、Swagger格式转成数据库数据
- `tools`: 提供各类工具模块，包括测试用例生成、数据库查询、向量检索等
- `workflow`: 定义测试用例生成的工作流，基于状态机模型进行流程控制
- `datas`: 存放测试数据文件，如OpenAPI、Swagger、测试数据Excel等
- `config`: 测试用例生成
- `main.py`: 项目入口文件
- `service`: fastapi后端服务
- `utils`: 接口文档生成用例
- `logs`: 项目日志
- `mcp_tools`: mcp服务
- `.env`: 项目环境变量配置文件
- `requirements.txt`: 项目依赖包列表
- `static`: Swagger接口文档静态样式文件

### 🚧 linux启动前置软件环境mysql

```bash
# 启动mysql数据库服务
systemctl start mysqld
# 配置开机自启动
systemctl enable mysqld
```

### 安装依赖

```bash
# 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# weaviate服务，docker安装weaviate
docker run -p 8080:8080 -p 50051:50051 semitechnologies/weaviate:latest
# 向量数据库
http://localhost:8080
```

### 配置环境

`.env` 模板根据需要修改配置信息

## 运行项目

```bash
python main.py
```

# AI智能体前端访问
http://localhost:8080

# 接口文档访问
http://localhost:8000/swagger

# LangSmith
https://smith.langchain.com/

# 硅基流动
https://cloud.siliconflow.cn/


帮我查询项目的所有接口
    - 应该使用InterfaceQueryTool工具去实现
帮我生成用户注册接口的用例
    - 应该使用InterfaceQueryTool工具去查询接口
    - 使用CompleteCaseGenerationInput去进行用例生成
帮我生成用户注册接口的用例，并且执行生成的用例
    - 应该使用InterfaceQueryTool工具去查询接口
    - 使用CompleteCaseGenerationInput去进行用例生成
    - 使用CaseExecutionTool去执行测试用例
执行所有可用的用例
    - 使用StructuredTestCaseQueryTool去查询出来所有可用的用例
    - 使用CaseExecutionTool去执行测试用例

agent的工具：
    1、向量数据库检索
    2、mysql数据库查询
    3、api文档----->基础用例测试(保存到数据库)
    4、基础用例----->结构化用例生成(保存到数据库)
    5、api文档----->基础用例----->结构化用例生成
    6、测试用例执行的转换
    7、更多的功能，自定义扩展工具去实现，比如：测试报告分析的工具
