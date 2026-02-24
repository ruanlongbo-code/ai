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


class ScenarioModel(BaseModel):
    """场景分组数据模型"""
    scenario: str
    cases: List[TestCaseModel]


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
        """基于测试点生成特定格式的测试用例（按场景分组）"""
        writer = get_stream_writer()
        writer("【开始用例生成】：基于测试点生成按场景分组的测试用例")
        parser = JsonOutputParser(pydantic_schema=List[ScenarioModel])
        chain = generator_testcase.prompt | llm | parser
        response = chain.invoke({
            "document": state.get("input_requirement"),
            "test_point": state.get("test_point"),
            "test_cases": state.get("test_cases"),
            "test_case_coverage_report": state.get("test_case_coverage_report")
        })

        # 兼容处理：AI 可能返回场景分组格式，也可能返回扁平列表
        flattened_cases = []
        if response and isinstance(response, list):
            first = response[0] if response else {}
            if isinstance(first, dict) and "scenario" in first and "cases" in first:
                # 场景分组格式 → 保留 scenario 信息到每条 case 中
                for scenario_group in response:
                    scenario_name = scenario_group.get("scenario", "未分类场景")
                    cases = scenario_group.get("cases", [])
                    for idx, case in enumerate(cases):
                        case["scenario"] = scenario_name
                        case["scenario_sort"] = idx
                        flattened_cases.append(case)
            else:
                # 扁平列表格式（兼容旧格式）
                for idx, case in enumerate(response):
                    if isinstance(case, dict):
                        if "scenario" not in case:
                            case["scenario"] = "默认场景"
                        case["scenario_sort"] = idx
                        flattened_cases.append(case)

        writer(f"【用例生成完成】：共生成 {len(flattened_cases)} 条用例")
        return {"test_cases": flattened_cases}

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
        """保存测试用例到数据库（含用例集和场景分组）"""
        writer = get_stream_writer()
        writer("【开始执行节点】：保存测试用例到数据库")
        
        test_cases = state.get('test_cases', [])
        # 从config中获取上下文信息
        requirement_id = config["metadata"].get('requirement_id') if config else None
        creator_id = config["metadata"].get('creator_id') if config else None
        project_id = config["metadata"].get('project_id') if config else None
        
        writer(f"开始保存{len(test_cases)}条测试用例到数据库")
        
        if not requirement_id:
            writer("requirement_id 为空，无法保存测试用例")
            return {"saved_cases_count": 0}
        
        saved_cases = self._save_functional_cases_to_db(test_cases, requirement_id, creator_id, project_id)
        
        writer(f"测试用例保存完成，成功保存{len(saved_cases)}条")
        return {"saved_cases_count": len(saved_cases)}
    
    def _save_functional_cases_to_db(self, test_cases, requirement_id, creator_id, project_id=None):
        """将功能测试用例保存到数据库（含用例集和场景分组）"""
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
            current_time = datetime.now()

            # === 1. 查询需求标题用于用例集命名 ===
            req_title = "未知需求"
            cursor.execute("SELECT title FROM requirement_doc WHERE id = %s", (str(requirement_id),))
            req_row = cursor.fetchone()
            if req_row:
                req_title = req_row.get("title", "未知需求")

            # === 2. 查找或创建用例集 ===
            # 如果该需求已有用例集则复用，否则新建
            case_set_id = None
            cursor.execute(
                "SELECT id FROM functional_case_set WHERE requirement_id = %s ORDER BY id DESC LIMIT 1",
                (str(requirement_id),)
            )
            existing_set = cursor.fetchone()
            if existing_set:
                case_set_id = existing_set["id"]
                # 更新用例集时间
                cursor.execute(
                    "UPDATE functional_case_set SET updated_at = %s WHERE id = %s",
                    (current_time, case_set_id)
                )
                writer(f"【复用用例集】：用例集ID={case_set_id}")
            else:
                # 确定 project_id
                actual_project_id = project_id
                if not actual_project_id:
                    cursor.execute(
                        """SELECT pm.project_id FROM requirement_doc rd 
                           JOIN project_module pm ON rd.module_id = pm.id 
                           WHERE rd.id = %s""",
                        (str(requirement_id),)
                    )
                    proj_row = cursor.fetchone()
                    if proj_row:
                        actual_project_id = proj_row["project_id"]

                if actual_project_id:
                    insert_set_sql = """
                    INSERT INTO functional_case_set (name, description, case_count, scenario_count, 
                                                      requirement_id, project_id, creator_id, 
                                                      created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    set_name = f"{req_title}"
                    set_desc = f"根据需求「{req_title}」AI自动生成的用例集"
                    cursor.execute(insert_set_sql, (
                        set_name, set_desc, 0, 0,
                        str(requirement_id),
                        str(actual_project_id),
                        str(creator_id) if creator_id else None,
                        current_time, current_time
                    ))
                    case_set_id = cursor.lastrowid
                    writer(f"【创建用例集】：{set_name}，ID={case_set_id}")

            # === 3. 先删除该需求的旧功能测试用例 ===
            delete_sql = "DELETE FROM functional_case WHERE requirement_id = %s"
            cursor.execute(delete_sql, (str(requirement_id),))
            writer(f"【删除旧用例】：删除需求 {requirement_id} 的旧功能测试用例")

            # === 4. 按场景分组插入用例 ===
            insert_sql = """
            INSERT INTO functional_case (case_no, case_name, priority, status, scenario, scenario_sort,
                                       preconditions, test_steps, test_data, expected_result, actual_result, 
                                       requirement_id, case_set_id, creator_id, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            saved_count = 0
            scenarios_set = set()
            
            for case_data in test_cases:
                case_no = case_data.get('case_id', f'TC_{saved_count + 1:03d}')
                case_name = case_data.get('case_name', f'功能测试用例_{saved_count + 1}')
                priority = self._convert_priority(case_data.get('priority', 'P2'))
                status = 'design'
                scenario = case_data.get('scenario', '默认场景')
                scenario_sort = case_data.get('scenario_sort', 0)
                preconditions = case_data.get('preconditions', '')
                test_steps = case_data.get('test_steps', '')
                test_data = case_data.get('test_data', '')
                expected_result = case_data.get('expected_result', '')
                actual_result = case_data.get('actual_result', '')

                scenarios_set.add(scenario)

                # 将复杂数据转换为JSON字符串
                test_steps_json = json.dumps(self._convert_test_steps(test_steps), ensure_ascii=False)
                test_data_json = json.dumps(self._convert_test_data(test_data), ensure_ascii=False)

                cursor.execute(insert_sql, (
                    case_no,
                    case_name,
                    priority,
                    status,
                    scenario,
                    scenario_sort,
                    preconditions,
                    test_steps_json,
                    test_data_json,
                    expected_result,
                    actual_result,
                    str(requirement_id),
                    case_set_id,
                    str(creator_id) if creator_id else None,
                    current_time,
                    current_time
                ))
                saved_count += 1
                writer(f"【保存用例】：[{scenario}] {case_name}")

            # === 5. 更新用例集的统计数据 ===
            if case_set_id:
                cursor.execute(
                    "UPDATE functional_case_set SET case_count = %s, scenario_count = %s, updated_at = %s WHERE id = %s",
                    (saved_count, len(scenarios_set), current_time, case_set_id)
                )

            # 提交事务
            connection.commit()
            writer(f"【保存完成】：成功保存 {saved_count} 条用例（{len(scenarios_set)} 个场景）到用例集")
            
            # 查询保存的用例并返回
            query_sql = "SELECT * FROM functional_case WHERE requirement_id = %s ORDER BY scenario, scenario_sort"
            cursor.execute(query_sql, (str(requirement_id),))
            return cursor.fetchall()
            
        except Exception as e:
            if connection:
                connection.rollback()
            writer(f"【保存失败】：保存功能测试用例到数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        finally:
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
        
        if isinstance(test_steps, list):
            return test_steps
            
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
        
        if isinstance(test_data, dict):
            return test_data
            
        if isinstance(test_data, str):
            return {"data": test_data}
        
        return {}

    def create_workflow(self):
        main_workflow = StateGraph(State)
        main_workflow.add_node("生成测试点", self.generator_point)
        main_workflow.add_node("生成测试用例", self.generate_test_case)
        main_workflow.add_node("验证测试用例覆盖率", self.verify_testcase_coverage)
        main_workflow.add_node("保存测试用例", self.save_test_cases)
        main_workflow.add_edge(START, "生成测试点")
        main_workflow.add_edge("生成测试点", "生成测试用例")
        main_workflow.add_edge("生成测试用例", "验证测试用例覆盖率")
        main_workflow.add_edge("保存测试用例", END)
        graph = main_workflow.compile()
        return graph
