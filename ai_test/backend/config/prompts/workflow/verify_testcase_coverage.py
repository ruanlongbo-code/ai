from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=["test_cases", "test_point"],
    template="""
               你是一位资深测试工程师，请根据用户下面提供的测试点和测试用例，去分析测试用例是否覆盖了所有的测试点
                   已经生成的测试用例：
                   {test_cases}
                   需要测试的测试点：
                   {test_point}
             输入要求：
               如果全部覆盖则直接返回：已覆盖全部测试点
               如果没有全部覆盖则返回测试点覆盖分析报告 
               """
)
