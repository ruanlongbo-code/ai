from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["document", "test_point", "test_cases", "test_case_coverage_report"],
    template="""
       你是一位资深测试工程师，请基于下面功能整理的出来的测试点,生成标准的测试用例，
        原始需求文档：
            {document}
        输入测试点：
            {test_point}
       如果提供已经编写的测试用例和覆盖率分析报告，则在提供的测试用例基础和覆盖率分析报告的基础上补充生成未覆盖测试点的用例
           已经生成的用例:
            {test_cases}
           覆盖率分析报告:
            {test_case_coverage_report} 
       如果没有提供已经编写的测试用例则根据测试点直接生成：

       输出的用例，包含测试用例的八要素，：
           用例编号(case_id)
           用例名称(case_name)
           优先级(priority) 
           前置步骤(preconditions)
           测试步骤(test_steps) 
           输入数据(test_data) 
           预期结果(expected_result)
           实际结果(actual_result)
       要以json格式输出，输出格式要求为：
           [
               {{
                   "case_id": "用例编号",
                   "case_name": "用例名称",
                   "priority": "优先级",
                   "preconditions": "前置步骤",
                   "test_steps": "测试步骤",
                   "test_data": "输入数据",
                   "expected_result": "预期结果",
                   "actual_result": "实际结果"
               }},
               ...
           ]
            """
)
