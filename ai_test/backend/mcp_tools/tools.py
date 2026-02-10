import json
from config import settings
from langchain_core.tools import tool
from langgraph.config import get_stream_writer
from rag.rag_manager import RAGManager
from utils.parser.ai_parser_api_document import AIAPIDocumentParser
from workflow.api_case_generator_main_workflow import ApiCaseGenerateMainWorkFlow
from workflow.case_generator_workflow import GeneratorTestCaseWorkflow
from rag.rag_api import RAGClient


async def rag_search(query: str, project_name: str = 'web_shop'):
    """
    需求检索的服务
    :param query: 需求检索的关键字
    :param project_name: 项目知识库名称
    :return:
    """
    # 初始化rag对象
    rag_manage = RAGManager()
    # 初始化rag对象
    await rag_manage.init_rag(project=project_name, working_dir=settings.STORAGE_PATH)
    # 搜索知识库中的内容
    response = rag_manage.search_text(query)
    result = ""
    async for chunk in response:
        print(chunk, end="", flush=True)
        result += chunk

    return result


@tool("search_requirement", description="需求文档检索的服务")
def search_requirement(query: str):
    writer = get_stream_writer()
    writer("开始执行【需求检索的服务】的工具")
    # ===============运行会报错提示，异步的事件循环不存在===============
    import asyncio
    # 添加到异步运行任务重
    result = asyncio.run(rag_search(query))
    print("知识库检索的结果：", result)
    print("===============工具1执行完毕=================")
    return result


# ===================开发用例生成的工具==================
@tool("generator_case", description="基于需求文档生成用例的服务")
def generator_case(document: str):
    """
    基于需求文档生成功能测试用例的服务
    :param document: 需求文档
    :return:
    """
    print("===============工具2执行开始=================")
    writer = get_stream_writer()
    writer("开始执行【基于需求文档生成用例的服务】的工具")
    workflow = GeneratorTestCaseWorkflow().create_workflow()
    # 开始生成用例
    response = workflow.invoke({"input_requirement": document})
    # writer("开始执行【基于需求文档生成用例的服务】执行结束")
    # 返回生成的测试用例
    return response.get("test_cases")


# ===================接口文档生成接口自动化用的工具============================

@tool("search_api_document", description="接口文档检索的服务")
def search_api_document(query: str):
    """
    去知识库查询接口的详细文档数据
    :param query: 查询的关键词
    :return:
    """
    writer = get_stream_writer()
    writer(f"开始执行【接口文档检索服务】工具,查询：{query}")
    rag_client = RAGClient()
    # 查询到接口文档
    result = rag_client.query(query)
    return result


# 将接口文档转换为生成用例所需的json格式
@tool("api_document_to_cases", description="基于接口文档生成用例的工具")
def api_document_to_cases(api_document: str,
                          preconditions: list,
                          db_config: list,
                          additional_info: dict,
                          test_data: dict):
    """
    基于知识库查询出来的接口文档，生成接口测试用例
    :param api_document: ，知识库检索出来的接口文档
    :param preconditions: 前置依赖接口的调用顺序，如果没有想过数据传空列表
        例如：["接口1",["接口2"]]
    :param preconditions
    :param db_config: 测试项目数据库的配置，如果没有想过数据传空列表
        例如： [
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
    :param additional_info:生成用例时，额外的备注信息，如果没有想过数据传空字段
        例如：{
                "项目名称": "木森上课演示项目",
                "模块名称": "登录模块",
                "备注": "对于注册时不能重复使用的数据，请使用工具随机生成"
            }
    :param test_data:  测试环境中的测试数据，如果没有想过数据传空字段
        例如：{
                "base_url": "http://106.54.233.149:8888",
                            }
    :return:
    """
    # 将接口文档转换为json格式
    api_parser = AIAPIDocumentParser()
    document = api_parser.parser(api_document)
    api_info = json.dumps(document, indent=4, ensure_ascii=False)
    # 后续平台之后，这里可以直接用过接口去读取测试环境的配置
    if not db_config:
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
    if not test_data:
        test_data = {
            "base_url": "http://106.54.233.149:8888",
        }
    if additional_info:
        additional_info = {
            "项目名称": "木森上课演示项目",
            "模块名称": "登录模块",
            "备注": "对于注册时不能重复使用的数据，请使用工具随机生成"
        }
        # 基于接口文档生成用例
    workflow = ApiCaseGenerateMainWorkFlow().create_workflow()
    response = workflow.invoke({"api_info": api_info,
                                "preconditions": preconditions,
                                "db_config": db_config,
                                "additional_info": additional_info,
                                "test_data": test_data,
                                })
    return response.get("api_case_list")


# 定义一个补充用例生成的环境数据的工具
@tool("load_env_data", description="加载用例生的环境数据")
def load_env_data():
    """
    加载用例生成的环境数据
    :return:
    """
    return {
        "db_config": [
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
        ],
        "preconditions": [],
        "additional_info": {
            "项目名称": "木森上课演示项目",
            "模块名称": "登录模块",
            "备注": "对于注册时不能重复使用的数据，请使用工具随机生成"
        },
        "test_data": {
            "base_url": "http://106.54.233.149:8888",
        },
    }


if __name__ == '__main__':
    res = search_requirement.invoke("获取用户注册的需求文档")
    print("=================")
    print(res)
