"""
接口用例生成的主流程：
    包含将接口文档-->基础用例
    遍历基础用例---并发去生成可以执行的用例
"""
import operator
from typing import TypedDict, Annotated, List
from langgraph.constants import START, END
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph
from langgraph.types import Send
from workflow.api_basecase_workflow import ApiBaseCaseGeneratorWorkFlow, StateNode
from workflow.api_run_case_wrokflow import ApiRunCaseGeneratorWorkFlow, ApiState


class MainState(TypedDict):
    api_info: str  # 接口文档信息
    preconditions: list  # 相关依赖接口文档
    base_cases: list  # 生成的基础用例(所有的基础用例)
    db_config: list  # 数据库配置
    additional_info: dict  # 额外补充信息
    test_data: dict  # 测试数据
    base_case: dict  # 基础用例
    api_case_list: Annotated[List, operator.add]
    interface_id: int  # 接口id


class ApiCaseGenerateMainWorkFlow0:
    """接口用例生成的主流程"""

    @staticmethod
    def generator_base_case(state: MainState):
        """生成基础用例"""
        writer = get_stream_writer()
        writer("【工作流调用】：调用生成基础用例的工作流")
        api_info = state.get("api_info")
        preconditions = state.get("preconditions")
        # 调用子流程，去生成基础用例
        workflow = ApiBaseCaseGeneratorWorkFlow().create_workflow()
        basecase_state: StateNode = workflow.invoke({"api_doc": api_info, "preconditions": str(preconditions)})
        # 数据库中查询该接口所有的基础用例
        return {"base_cases": basecase_state.get("out_put_cases")}

    @staticmethod
    def generate_run_api_case(state: MainState):
        """生成可以运行的接口用例"""
        writer = get_stream_writer()
        writer("【工作流调用】：调用生成可执行用例的工作流")
        workflow = ApiRunCaseGeneratorWorkFlow().create_workflow()
        api_case_state: ApiState = workflow.invoke({"base_case": state.get("base_case"),
                                                    "db_config": state.get("db_config", []),
                                                    "additional_info": state.get("additional_info"),
                                                    "test_data": state.get("test_data"),
                                                    "preconditions_api_doc": state.get("preconditions"),
                                                    "api_info": state.get("api_info"),
                                                    })
        # 获取生成的可执行用例
        api_case = api_case_state.get("api_case")
        return {"api_case_list": [api_case]}

    @staticmethod
    def api_case_generation_task_split(state: MainState):
        """并发去生成可以执行的接口测试用例"""
        writer = get_stream_writer()
        writer("【任务并发】：开始并发生可执行用例")
        task_list = []
        for base_case in state.get("base_cases"):
            task_list.append(
                Send("生成可执行用例", {
                    "api_info": state.get("api_info"),
                    "base_case": base_case,
                    "db_config": state.get("db_config", []),
                    "additional_info": state.get("additional_info"),
                    "test_data": state.get("test_data"),
                    "preconditions_api_doc": state.get("preconditions")
                })
            )
        return task_list

    @staticmethod
    def output_save_all_case(state: MainState):
        """保存生成的所有用例"""
        writer = get_stream_writer()
        writer("【生成完成】：已保存基础用例与可执行用例")

    def create_workflow(self):
        """创建工作流"""
        graph = StateGraph(MainState)
        # 生成基础用例
        graph.add_node("生成基础用例", self.generator_base_case)
        graph.add_node("生成可执行用例", self.generate_run_api_case)
        # 对执行节点进行编排
        graph.add_edge(START, "生成基础用例")
        graph.add_conditional_edges("生成基础用例", self.api_case_generation_task_split, ['生成可执行用例'])
        graph.add_edge("生成可执行用例", END)
        return graph.compile()


class ApiCaseGenerateMainWorkFlow:
    """接口用例生成的主流程"""

    @staticmethod
    def generator_base_case(state: MainState):
        """生成基础用例"""
        api_info = state.get("api_info")
        preconditions = state.get("preconditions")
        # 调用子流程，去生成基础用例
        workflow = ApiBaseCaseGeneratorWorkFlow().create_workflow()
        basecase_state: StateNode = workflow.invoke({"api_doc": api_info,
                                                     "preconditions": str(preconditions),
                                                     "interface_id": state.get("interface_id")
                                                     },
                                                    )
        return {"base_cases": basecase_state.get("out_put_cases")}

    @staticmethod
    def generate_run_api_case(state: MainState):
        """单线程逐个用例生成可执行用例"""
        for case in state.get("base_cases"):
            # 创建工作流
            workflow = ApiRunCaseGeneratorWorkFlow().create_workflow()
            # 提交任务到线程池（第一个参数为线程执行的任务函数，第二个参数开始为传递给工作函数的参数）
            workflow.invoke({"base_case": case,
                             "db_config": state.get("db_config", []),
                             "additional_info": state.get("additional_info"),
                             "test_data": state.get("test_data"),
                             "preconditions_api_doc": state.get("preconditions"),
                             "api_info": state.get("api_info"),
                             "base_case_id": case.get("id"),
                             "interface_id": state.get("interface_id"),
                             })
        return {}

    # @staticmethod
    # def generate_run_api_case(state: MainState):
    #     """利用多线程并发生成可执行的接口用例"""
    #     with ThreadPoolExecutor(max_workers=7) as executor:
    #         for case in state.get("base_cases"):
    #             # 创建工作流
    #             workflow = ApiRunCaseGeneratorWorkFlow().create_workflow()
    #             # 提交任务到线程池（第一个参数为线程执行的任务函数，第二个参数开始为传递给工作函数的参数）
    #             executor.submit(workflow.invoke, {"base_case": case,
    #                                               "db_config": state.get("db_config", []),
    #                                               "additional_info": state.get("additional_info"),
    #                                               "test_data": state.get("test_data"),
    #                                               "preconditions_api_doc": state.get("preconditions"),
    #                                               "api_info": state.get("api_info"),
    #                                               "base_case_id": case.get("id"),
    #                                               "interface_id": state.get("interface_id"),
    #                                               })
    #     return {}

    @staticmethod
    def output_save_all_case(state: MainState):
        """保存生成的所有用例"""
        writer = get_stream_writer()
        writer("【流程完成】：所有的基础用例与可执行用例生成完毕")

    def create_workflow(self):
        """创建工作流"""
        graph = StateGraph(MainState)
        # 生成基础用例
        graph.add_node("生成基础用例", self.generator_base_case)
        graph.add_node("生成可执行用例", self.generate_run_api_case)
        graph.add_node("保存所有用例", self.output_save_all_case)
        # 对执行节点进行编排
        graph.add_edge(START, "生成基础用例")
        graph.add_edge("生成基础用例", "生成可执行用例")
        graph.add_edge("生成可执行用例", "保存所有用例")
        graph.add_edge("保存所有用例", END)
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
            "description": "用户账号",
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
    additional_info = {
        "项目名称": "木森上课演示项目",
        "模块名称": "登录模块",
        "备注": "对于注册时不能重复使用的数据，请使用工具随机生成"
    }
    test_data = {
        "base_url": "http://106.54.233.149:8888",
    }

    workflow = ApiCaseGenerateMainWorkFlow().create_workflow()
    response = workflow.stream({"api_info": api_info,
                                "preconditions": preconditions,
                                "db_config": db_config,
                                "additional_info": additional_info,
                                "test_data": test_data,
                                },
                               subgraphs=True,
                               stream_mode=["messages", "custom"]
                               )
    writer = get_stream_writer()
    for item in response:
        if item[1] == "messages":
            writer(item[2][0].content)
        elif item[1] == "custom":
            writer(str(item[1]))
