"""
获取用例执行的前后置脚本中可用的函数列表
    输出
    [
        {
        "name":"函数名称"，
        "params":函数参,
        "desc":"函数的描述"
        },
        {
        "name":"函数名称"，
        "params":函数参,
        "desc":"函数的描述"
        }
    ]
"""
from typing import Dict, Any, List
import inspect


def get_module_functions(module_name: object) -> List[Dict[str, Any]]:
    """
    获取模块中的可用函数列表
    :param module_name: 需要检测的模块
    :return:
    """
    functions = []
    # 获取模块中的所有函数
    function_list = inspect.getmembers(module_name, predicate=inspect.isfunction)
    for name, func_obj in function_list:
        # 获取函数的参数信息
        params = inspect.signature(func_obj).parameters
        # 获取函数的文档描述
        decs = inspect.getdoc(func_obj)
        functions.append({
            "name": name,
            "params": list(params.keys()),
            "desc": decs
        })
    return functions


if __name__ == '__main__':
    from api_case_run import global_tools

    result = get_module_functions(global_tools)
