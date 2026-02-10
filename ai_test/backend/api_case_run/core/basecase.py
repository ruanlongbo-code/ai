import json
import re
import traceback
from numbers import Number
import jmespath
from requests.sessions import Session
from requests_toolbelt import MultipartEncoder
from api_case_run.core.database_client import DBClient
from api_case_run.core.test_result import TestResult, APIRequestInfo
from api_case_run import global_tools as global_function

"""
定义单条接口测试用例执行的核心逻辑
    1、检查是否有前置依赖接口
        - 有的话就先请求前置依赖的接口，提取依赖字段进行保存
         遍历出来每一个接口
            - 前置脚本执行
            - 替换用例参数中的变量引用
            - 发送请求（request）
            - 后置脚本执行
            - 后面接口依赖字段，数据的提取       
    2、执行用例前置脚本
    3、替换用例参数中的变量引用(依赖字段，测试环境中的数据，base_url)
    4、发送请求（request）
    5、后置脚本执行
    6、断言预期结果和实际结果是否一致
问题点： 在执行后置脚本的时候，如何获取前置脚本中提取的变量(前后置脚本中的数据互通)
"""


class BaseTestCase:
    """定义一个通用的接口用例执行流程的类"""

    def __init__(self, case_data: dict, result: TestResult, test_env_global: dict, db: DBClient):
        """
        :param case_data: 用例数据
        :param result: 执行器对象
        :param test_env_global: 测试环境数据
        """
        self.case_data = case_data
        self.result = result
        self.test_env_global = test_env_global
        # 创建一个接口请求对象
        self.http = Session()
        self.db = db

    def execute_preconditions(self):
        """执行前置依赖接口"""
        self.result.add_info_log("开始检测用例的前置依赖接口")
        if self.case_data.get("preconditions"):
            # 遍历每一个接口，然后执行请求，提取数据。
            for api in self.case_data.get("preconditions"):
                api_info = api.get("request")
                # 执行依赖接口中的前置脚本
                self.execute_setup_script(api_info)
                # 替换变量
                api_info = self.replace_variables(api_info)
                # 发送请求
                response = self.request_api(api_info)
                # 执行依赖接口中的后置脚本
                self.execute_teardown_script(response)
                # 依赖数据提取的方法
                self.extract_data(api, response)
            self.result.add_info_log("前置依赖接口执行完毕")
        else:
            self.result.add_info_log("没有前置依赖接口")

    def _run_script(self, api_info):
        """执行前后置脚本的方法"""
        # 对相关的操作进行重命名（方便编辑前后置脚本）
        test = self
        db = self.db

        setup_script = api_info.get("setup_script", '')
        if setup_script:
            self.result.add_info_log(f"开始执行用例的前置脚本:\n{setup_script}")
            exec(setup_script)
        response = yield
        teardown_script = api_info.get("teardown_script", '')
        if teardown_script:
            self.result.add_info_log(f"开始执行用例的后置脚本:\n{teardown_script}")
            exec(teardown_script)

    def execute_setup_script(self, api_info):
        """执行用例前置脚本"""
        # 获取用例中的前置脚本
        # 创建一个脚本执行器
        self.script_executor = self._run_script(api_info)
        # 执行前置脚本
        next(self.script_executor)

    def execute_teardown_script(self, response):
        """执行用例后置脚本"""
        try:
            # 执行后置脚本
            self.script_executor.send(response)
        except StopIteration:
            pass
        finally:
            # 删除脚本执行器
            del self.script_executor

    def replace_variables(self, api_info: dict) -> dict:
        """替换用例参数中的变量引用"""
        self.result.add_info_log("开始替换用例参数中的变量引用")
        # 定义变量替换的正则表达式的规则
        pattern = r"\${{(.+?)}}"
        # 有可能需要替换处理的字段
        data = str({
            "url": api_info.get("url"),
            "base_url": api_info.get("base_url"),
            "headers": api_info.get("headers"),
            "params": api_info.get("params"),
            "body": api_info.get("body"),
            "files": api_info.get("files"),
        })

        print("替换之前的数据为：", api_info)
        # 写一个正则表达式，进行循环匹配
        while re.search(pattern, data):
            match = re.search(pattern, data)
            pattern_content = match.group()
            key = match.group(1)
            value = self.test_env_global.get(key, None)
            # ==================判断value值的类型=======================
            if value:
                self.result.add_info_log(
                    f"正则匹配到：{pattern_content},需要替换为测试环境数据中的变量：{key},变量值为：{value}")
                # 如果替换的值为数值
                if isinstance(value, Number):
                    s = data.find(pattern_content)
                    new_pattern_content = data[s - 1:s + len(pattern_content) + 1]
                    print("数值类型，需要替换的内容：", new_pattern_content)
                    data = data.replace(new_pattern_content, str(value))
                # 如果替换的值为列表或者字典
                elif isinstance(value, list) or isinstance(value, dict):
                    s = data.find(pattern_content)
                    new_pattern_content = data[s - 1:s + len(pattern_content) + 1]
                    data = data.replace(new_pattern_content, str(value))
                # 如果替换的字符串中有单引号
                elif isinstance(value, str) and "'" in value:
                    data = data.replace(pattern_content, value.replace("'", '"'))
                else:
                    data = data.replace(pattern_content, str(value))
            else:
                self.result.add_info_log(
                    f"正则匹配到：{pattern_content},没有找到对应的测试环境数据中的变量：{key},给变量设置默认值为空字符串")
                data = data.replace(pattern_content, "")
        # 数据替换完之后，需要重新转换为字典
        new_data = eval(data)
        # 更新api_info中被替换的字段
        api_info.update(new_data)
        # 返回数据
        return api_info

    def release_assertions(self, assertions: dict) -> dict:
        self.result.add_info_log("开始替换用例参数中的变量引用")
        # 定义变量替换的正则表达式的规则
        pattern = r"\${{(.+?)}}"
        data = str(assertions)
        # 写一个正则表达式，进行循环匹配
        while re.search(pattern, data):
            match = re.search(pattern, data)
            pattern_content = match.group()
            key = match.group(1)
            value = self.test_env_global.get(key, None)
            # ==================判断value值的类型=======================
            if value:
                self.result.add_info_log(
                    f"正则匹配到：{pattern_content},需要替换为测试环境数据中的变量：{key},变量值为：{value}")
                # 如果替换的值为数值
                if isinstance(value, Number):
                    s = data.find(pattern_content)
                    new_pattern_content = data[s - 1:s + len(pattern_content) + 1]
                    print("数值类型，需要替换的内容：", new_pattern_content)
                    data = data.replace(new_pattern_content, str(value))
                # 如果替换的值为列表或者字典
                elif isinstance(value, list) or isinstance(value, dict):
                    s = data.find(pattern_content)
                    new_pattern_content = data[s - 1:s + len(pattern_content) + 1]
                    data = data.replace(new_pattern_content, str(value))
                # 如果替换的字符串中有单引号
                elif isinstance(value, str) and "'" in value:
                    data = data.replace(pattern_content, value.replace("'", '"'))
                else:
                    data = data.replace(pattern_content, str(value))
            else:
                self.result.add_info_log(
                    f"正则匹配到：{pattern_content},没有找到对应的测试环境数据中的变量：{key},给变量设置默认值为空字符串")
                data = data.replace(pattern_content, "")
        # 数据替换完之后，需要重新转换为字典
        new_data = eval(data)
        return new_data

    def request_api(self, api_info):
        """请求接口"""
        # 创建一个保存请求信息的对象
        api_request_info = APIRequestInfo(interface_id=api_info.get("interface_id", None))
        # 获取请求方法
        method = api_info.get('method', 'GET').upper()
        api_request_info.method = method
        # 获取完整的请求地址
        url = api_info.get('base_url', self.test_env_global.get('base_url', "")) + api_info.get('url')
        api_request_info.url = url
        # 获取请求头
        headers = api_info.get('headers', {})  # content-type 指定请求体的参数格式
        api_request_info.headers = headers
        # 获取查询参数
        params = api_info.get('params', {})
        api_request_info.params = params
        # 获取请求体参数（表单参数 | json参数 | xml文件上传的参数）
        body = api_info.get('body', {})

        # 获取上传的文件
        files = api_info.get('files', {})
        # 获取请求体的类型
        content_type = headers.get('Content-Type', '').lower()
        self.result.add_info_log(
            f"开始发送请求,请求地址为：{url}请求方法为：{method}，请求头为：{headers}，请求参数为：{params}，请求体参数为：{body}")
        api_request_info.body = body
        try:
            if content_type.startswith('application/json'):
                # json参数
                response = self.http.request(method=method, url=url, headers=headers, params=params, json=body)
            elif content_type.startswith('application/xml'):
                response = self.http.request(method=method, url=url, headers=headers, params=params, data=body)
            elif content_type.startswith('application/x-www-form-urlencoded'):
                # 表单参数
                response = self.http.request(method=method, url=url, headers=headers, params=params, data=body)
            elif content_type.startswith('multipart/form-data'):
                # 文件上传参数（等会儿需要额处理）
                new_files = {}
                # 处理文件上传参数
                for key, value in files.items():
                    if len(value) == 3:
                        # 获取上传的文件名
                        file_name = value[0]
                        # 获取上传的文件内容
                        file_content = open(value[1], 'rb')
                        file_type = value[2]
                        new_files[key] = (file_name, file_content, file_type)
                    else:
                        new_files[key] = value
                        # 对文件上传的参数进行编码处理
                m = MultipartEncoder(fields=new_files)
                headers['Content-Type'] = m.content_type
                response = self.http.request(method=method, url=url, headers=headers, params=params, data=m)
                api_request_info.body = m
            else:
                # 默认为表单参数
                response = self.http.request(method=method, url=url, headers=headers, params=params, data=body)
        except Exception as e:
            api_request_info.status_code = None
            api_request_info.response_body = None
            self.result.api_requests_info.append(api_request_info)
            self.result.add_error_log(f"请求接口异常，异常信息为：{e}")
            self.result.traceback = traceback.format_exc()
            raise e
        else:
            api_request_info.status_code = response.status_code
            # 判断响应体是否为json
            if response.headers.get('Content-Type', '').lower().startswith('application/json'):
                # 记录响应状态码
                api_request_info.response_body = response.json()
                self.result.add_info_log(
                    f"获取到接口的请求响应：\n响应状态码为：{response.status_code}\n响应结果为：{response.json()}\n响应头为：{response.headers}，")
            else:
                api_request_info.response_body = response.text
                self.result.add_info_log(
                    f"获取到接口的请求响应：\n响应状态码为：{response.status_code}\n响应结果为：{response.text}\n响应头为：{response.headers}，")
            self.result.api_requests_info.append(api_request_info)
            return response

    def assert_result(self, assertions, response):
        """断言用例结果"""
        self.result.add_info_log("开始断言用例结果")
        # 替换断言字段中的变量
        if not assertions:
            self.result.add_info_log("assert中没有需要断言的数据")
        # 断言的逻辑
        for item in assertions.get("response"):
            type_ = item.get("type")
            # 实际结果的提取表达式
            field = item.get("field")
            # 预期结果的值
            expected = item.get("expected")
            # 在日志中记录断言信息
            self.result.add_info_log(f"正在断言：比较类型为：{type_}，实际结果为：{field}的值，预期结果为：{expected}")
            # 判断是否是断言http状态码
            if type_ == "http_code":
                assert int(
                    expected) == response.status_code, f"http状态码不相等，预期结果为：{expected}，实际结果为：{response.status_code}"
            elif type_ == "equal":
                # 提取实际结果的值
                actual = jmespath.search(field, response.json())
                assert expected == actual, f"{field}的值不相等，预期结果为：{expected}，实际结果为：{actual}"
            elif type_ == "not_null":
                # 提取实际结果的值
                actual = jmespath.search(field, response.json())
                assert actual is not None, f"{field}的值不能为空"
            # 更多的断言方式的支持，可以在此处扩展

    # 依赖数据提取的方法
    def extract_data(self, api_info, response):
        """提取数据"""
        self.result.add_info_log("开始提取数据")
        if api_info.get("extract", None):
            for var_name, jmes_path in api_info.get("extract"):
                # 通过jmespath提取数据
                var_value = jmespath.search(jmes_path, response.json())
                # 将提取出来的值保存到test_env_global中
                self.test_env_global[var_name] = var_value
                self.result.add_info_log(f"提取数据成功，变量名称为：{var_name}，变量值为：{var_value}")
        else:
            self.result.add_info_log("extract中没有需要提取的数据")

    def save_test_env_variables(self, name, value):
        """保存环境变量"""
        self.result.add_info_log(f"开始保存环境变量:变量名称为：{name}，变量值为：{value}")
        self.test_env_global[name] = value

    def get_test_env_variables(self, name):
        """获取环境变量"""
        self.result.add_info_log("开始获取环境变量")
        return self.test_env_global.get(name)

    def json_extract(self, expr, response):
        """
        使用jsonpath提取数据
        :param response: 响应对象
        :param expr: jsonpath表达式
        :return: 提取结果
        """
        value = jmespath.search(expr, response.json())
        self.result.add_info_log(f"JSON提取数据: 表达式={expr}, 结果={value}")
        return value

    def re_extract(self, string, pattern):
        """
        使用正则表达式提取数据
        :param string: 要匹配的字符串
        :param pattern: 正则表达式
        :return: 提取结果
        """
        match = re.search(pattern, string)
        value = match.group(1) if match else None
        self.result.add_info_log(f"正则提取数据: 表达式={pattern}, 结果={value}")
        return value

    def run(self):
        """用例执行的主入口函数"""
        # 执行前置依赖接口
        self.execute_preconditions()
        # 获取用例数据的requests字段信息
        case_api_info = self.case_data.get("request")
        # 执行用例前置脚本
        self.execute_setup_script(case_api_info)
        # 替换用例参数中的变量引用
        case_api_info = self.replace_variables(case_api_info)
        # 请求发送
        response = self.request_api(case_api_info)
        # 后置脚本执行
        self.execute_teardown_script(response)
        # 替换断言中的变量引用
        assertions = self.release_assertions(self.case_data.get("assertions", {}))
        # 断言用例执行的结果
        self.assert_result(assertions, response)
