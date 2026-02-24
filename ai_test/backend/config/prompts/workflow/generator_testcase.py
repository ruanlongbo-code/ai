from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["document", "test_point", "test_cases", "test_case_coverage_report"],
    template="""
       你是一位资深测试工程师，请基于下面功能整理出来的测试点，生成标准的测试用例。
       
       **核心要求：你必须将用例按"测试场景"进行分组输出。**
       
       分组原则：
       1. 根据测试点的业务逻辑和验证目标，将相关的用例归入同一个测试场景
       2. 场景命名应清晰表达该场景验证的功能点，如"正常登录场景"、"用户名校验场景"、"密码强度校验场景"
       3. 每个场景下至少包含1个用例，建议2-5个
       4. 场景之间应该互不重叠，覆盖所有测试点

       注意：需求文档中可能包含多个信息来源（原始需求、RAG知识库补充、评审会议知识、历史用例参考），
       请综合所有信息生成更完善的测试用例。特别是评审会议中提到的关键决策和遗漏场景，必须生成对应的用例覆盖。

       需求文档（含增强知识）：
            {document}
       输入测试点：
            {test_point}
       如果提供已经编写的测试用例和覆盖率分析报告，则在提供的测试用例基础和覆盖率分析报告的基础上补充生成未覆盖测试点的用例
           已经生成的用例:
            {test_cases}
           覆盖率分析报告:
            {test_case_coverage_report} 
       如果没有提供已经编写的测试用例则根据测试点直接生成：

       输出的用例，包含测试用例的八要素：
           用例编号(case_id)
           用例名称(case_name)
           优先级(priority) 
           前置步骤(preconditions)
           测试步骤(test_steps) 
           输入数据(test_data) 
           预期结果(expected_result)
           实际结果(actual_result)
           
       **必须以如下json格式输出（按场景分组）：**
           [
               {{
                   "scenario": "场景名称（如：正常登录场景）",
                   "cases": [
                       {{
                           "case_id": "用例编号",
                           "case_name": "用例名称",
                           "priority": "优先级",
                           "preconditions": "前置步骤",
                           "test_steps": "测试步骤",
                           "test_data": "输入数据",
                           "expected_result": "预期结果",
                           "actual_result": "实际结果"
                       }}
                   ]
               }},
               {{
                   "scenario": "另一个场景名称",
                   "cases": [...]
               }}
           ]
           
       注意事项：
       1. 每个场景的cases数组中的用例编号应在场景内连续编号
       2. 场景名称要简洁有意义，能让测试人员一眼看出验证的是什么功能点
       3. 正向验证的测试点归入对应的功能场景，边界值和异常的测试点归入对应的校验/异常场景
            """
)
