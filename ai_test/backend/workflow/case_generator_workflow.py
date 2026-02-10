from dataclasses import dataclass
from typing import TypedDict, List, Annotated
import operator
from langchain_core.output_parsers import JsonOutputParser
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph
from langgraph.types import Command
from langgraph.constants import START, END
from pydantic import BaseModel
from config.settings import llm
from config.prompts.workflow import verify_test_points_coverage, generator_testcase, verify_testcase_coverage, \
    generator_test_point


@dataclass
class RuntimeContext:
    """运行时上下文参数"""
    requirement_id: int  # 需求id
    creator_id: int  # 测试人员名称


class State(TypedDict):
    """主工作流的状态"""
    # 输入需求文档
    input_requirement: str
    test_point: str
    test_cases: Annotated[List, operator.add]
    # 测试用例覆盖率的报告分析
    test_case_coverage_report: str


class State2(TypedDict):
    """子工作流的状态"""
    # 输入需求文档
    document: str
    # 生成的测试点
    point: Annotated[List, operator.add]
    # 覆盖率分析报告
    coverage_report: str


class TestPointModel(BaseModel):
    """测试点数据模型"""
    type: str
    test_point: str


# 生成测试点的工作流
class GeneratorPointWorkflow:

    # 基于需求整理测试点 节点
    def generate_test_points(self, state: State2):
        """基于需求文档生成测试点"""
        writer = get_stream_writer()
        writer("【开始提取测试点】：正在分析需求文档，请稍等...")
        # 获取用户输入的文档
        input_requirement = state.get("document")

        parser = JsonOutputParser(pydantic_schema=List[TestPointModel])

        # 通过提示词和模型创建调用链
        chain = generator_test_point.prompt | llm | parser
        # 调用大模型进行生成
        response = chain.invoke({"document": input_requirement,
                                 "point": state.get("point"),
                                 "coverage_report": state.get("coverage_report")})
        writer(f"【测试点提取】已经提取测试点数量为{len(response)}个")
        # 获取大模型调用的结果
        return {"point": response}

    # 验证测试点覆盖率 节点
    def verify_test_points_coverage(self, state: State2):
        """验证测试点的覆盖率"""
        writer = get_stream_writer()
        writer("【验证测试点覆盖率】：验证测试点的是否覆盖需求文档所有内容")
        chain = verify_test_points_coverage.prompt | llm
        # 调用大模型进行生成
        response = chain.invoke({
            "test_point": state.get("point"),
            "document": state.get("document")
        })
        coverage_report = response.content
        # 获取大模型调用的结果
        return {"coverage_report": coverage_report}

    # 输出所有的测试点
    def output_all_test_points(self, state: State2):
        """输出所有的测试点"""
        writer = get_stream_writer()
        writer("【测试点提取完成】：输出所有的测试点")
        return {"test_point": state.get("point")}

    # 路由分发的节点
    def route_dispatch(self, state: State2):
        """路由分派"""
        writer = get_stream_writer()
        if "测试点已经全部覆盖" in state["coverage_report"]:
            writer("【测试点覆盖率验证通过】：需求文档已全部覆盖")
            return "输出所有测试点"
        else:
            writer("【测试点覆盖率验证未通过】：开始补全测试点")
            return "生成测试点"

    def create_workflow(self):
        # 对子节点进行编排
        workflow = StateGraph(State2)
        # 添加工作流的节点
        workflow.add_node("生成测试点", self.generate_test_points)
        workflow.add_node("验证测试点覆盖率", self.verify_test_points_coverage)
        workflow.add_node("路由分派", self.route_dispatch)
        workflow.add_node("输出所有测试点", self.output_all_test_points)
        # 对节点进行编排
        workflow.add_edge(START, "生成测试点")
        workflow.add_edge("生成测试点", "验证测试点覆盖率")
        workflow.add_conditional_edges("验证测试点覆盖率", self.route_dispatch, ["生成测试点", "输出所有测试点"])
        workflow.add_edge("输出所有测试点", END)
        # 对节点进行编译(作为子工作流使用，配置checkpointer=True即可开启子图的检查点)
        graph1 = workflow.compile()
        return graph1


class TestCaseModel(BaseModel):
    """测试用例数据模型"""
    case_id: str
    case_name: str
    priority: str
    preconditions: str
    test_steps: str
    test_data: str
    expected_result: str
    actual_result: str | None


# 生成测试用例的工作流
class GeneratorTestCaseWorkflow:

    def generator_point(self, state: State):
        """生成测试点"""
        writer = get_stream_writer()
        writer("【开始执行节点】：基于需求文档提取测试点")
        # 创建生成测试点的工作流对象
        graph1 = GeneratorPointWorkflow().create_workflow()
        # 调用子图去生成测试点
        response_state = graph1.invoke({
            "document": state.get("input_requirement")
        })
        # 将子图(工作流)执行结果中的point传递给父工作流的test_point
        return {"test_point": response_state.get("point")}

    # 生成测试用例的节点
    def generate_test_case(self, state: State):
        """基于测试点生成特定格式的测试用例"""
        writer = get_stream_writer()
        writer("【开始用例生成】：基于测试点生成特定格式的测试用例")
        parser = JsonOutputParser(pydantic_schema=List[TestCaseModel])
        chain = generator_testcase.prompt | llm | parser
        response = chain.invoke({
            "document": state.get("input_requirement"),
            "test_point": state.get("test_point"),
            "test_cases": state.get("test_cases"),
            "test_case_coverage_report": state.get("test_case_coverage_report")

        })
        return {"test_cases": response}

    # 分析测试用例是否覆盖所有的测试点
    def verify_testcase_coverage(self, state: State):
        """验证测试用例的覆盖率"""
        writer = get_stream_writer()
        writer("【验证覆盖率】：开始验证用例覆盖率")

        chian = verify_testcase_coverage.prompt | llm
        response = chian.invoke({
            "test_cases": state.get("test_cases"),
            "test_point": state.get("test_point")
        })
        result = response.content
        if "已覆盖全部测试点" in result:
            return Command(goto="保存测试用例")
        else:
            # 再次补充生成测试用例
            return Command(goto="生成测试用例", update={"test_case_coverage_report": result})

    def save_test_cases(self, state: State, config=None):
        """保存测试用例到数据库"""
        writer = get_stream_writer()
        writer("【开始执行节点】：保存测试用例到数据库")
        
        test_cases = state.get('test_cases', [])
        # 从config中获取上下文信息
        requirement_id = config["metadata"].get('requirement_id') if config else None
        creator_id = config["metadata"].get('creator_id') if config else None
        
        writer(f"开始保存{len(test_cases)}条测试用例到数据库")
        
        if not requirement_id:
            writer("requirement_id 为空，无法保存测试用例")
            return {"saved_cases_count": 0}
        

        saved_cases = self._save_functional_cases_to_db(test_cases, requirement_id, creator_id)
        
        writer(f"测试用例保存完成，成功保存{len(saved_cases)}条")
        return {"saved_cases_count": len(saved_cases)}
    
    def _save_functional_cases_to_db(self, test_cases, requirement_id, creator_id):
        """将功能测试用例保存到数据库"""
        writer = get_stream_writer()

        import pymysql
        import json
        import os
        from datetime import datetime

        if not requirement_id:
            print("requirement_id 为空，无法保存功能测试用例")
            return []

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

            # 先删除该需求的旧功能测试用例
            delete_sql = "DELETE FROM functional_case WHERE requirement_id = %s"
            cursor.execute(delete_sql, (str(requirement_id),))
            writer(f"【删除数据库原有功能测试用例】：开始删除需求 {requirement_id} 的旧功能测试用例")

            # 插入新的功能测试用例
            insert_sql = """
            INSERT INTO functional_case (case_no, case_name, priority, status, preconditions, 
                                       test_steps, test_data, expected_result, actual_result, 
                                       requirement_id, creator_id, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            saved_count = 0
            current_time = datetime.now()
            
            for case_data in test_cases:

                case_no = case_data.get('case_id', f'TC_{saved_count + 1:03d}')
                case_name = case_data.get('case_name', f'功能测试用例_{saved_count + 1}')
                priority = self._convert_priority(case_data.get('priority', 'P2'))
                status = 'design'  # 默认状态为设计阶段
                preconditions = case_data.get('preconditions', '')
                test_steps = case_data.get('test_steps', '')
                test_data = case_data.get('test_data', '')
                expected_result = case_data.get('expected_result', '')
                actual_result = case_data.get('actual_result', '')

                # 将复杂数据转换为JSON字符串
                test_steps_json = json.dumps(self._convert_test_steps(test_steps), ensure_ascii=False)
                test_data_json = json.dumps(self._convert_test_data(test_data), ensure_ascii=False)

                cursor.execute(insert_sql, (
                    case_no,
                    case_name,
                    priority,
                    status,
                    preconditions,
                    test_steps_json,
                    test_data_json,
                    expected_result,
                    actual_result,
                    str(requirement_id),
                    str(creator_id) if creator_id else None,
                    current_time,
                    current_time
                ))
                saved_count += 1
                writer(f"【正在保存用例】：{case_name}")

            # 提交事务
            connection.commit()
            writer(f"【用例保存完成】：成功保存 {saved_count} 条功能测试用例到数据库")
            
            # 查询保存的用例并返回
            query_sql = "SELECT * FROM functional_case WHERE requirement_id = %s ORDER BY created_at DESC"
            cursor.execute(query_sql, (str(requirement_id),))
            return cursor.fetchall()
            
        except Exception as e:
            if connection:
                connection.rollback()
            writer(f"【用例保存失败】：保存功能测试用例到数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            # 关闭数据库连接
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def _convert_priority(self, priority_str: str) -> int:
        """转换优先级字符串为数字"""
        priority_map = {
            'P0': 1, 'P1': 2, 'P2': 3, 'P3': 4,
            '高': 1, '中': 3, '低': 4
        }
        return priority_map.get(priority_str, 3)
    
    def _convert_test_steps(self, test_steps: str) -> list:
        """转换测试步骤为JSON格式"""
        if not test_steps:
            return []
        
        # 如果已经是列表，直接返回
        if isinstance(test_steps, list):
            return test_steps
            
        # 简单的步骤分割处理
        steps = []
        if isinstance(test_steps, str):
            step_lines = test_steps.split('\n')
            for i, step in enumerate(step_lines):
                if step.strip():
                    steps.append({
                        "step": i + 1,
                        "action": step.strip(),
                        "expected": ""
                    })
        return steps
    
    def _convert_test_data(self, test_data: str) -> dict:
        """转换测试数据为JSON格式"""
        if not test_data:
            return {}
        
        # 如果已经是字典，直接返回
        if isinstance(test_data, dict):
            return test_data
            
        # 简单的数据处理
        if isinstance(test_data, str):
            return {"data": test_data}
        
        return {}

    def create_workflow(self):
        main_workflow = StateGraph(State)
        # 把子工作流添加到主工作流中的一个节点
        main_workflow.add_node("生成测试点", self.generator_point)
        main_workflow.add_node("生成测试用例", self.generate_test_case)
        main_workflow.add_node("验证测试用例覆盖率", self.verify_testcase_coverage)
        main_workflow.add_node("保存测试用例", self.save_test_cases)
        # 对节点进行编排序
        main_workflow.add_edge(START, "生成测试点")
        main_workflow.add_edge("生成测试点", "生成测试用例")
        main_workflow.add_edge("生成测试用例", "验证测试用例覆盖率")
        main_workflow.add_edge("保存测试用例", END)
        # 对主工作流进行编译,设置检查点
        graph = main_workflow.compile()
        return graph


if __name__ == '__main__':
    workflow = GeneratorTestCaseWorkflow().create_workflow()
    response = workflow.stream({
        "input_requirement": """
        ### 用户注册功能概述  
        用户注册功能（F1.1）是电商系统用户模块的核心功能，支持新用户通过邮箱或用户名+密码的方式创建账户。以下是关键细节：  
        
        #### 主流程  
        1. 用户填写注册信息（用户名/邮箱、密码）。  
        2. 系统校验格式与唯一性：  
           - 用户名：4~20位字母数字组合，唯一性校验。  
           - 邮箱：符合标准格式（xxx@xxx.xx），唯一性校验。  
           - 密码：长度≥6位。  
        3. 提交成功后，系统自动创建账户，初始状态为“正常”，并记录注册时间。  
        4. 用户自动登录并跳转至首页。  
        
        #### 异常处理  
        - **重复注册**：提示“邮箱/用户名已存在”。  
        - **密码不一致**：提示重新输入。  
        
        #### 业务规则  
        - 新用户默认头像为系统预设图片。  
        - 注册时间记录精确到秒，用于后续行为分析（如用户留存统计）。  
        - 与**用户登录功能（F1.2）**直接关联，注册账户可立即用于登录。  
        
        #### 关联功能  
        - **获取验证码（F1.6）**：支持绑定手机/邮箱时的安全验证（需短信/邮箱验证）。  
        - **用户信息修改（F1.3）**：允许后续完善昵称、头像等资料。  
        
        ### 技术实现  
        - 采用前端格式校验与后端唯一性校验双重保障。  
        - 密码存储需加密（如哈希算法）。  
        """
    },
        subgraphs=True,
        stream_mode=['messages', "custom"],
        config={"configurable": {"thread_id": "1"}},
        context={"creator_id": 2, "requirement_id": 2}
    )
    # （custom，消息内容)）     => （(),custom，消息内容)）
    # （messages，(AIMassage(content="消息内容"))）   =>（(),messages，(AIMassage(content="消息内容"))）
    for chunk in response:
        if chunk[1] == 'custom':
            print()
            print(chunk[2])
        elif chunk[1] == 'messages':
            print(chunk[2][0].content, end="", flush=True)
