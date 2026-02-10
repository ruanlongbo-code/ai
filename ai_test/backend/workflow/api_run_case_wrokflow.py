from langchain_core.exceptions import OutputParserException
from langgraph.constants import START, END
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph
from typing import TypedDict
from api_case_run.execute import TestExecutor
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from api_case_run import global_tools
from utils.loader.get_script_function_list import get_module_functions
from utils.loader.get_test_file_list import inspect_test_files
from config.prompts.api_cases_work import api_case_generator
from config.settings import llm
import copy


class ApiState(TypedDict):
    """定义工作流的数据状态"""
    api_doc: str  # 主接口的文档
    base_case: str  # 基础用例
    preconditions_api_doc: list  # 前置依赖接口的文档
    test_data: dict  # 测试数据
    db_config: list  # 数据库的配置信息

    additional_info: str  # 额外的补充信息
    test_files_list: list  # 文件上传相关接口可以用文件列表
    function_list: list  # 前后置脚本中可以引用的工具函数列表
    api_case: dict  # 生成的接口用例
    # 标记用例的状态(可用性)
    status: str
    # 记录重新生成的次数
    generator_count: int
    base_case_id: int
    interface_id: int


class APICaseParser(BaseModel):
    """解析生成的接口用例"""
    name: str = Field(..., description="用例名称")
    description: str = Field(..., description="用例描述")
    interface: str = Field(..., description="接口名称")
    preconditions: list = Field(..., description="前置依赖接口信息")
    request: dict = Field(..., description="用例请求数据")
    assertions: list = Field(..., description="用例断言信息")


class ApiRunCaseGeneratorWorkFlow:
    """可运行的接口用例生成的工作流"""

    @staticmethod
    def get_functions_and_files(state: ApiState):
        """加载用例生成需要用到的脚本工具函数和可用测试文件的列表"""
        test_files_list = inspect_test_files()
        function_list = get_module_functions(global_tools)
        return {
            "test_files_list": test_files_list,
            "function_list": function_list
        }

    @staticmethod
    def generator_api_case(state: ApiState):
        """生成可执行的接口用例"""
        # 在生成的时候，如果失败了则重新进行生成
        for i in range(3):
            try:
                parser = JsonOutputParser(pydantic_object=APICaseParser)
                # 组装一个调用链
                chain = api_case_generator.prompt | llm | parser
                response = chain.invoke({
                    'api_case_output_format': api_case_generator.api_case_output_format,
                    'case_info': state.get("base_case"),
                    'case_api': state.get("api_doc"),
                    'other_api': state.get("preconditions_api_doc"),
                    'test_data': state.get("test_data"),
                    'files_list': state.get("test_files_list"),
                    'function_list': state.get("function_list"),
                    'additional_info': state.get("additional_info"),
                })
            except OutputParserException as e:
                writer = get_stream_writer()
                writer(f"【用例生成失败】：生成的用例数据 JSON 解析错误：{e}")
                continue
            else:
                if response:
                    return {"api_case": response, "generator_count": state.get("generator_count", 0) + 1}
        else:
            writer = get_stream_writer()
            writer("【用例生成失败】：多次尝试后仍未生成可执行用例")
            return {"api_case": {}, "generator_count": state.get("generator_count", 0) + 1}

    @staticmethod
    def api_case_run(state: ApiState):
        """执行生成的测试用例，验证用例是否可用"""
        writer = get_stream_writer()
        writer("【预执行验证】：开始对用例进行预执行验证可用性")
        # 获取用例相关的信息，进行执行
        case_info = state.get("api_case", {})
        test_env_global = state.get("test_data")
        db_config = state.get("db_config")
        try:
            # 创建一个用例执行器
            case_executor = TestExecutor(test_env_global=test_env_global, db_config=db_config)
            # 在预运行的时候会对用例数据进行替换操作，所有这个地方需要对用例数据进行深拷贝，避免对原数据进行修改
            case_ = copy.deepcopy(case_info)
            # 执行测试用例
            case_executor.execute_test_case(case_)
        except Exception as e:
            writer = get_stream_writer()
            writer(f"【预执行失败】：用例执行异常：{e}")
            return {"status": "disabled"}
        else:
            return {"status": "ready"}

    @staticmethod
    def check_case_is_pass(state: ApiState):
        """验证用例是否可以执行"""
        if state.get("status") == "ready":
            return "保存用例"
        elif state.get("generator_count", 0) <= 3:
            return "生成接口用例"
        else:
            return "保存用例"

    @staticmethod
    def sava_api_case(state: ApiState):
        """保存接口用例到数据库"""
        cases = state.get("api_case", {})
        status = state.get("status", "disabled")

        # 从运行时上下文获取必要的ID信息
        base_case_id = state.get("base_case_id")
        interface_id = state.get("interface_id")
        writer = get_stream_writer()
        writer(f"【保存用例】：开始保存接口测试用例{cases.get('name')},状态: {status}")

        if not cases:
            writer("【保存用例跳过】：没有生成的用例需要保存")

            return {"saved": False, "message": "没有用例数据"}

        # 调用保存方法
        result = ApiRunCaseGeneratorWorkFlow._save_api_case_to_db(cases, status, base_case_id)

        writer(f"【保存用例结果】：{result}")
        return result

    @staticmethod
    def _save_api_case_to_db(case_data, status, base_case_id=None):
        """将接口测试用例保存到数据库"""
        import pymysql
        import json
        import os
        from datetime import datetime
        writer = get_stream_writer()

        if not case_data:
            writer("【保存用例失败】：用例数据为空，无法保存")
            return {"saved": False, "message": "用例数据为空"}

        connection = None
        cursor = None

        try:
            # 建立数据库连接
            connection = pymysql.connect(
                host=os.getenv("DATA_BASE_HOST"),
                port=int(os.getenv("DATA_BASE_PORT")),
                user=os.getenv("DATA_BASE_USER"),
                password=os.getenv("DATA_BASE_PASSWORD"),
                database=os.getenv("DATA_BASE_NAME"),
                charset='utf8mb4'
            )
            cursor = connection.cursor()

            # 准备插入数据 - 根据实际的ApiTestCase模型字段
            case_name = case_data.get('name', f'接口测试用例_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            case_description = case_data.get('description', '')
            case_interface = case_data.get('interface', '')
            case_preconditions = case_data.get('preconditions', [])
            case_request = case_data.get('request', {})
            case_assertions = case_data.get('assertions', [])

            # 将复杂数据结构转换为JSON字符串
            preconditions_json = json.dumps(case_preconditions, ensure_ascii=False) if case_preconditions else '[]'
            request_json = json.dumps(case_request, ensure_ascii=False) if case_request else '{}'
            assertions_json = json.dumps(case_assertions, ensure_ascii=False) if case_assertions else '[]'

            # 插入接口测试用例 - 使用正确的字段名
            insert_sql = """
            INSERT INTO api_test_case (
                base_case_id, name, description, interface_name,
                preconditions, request, assertions, status, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            current_time = datetime.now()

            cursor.execute(insert_sql, (
                base_case_id,
                case_name,
                case_description,
                case_interface,
                preconditions_json,
                request_json,
                assertions_json,
                status,
                current_time,
                current_time
            ))

            # 获取插入的用例ID
            case_id = cursor.lastrowid

            # 提交事务
            connection.commit()
            writer(f"【保存成功】：成功保存接口测试用例到数据库，用例ID: {case_id}")

            return {
                "saved": True,
                "case_id": case_id,
                "message": f"成功保存用例: {case_name}",
                "case_data": {
                    "id": case_id,
                    "name": case_name,
                    "status": status,
                    "created_at": current_time.isoformat()
                }
            }

        except Exception as e:
            if connection:
                connection.rollback()
            error_msg = f"保存接口测试用例到数据库失败: {str(e)}"
            writer(error_msg)
            import traceback
            traceback.print_exc()
            return {"saved": False, "message": error_msg}
        finally:
            # 关闭数据库连接
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def create_workflow(self):
        """创建工作流"""
        graph = StateGraph(ApiState)
        # 添加节点
        graph.add_node("加载工具函数和文件列表", self.get_functions_and_files)
        graph.add_node("生成接口用例", self.generator_api_case)
        graph.add_node("用例预执行", self.api_case_run)
        graph.add_node("保存用例", self.sava_api_case)
        # 节点编排
        graph.add_edge(START, "加载工具函数和文件列表")
        graph.add_edge("加载工具函数和文件列表", "生成接口用例")
        graph.add_edge("生成接口用例", "用例预执行")
        graph.add_conditional_edges("用例预执行", self.check_case_is_pass, ["保存用例", "生成接口用例"])
        graph.add_edge("保存用例", END)
        return graph.compile()


if __name__ == '__main__':
    app = ApiRunCaseGeneratorWorkFlow().create_workflow()
    # 接口文档(从接口表中查询)
    api_info = """
    {
      "path": "/api/users/register",
      "method": "POST",
      "summary": "用户注册",
      "description": "",
      "parameters": {
        "header": [],
        "path": [],
        "query": []
      },
      "requestBody": {
        "content_type": "application/json",
        "body": [
          {
            "name": "username",
            "type": "string",
            "description": "用户名",
            "required": true
          },
          {
            "name": "password",
            "type": "string",
            "description": "密码，长度在8到16位之间",
            "required": true
          },
          {
            "name": "password_confirm",
            "type": "string",
            "description": "确认密码",
            "required": true
          },
          {
            "name": "email",
            "type": "string",
            "description": "邮箱",
            "required": true
          },
          {
            "name": "mobile",
            "type": "string",
            "description": "手机号",
            "required": true
          },
          {
            "name": "nickname",
            "type": "string",
            "description": "昵称",
            "required": false
          }
        ]
      },
      "responses": [
        {
          "http_code": 200,
          "description": "Successful Response",
          "media_type": "application/json",
          "response_body": {
            "id": 123,
            "username": "string_example",
            "nickname": "string_example",
            "email": "string_example",
            "mobile": "string_example",
            "is_active": true,
            "is_superuser": false
          }
        },
        {
          "http_code": 422,
          "description": "Validation Error",
          "media_type": "application/json",
          "response_body": {}
        }
      ]
    }

      """
    # 基础用例(从数据库中查询)
    base_case = {
        "name": "正常请求-注册成功",
        "steps": [
            "发送POST请求到/api/users/register",
            "请求头设置Content-Type为application/json",
            "请求体包含正确的username、password、password_confirm、email、mobile参数"
        ],
        "expected": [
            "HTTP状态码为200",
            "响应体包含id、username、nickname、email、mobile等字段",
            "is_active和is_superuser字段有默认值"
        ],
        "dependencies": []
    }
    # 从测试环境的数据库配置表中查询数据库配置
    db_config = [
        {
            # 数据库的类型
            "type": "mysql",
            # 连接名称(自定义的)
            "name": "mysql_db",
            "config": {
                "host": "127.0.0.1",
                "port": 3306,
                "user": "root",
                "password": "mysql",
                "database": "test001",
            }
        }
    ]
    # 额外的加信息(前端用户输入的参数中传递)
    additional_info = {
        "项目名称": "木森上课演示项目",
        "模块名称": "登录模块",
        "备注": "对于注册时不能重复使用的数据，请使用工具随机生成"
    }
    # 从测试环境表中获取测试数据
    test_data = {
        "base_url": "http://106.54.233.149:8888",
    }
    # 当前接口的前置依赖接口(从数据库中查询当前接口的依赖分组中的前置依赖接口)
    preconditions_api_doc = []

    response = app.stream({
        "api_doc": api_info,
        "base_case": str(base_case),
        "preconditions_api_doc": preconditions_api_doc,
        "db_config": db_config,
        "test_data": test_data,
        "additional_info": str(additional_info),
    },
        stream_mode=["messages", "custom"]
    )
    writer = get_stream_writer()
    for item in response:
        if item[0] == "messages":
            writer(item[1][0].content)
        elif item[0] == "custom":
            writer(str(item[1]))
