import os
from dataclasses import dataclass
from langgraph.config import get_stream_writer
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from typing import TypedDict, List, Annotated
import operator
from config.prompts.api_cases_work import base_case_generator, base_case_check_coverage, supplement_case
from config.settings import llm
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser


@dataclass
class RuntimeContext:
    """运行时上下文参数"""
    interface_id: int  # 接口id


# 定义工作流的数据状态
class StateNode(TypedDict):
    api_doc: str  # 接口文档
    preconditions: list  # 前置执行依赖接口的调用顺序
    cases: Annotated[List, operator.add]  # 保存生成的基础用例
    coverage_is_pass: bool  # 保存是否覆盖所有的测试点
    coverage_report: str  # 覆盖率分析报告
    project: str  # 项目名称
    module: str  # 模块名称
    env_config: dict  # 测试环境配置信息
    out_put_cases: list  # 输出的用例
    interface_id: int


class BaseCaseParser(BaseModel):
    name: str = Field(..., description="用例名称")
    steps: list = Field(..., description="用例步骤")
    expected: str = Field(..., description="预期结果")
    dependencies: dict = Field(..., description="前置依赖接口的调用顺序")


class ApiBaseCaseGeneratorWorkFlow:
    """
    基于接口文档生成基础的测试用例
    """
    parser = JsonOutputParser(pydantic_object=List[BaseCaseParser])

    def generator_base_case(self, state):
        """生成基础用例的节点函数"""
        writer = get_stream_writer()
        writer("【执行节点】：生成基础用例")
        for i in range(3):
            try:
                api_doc = state.get("api_doc")
                preconditions = state.get("preconditions")
                # 获取基础用例生成的提示词，组装调用链，定义输出的用例解析器
                prompt = base_case_generator.prompt
                chain = prompt | llm | self.parser
                response = chain.invoke({"api_doc": api_doc, "preconditions": preconditions})
            except Exception as e:
                print(f"生成的数据格式提取失败（第{i+1}次），重新生成: {e}")
                continue
            else:
                res = response or []
                return {"cases": res}
        # 所有重试均失败，返回空列表避免下游 NoneType 错误
        writer("【用例生成失败】：多次尝试后仍未成功生成基础用例")
        return {"cases": []}

    def check_coverage(self, state):
        """检查用例的覆盖率"""
        writer = get_stream_writer()
        writer("【执行节点】：检查用例的覆盖率")
        api_doc = state.get("api_doc")
        cases = state.get("cases")
        # 对覆盖率进行验证
        chain = base_case_check_coverage.prompt | llm
        response = chain.invoke({"api_doc": api_doc, "cases": str(cases)})
        # 优化一下条件判断：判断响应的结果response.content中是否有100%的覆盖率
        if "100%" in response.content or "100 %" in response.content:
            return {"coverage_is_pass": True}
        else:
            return {"coverage_report": response.content, "coverage_is_pass": False}

    def check_coverage_is_pass(self, state):
        """验证覆盖率是否通过"""
        writer = get_stream_writer()
        writer("【执行节点】：验证覆盖率是否通过")
        print("coverage_is_pass:", state.get("coverage_is_pass"))
        if state.get("coverage_is_pass"):
            return "输出基础测试用例"
        else:
            return "补充生成测试用例"

    def supplement_case(self, state):
        """补充生成测试用例"""
        writer = get_stream_writer()
        for i in range(3):
            writer(f"【执行节点】：正在补充生成测试用例,重试次数{i}")
            try:
                cases = state.get("cases")
                api_doc = state.get("api_doc")
                preconditions = state.get("preconditions")
                coverage_report = state.get("coverage_report")
                chain = supplement_case.prompt | llm | self.parser
                response = chain.invoke({"api_doc": api_doc,
                                         "cases": str(cases),
                                         "coverage_report": coverage_report,
                                         "preconditions": preconditions})
            except Exception as e:
                writer("生成的数据格式提取失败，重新生成")
                continue
            else:
                new_cases = response or []
                return {"cases": new_cases}
        # 所有重试均失败，返回空列表
        writer("【补充用例失败】：多次尝试后仍未成功补充用例")
        return {"cases": []}

    def output_base_case(self, state, runtime=None):
        """输出基础测试用例并保存到数据库"""
        writer = get_stream_writer()
        cases = state.get("cases", []) or []
        writer(f"【用例生成完毕】：一共生成用例数：{len(cases)}条")
        # 保存基础用例到数据库
        if runtime and hasattr(runtime, 'context'):
            if runtime.context:
                interface_id = runtime.context.get("interface_id")
            else:
                interface_id = state.get("interface_id")
        else:
            interface_id = state.get("interface_id")

        if interface_id and cases:
            saved_cases = self._save_base_cases_to_db(cases, interface_id)
            # 如果保存失败返回了 None，使用原始 cases
            if saved_cases is not None:
                cases = saved_cases

        return {"out_put_cases": cases}

    def _save_base_cases_to_db(self, cases, interface_id):
        """将基础用例保存到数据库"""
        writer = get_stream_writer()
        writer("【保存用例】：将基础用例保存到数据库")
        import pymysql
        import json

        if not interface_id:
            print("interface_id 为空，无法保存基础用例")
            return

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
                cursorclass=pymysql.cursors.DictCursor,
                charset='utf8mb4'
            )
            cursor = connection.cursor()

            # 先删除该接口旧基础用例关联的测试用例（外键约束）
            delete_test_cases_sql = """
            DELETE FROM api_test_case 
            WHERE base_case_id IN (SELECT id FROM api_base_case WHERE interface_id = %s)
            """
            cursor.execute(delete_test_cases_sql, (interface_id,))
            deleted_test_cases = cursor.rowcount
            if deleted_test_cases > 0:
                print(f"删除接口 {interface_id} 关联的 {deleted_test_cases} 条旧测试用例")

            # 再删除该接口的旧基础用例
            delete_sql = "DELETE FROM api_base_case WHERE interface_id = %s"
            cursor.execute(delete_sql, (interface_id,))
            print(f"删除接口 {interface_id} 的旧基础用例")

            # 插入新的基础用例
            from datetime import datetime
            insert_sql = """
            INSERT INTO api_base_case (interface_id, name, steps, expected, status, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            saved_count = 0
            current_time = datetime.now()
            for case in cases:
                case_name = case.get('name', f'基础用例_{saved_count + 1}')
                case_steps = case.get('steps', [])
                case_expected = case.get('expected', '')
                case_status = 'ready'  # 默认状态为ready

                # 将steps和expected转换为JSON字符串
                steps_json = json.dumps(case_steps, ensure_ascii=False) if isinstance(case_steps,
                                                                                      (list, dict)) else json.dumps(
                    [case_steps], ensure_ascii=False)
                expected_json = json.dumps([case_expected], ensure_ascii=False) if isinstance(case_expected,
                                                                                              str) else json.dumps(
                    case_expected, ensure_ascii=False)

                cursor.execute(insert_sql, (
                    str(interface_id),
                    case_name,
                    steps_json,
                    expected_json,
                    case_status,
                    current_time,
                    current_time
                ))
                writer(f"【用例保存】： {case_name} 已保存到数据库 ")
                saved_count += 1

            # 提交事务
            connection.commit()
            writer(f"【用例保存完毕】：成功保存 {saved_count} 条基础用例到数据库")
            # 数据库中查询该接口的基线用例
            query_sql = "SELECT * FROM api_base_case WHERE interface_id = %s"
            cursor.execute(query_sql, (str(interface_id),))
            return cursor.fetchall()
        except Exception as e:
            if connection:
                connection.rollback()
            writer(f"【用例保存失败】：保存基础用例到数据库失败")
            import traceback
            traceback.print_exc()
        finally:
            # 关闭数据库连接
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def create_workflow(self):
        """创建工作流的入口"""
        # 一、创建一个Graph
        graph = StateGraph(StateNode)
        # 二、给graph添加节点
        # 1、生成基础的测试用例
        graph.add_node("生成基础测试用例", self.generator_base_case)
        # 2、验证用例的覆盖率
        graph.add_node("检查用例的覆盖率", self.check_coverage)
        # 3、补充生成测试用例
        graph.add_node("补充生成测试用例", self.supplement_case)
        # 4、输出基础测试用例
        graph.add_node("输出基础测试用例", self.output_base_case)

        # 三、对节点进行流程编排
        graph.add_edge(START, "生成基础测试用例")
        graph.add_edge("生成基础测试用例", "检查用例的覆盖率")
        graph.add_conditional_edges("检查用例的覆盖率",
                                    self.check_coverage_is_pass,
                                    ["输出基础测试用例", "补充生成测试用例"])
        graph.add_edge("补充生成测试用例", "检查用例的覆盖率")

        graph.add_edge("输出基础测试用例", END)
        # 四、编译graph对象并返回
        return graph.compile()


if __name__ == '__main__':
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
          "is_superuser": true
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
    preconditions = []
    # 创建工作流
    workflow = ApiBaseCaseGeneratorWorkFlow().create_workflow()
    response = workflow.stream({"api_doc": api_info,
                                "preconditions": preconditions},
                               stream_mode=["messages", "custom"]
                               )
    for chunk in response:
        if chunk[0] == "messages":
            print(chunk[1][0].content, end='')
        elif chunk[0] == "custom":
            print(chunk[1])
