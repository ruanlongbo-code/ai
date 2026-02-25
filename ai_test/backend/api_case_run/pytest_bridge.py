"""
pytest 桥接层：将数据库中的 API 测试用例动态转换为 pytest 测试函数
并通过 allure-pytest 生成专业测试报告

核心架构：
  1. PytestCaseLoader  - 从数据库加载用例并转换为 pytest 可识别的数据结构
  2. conftest.py 动态生成 - 注入环境变量、数据库连接等 fixture
  3. test_api_*.py 动态生成 - 基于用例数据生成 pytest 测试文件
  4. PytestRunner  - 调用 pytest.main() 执行并收集 allure 结果
"""
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PytestCaseData:
    """pytest 用例数据结构"""
    case_id: int
    name: str
    description: str = ""
    interface_name: str = ""
    suite_name: str = ""
    preconditions: list = field(default_factory=list)
    request: dict = field(default_factory=dict)
    assertions: dict = field(default_factory=dict)
    skip: bool = False


@dataclass
class PytestRunConfig:
    """pytest 运行配置"""
    env_vars: dict = field(default_factory=dict)
    db_configs: list = field(default_factory=list)
    parallel: bool = False
    max_workers: int = 4
    reruns: int = 0
    timeout: int = 30
    markers: list = field(default_factory=list)


class PytestBridge:
    """
    pytest 桥接器：核心执行引擎

    将平台用例 → pytest 测试文件 → pytest 执行 → allure 报告
    """

    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="ai_test_pytest_")
        self.allure_results_dir = os.path.join(self.work_dir, "allure-results")
        self.allure_report_dir = os.path.join(self.work_dir, "allure-report")
        self.test_dir = os.path.join(self.work_dir, "tests")
        os.makedirs(self.test_dir, exist_ok=True)
        os.makedirs(self.allure_results_dir, exist_ok=True)

    def generate_conftest(self, config: PytestRunConfig) -> str:
        """
        动态生成 conftest.py
        注入 fixture：环境变量、数据库连接、请求 Session 等
        """
        env_vars_json = json.dumps(config.env_vars, ensure_ascii=False, indent=4)
        db_configs_json = json.dumps(config.db_configs, ensure_ascii=False, indent=4)

        conftest_content = f'''# Auto-generated conftest.py by AI Test Platform
import pytest
import json
import re
import sys
import os
import time
from numbers import Number

import allure
import jmespath
import requests
from requests.sessions import Session
from requests_toolbelt import MultipartEncoder

# ============================ 全局 fixture ============================

@pytest.fixture(scope="session")
def env_vars():
    """测试环境变量 fixture"""
    return {env_vars_json}


@pytest.fixture(scope="session")
def db_configs():
    """数据库配置 fixture"""
    return {db_configs_json}


@pytest.fixture(scope="session")
def base_url(env_vars):
    """基础 URL fixture"""
    return env_vars.get("base_url", "")


@pytest.fixture(scope="function")
def http_session():
    """每个用例独立的 HTTP Session"""
    session = Session()
    yield session
    session.close()


# ============================ 通用工具函数 ============================

def replace_variables(data_str: str, env_vars: dict) -> str:
    """替换变量引用 ${{variable_name}}"""
    pattern = r"\\$\\{{\\{{(.+?)\\}}\\}}"
    while re.search(pattern, data_str):
        match = re.search(pattern, data_str)
        key = match.group(1)
        value = env_vars.get(key, "")
        pattern_content = match.group()
        if isinstance(value, Number) and not isinstance(value, bool):
            s = data_str.find(pattern_content)
            new_pattern_content = data_str[s - 1:s + len(pattern_content) + 1]
            data_str = data_str.replace(new_pattern_content, str(value))
        elif isinstance(value, (list, dict)):
            s = data_str.find(pattern_content)
            new_pattern_content = data_str[s - 1:s + len(pattern_content) + 1]
            data_str = data_str.replace(new_pattern_content, str(value))
        elif isinstance(value, str) and "\\'" in value:
            data_str = data_str.replace(pattern_content, value.replace("\\'", '"'))
        else:
            data_str = data_str.replace(pattern_content, str(value))
    return data_str


def send_request(session: Session, api_info: dict, env_vars: dict) -> requests.Response:
    """发送 HTTP 请求"""
    # 替换变量
    data_str = str({{
        "url": api_info.get("url", ""),
        "base_url": api_info.get("base_url", env_vars.get("base_url", "")),
        "headers": api_info.get("headers", {{}}),
        "params": api_info.get("params", {{}}),
        "body": api_info.get("body", {{}}),
        "files": api_info.get("files", {{}}),
    }})
    data_str = replace_variables(data_str, env_vars)
    replaced_data = eval(data_str)

    method = api_info.get("method", "GET").upper()
    url = replaced_data.get("base_url", "") + replaced_data.get("url", "")
    headers = replaced_data.get("headers", {{}})
    params = replaced_data.get("params", {{}})
    body = replaced_data.get("body", {{}})
    files = replaced_data.get("files", {{}})

    content_type = headers.get("Content-Type", "").lower()

    with allure.step(f"发送 {{method}} 请求: {{url}}"):
        allure.attach(json.dumps(headers, ensure_ascii=False, indent=2), "请求头", allure.attachment_type.JSON)
        if params:
            allure.attach(json.dumps(params, ensure_ascii=False, indent=2), "查询参数", allure.attachment_type.JSON)
        if body:
            allure.attach(json.dumps(body, ensure_ascii=False, indent=2), "请求体", allure.attachment_type.JSON)

        if content_type.startswith("application/json"):
            response = session.request(method=method, url=url, headers=headers, params=params, json=body)
        elif content_type.startswith("multipart/form-data"):
            new_files = {{}}
            for key, value in files.items():
                if isinstance(value, list) and len(value) == 3:
                    new_files[key] = (value[0], open(value[1], "rb"), value[2])
                else:
                    new_files[key] = value
            m = MultipartEncoder(fields=new_files)
            headers["Content-Type"] = m.content_type
            response = session.request(method=method, url=url, headers=headers, params=params, data=m)
        else:
            response = session.request(method=method, url=url, headers=headers, params=params, data=body)

        # 记录响应
        allure.attach(str(response.status_code), "状态码", allure.attachment_type.TEXT)
        try:
            allure.attach(
                json.dumps(response.json(), ensure_ascii=False, indent=2),
                "响应体", allure.attachment_type.JSON
            )
        except Exception:
            allure.attach(response.text[:2000], "响应体", allure.attachment_type.TEXT)

    return response


def run_assertions(assertions: dict, response: requests.Response, env_vars: dict):
    """执行断言"""
    if not assertions or not assertions.get("response"):
        return

    # 替换断言中的变量
    assertion_str = str(assertions)
    assertion_str = replace_variables(assertion_str, env_vars)
    assertions = eval(assertion_str)

    for item in assertions.get("response", []):
        type_ = item.get("type")
        field_path = item.get("field", "")
        expected = item.get("expected")

        with allure.step(f"断言: {{type_}} | field={{field_path}} | expected={{expected}}"):
            if type_ == "http_code":
                assert int(expected) == response.status_code, \\
                    f"HTTP状态码不匹配: 预期 {{expected}}, 实际 {{response.status_code}}"
            elif type_ == "equal":
                actual = jmespath.search(field_path, response.json())
                assert expected == actual, \\
                    f"{{field_path}} 值不相等: 预期 {{expected}}, 实际 {{actual}}"
            elif type_ == "not_null":
                actual = jmespath.search(field_path, response.json())
                assert actual is not None, f"{{field_path}} 的值不能为空, 实际为 None"
            elif type_ == "contains":
                actual = jmespath.search(field_path, response.json())
                assert expected in str(actual), \\
                    f"{{field_path}} 不包含 {{expected}}, 实际值: {{actual}}"
            elif type_ == "not_equal":
                actual = jmespath.search(field_path, response.json())
                assert expected != actual, \\
                    f"{{field_path}} 不应等于 {{expected}}, 但实际相等"
            elif type_ == "greater_than":
                actual = jmespath.search(field_path, response.json())
                assert float(actual) > float(expected), \\
                    f"{{field_path}} 应大于 {{expected}}, 实际 {{actual}}"
            elif type_ == "less_than":
                actual = jmespath.search(field_path, response.json())
                assert float(actual) < float(expected), \\
                    f"{{field_path}} 应小于 {{expected}}, 实际 {{actual}}"
            elif type_ == "length_equal":
                actual = jmespath.search(field_path, response.json())
                assert len(actual) == int(expected), \\
                    f"{{field_path}} 长度应为 {{expected}}, 实际 {{len(actual)}}"
            elif type_ == "type_check":
                actual = jmespath.search(field_path, response.json())
                type_map = {{"int": int, "str": str, "float": float, "list": list, "dict": dict, "bool": bool}}
                expected_type = type_map.get(expected, str)
                assert isinstance(actual, expected_type), \\
                    f"{{field_path}} 类型应为 {{expected}}, 实际 {{type(actual).__name__}}"
'''

        conftest_path = os.path.join(self.test_dir, "conftest.py")
        with open(conftest_path, "w", encoding="utf-8") as f:
            f.write(conftest_content)

        return conftest_path

    def generate_test_file(self, cases: List[PytestCaseData], suite_name: str = "default") -> str:
        """
        将用例数据生成为 pytest 测试文件
        每个 PytestCaseData 生成一个 test_ 函数
        """
        safe_suite_name = "".join(c if c.isalnum() or c == "_" else "_" for c in suite_name)
        test_file_name = f"test_api_{safe_suite_name}.py"

        lines = [
            "# Auto-generated by AI Test Platform - pytest bridge",
            "import pytest",
            "import json",
            "import allure",
            "from conftest import send_request, run_assertions",
            "",
            "",
        ]

        for case in cases:
            func_name = f"test_case_{case.case_id}"
            case_json = json.dumps({
                "id": case.case_id,
                "name": case.name,
                "preconditions": case.preconditions,
                "request": case.request,
                "assertions": case.assertions,
            }, ensure_ascii=False)

            # 生成 allure 装饰器
            lines.append(f'@allure.epic("接口自动化测试")')
            lines.append(f'@allure.feature("{suite_name}")')
            lines.append(f'@allure.story("{case.interface_name or case.name}")')
            lines.append(f'@allure.title("{case.name}")')
            if case.description:
                lines.append(f'@allure.description("""{case.description}""")')
            if case.skip:
                lines.append(f'@pytest.mark.skip(reason="用例被标记为跳过")')

            lines.append(f"def {func_name}(http_session, env_vars):")
            lines.append(f"    '''用例ID: {case.case_id} - {case.name}'''")
            lines.append(f"    case_data = json.loads('''{case_json}''')")
            lines.append(f"")

            # 前置依赖接口
            lines.append(f"    # 执行前置依赖接口")
            lines.append(f"    preconditions = case_data.get('preconditions', [])")
            lines.append(f"    if preconditions:")
            lines.append(f"        for pre_api in preconditions:")
            lines.append(f"            with allure.step(f\"前置接口: {{pre_api.get('name', '未命名')}}\"):")
            lines.append(f"                pre_request = pre_api.get('request', {{}})")
            lines.append(f"                pre_response = send_request(http_session, pre_request, env_vars)")
            lines.append(f"                # 提取依赖数据")
            lines.append(f"                for var_name, jmes_path in pre_api.get('extract', []):")
            lines.append(f"                    import jmespath")
            lines.append(f"                    value = jmespath.search(jmes_path, pre_response.json())")
            lines.append(f"                    env_vars[var_name] = value")
            lines.append(f"                    allure.attach(str(value), f'提取变量: {{var_name}}', allure.attachment_type.TEXT)")
            lines.append(f"")

            # 主请求
            lines.append(f"    # 执行主请求")
            lines.append(f"    with allure.step('执行主请求'):")
            lines.append(f"        main_request = case_data.get('request', {{}})")
            lines.append(f"        response = send_request(http_session, main_request, env_vars)")
            lines.append(f"")

            # 断言
            lines.append(f"    # 执行断言")
            lines.append(f"    with allure.step('断言验证'):")
            lines.append(f"        run_assertions(case_data.get('assertions', {{}}), response, env_vars)")
            lines.append(f"")
            lines.append(f"")

        test_file_path = os.path.join(self.test_dir, test_file_name)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return test_file_path

    def generate_pytest_ini(self, config: PytestRunConfig) -> str:
        """生成 pytest.ini 配置文件"""
        markers = "\n    ".join(config.markers) if config.markers else ""

        ini_content = f"""[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --alluredir={self.allure_results_dir}
{f'markers = {markers}' if markers else ''}
"""
        ini_path = os.path.join(self.work_dir, "pytest.ini")
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(ini_content)
        return ini_path

    def run(self, config: PytestRunConfig, cases: List[PytestCaseData],
            suite_name: str = "default") -> Dict[str, Any]:
        """
        完整执行流程：
        1. 生成 conftest.py + test_*.py + pytest.ini
        2. 调用 pytest 执行
        3. 生成 allure 报告
        4. 收集执行结果
        """
        start_time = time.time()

        # 1. 生成文件
        self.generate_conftest(config)
        self.generate_test_file(cases, suite_name)
        self.generate_pytest_ini(config)

        # 生成 __init__.py
        init_path = os.path.join(self.test_dir, "__init__.py")
        with open(init_path, "w") as f:
            f.write("")

        # 2. 执行 pytest
        pytest_args = [
            "python", "-m", "pytest",
            self.test_dir,
            "-v",
            "--tb=short",
            f"--alluredir={self.allure_results_dir}",
            "--no-header",
        ]

        if config.timeout:
            pytest_args.extend(["--timeout", str(config.timeout)])

        if config.reruns:
            pytest_args.extend(["--reruns", str(config.reruns)])

        if config.parallel and config.max_workers > 1:
            pytest_args.extend(["-n", str(config.max_workers)])

        env = os.environ.copy()
        env["PYTHONPATH"] = self.test_dir

        process = subprocess.run(
            pytest_args,
            capture_output=True,
            text=True,
            cwd=self.work_dir,
            env=env,
            timeout=300,  # 5 分钟超时
        )

        # 3. 尝试生成 allure HTML 报告
        allure_html_generated = False
        try:
            allure_cmd = shutil.which("allure")
            if allure_cmd:
                subprocess.run(
                    [allure_cmd, "generate", self.allure_results_dir,
                     "-o", self.allure_report_dir, "--clean"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                allure_html_generated = os.path.exists(
                    os.path.join(self.allure_report_dir, "index.html")
                )
        except Exception:
            pass

        # 4. 解析执行结果
        result = self._parse_results(process, start_time)
        result["allure_results_dir"] = self.allure_results_dir
        result["allure_report_dir"] = self.allure_report_dir if allure_html_generated else None
        result["work_dir"] = self.work_dir

        return result

    def _parse_results(self, process: subprocess.CompletedProcess, start_time: float) -> Dict[str, Any]:
        """解析 pytest 执行结果"""
        end_time = time.time()
        duration = end_time - start_time

        stdout = process.stdout or ""
        stderr = process.stderr or ""

        # 解析 pytest 输出统计
        total = 0
        passed = 0
        failed = 0
        error = 0
        skipped = 0

        for line in stdout.split("\n"):
            line = line.strip()
            # 解析如 "5 passed, 2 failed, 1 skipped in 3.45s"
            if "passed" in line or "failed" in line or "error" in line:
                import re
                nums = re.findall(r"(\d+)\s+(passed|failed|error|skipped|warnings?)", line)
                for num, status in nums:
                    if status == "passed":
                        passed = int(num)
                    elif status == "failed":
                        failed = int(num)
                    elif status == "error":
                        error = int(num)
                    elif status == "skipped":
                        skipped = int(num)
                if any(nums):
                    total = passed + failed + error + skipped

        # 如果没能解析到数值，尝试从 allure 结果目录解析
        if total == 0:
            total, passed, failed, error, skipped = self._parse_allure_results()

        pass_rate = round(passed / max(total, 1) * 100, 1)

        return {
            "status": "passed" if (failed == 0 and error == 0 and total > 0) else "failed",
            "exit_code": process.returncode,
            "total": total,
            "passed": passed,
            "failed": failed,
            "error": error,
            "skipped": skipped,
            "pass_rate": pass_rate,
            "duration": round(duration, 2),
            "stdout": stdout,
            "stderr": stderr,
        }

    def _parse_allure_results(self):
        """从 allure results JSON 文件解析结果"""
        total = passed = failed = error = skipped = 0
        try:
            for fname in os.listdir(self.allure_results_dir):
                if fname.endswith("-result.json"):
                    filepath = os.path.join(self.allure_results_dir, fname)
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    status = data.get("status", "")
                    total += 1
                    if status == "passed":
                        passed += 1
                    elif status == "failed":
                        failed += 1
                    elif status == "broken":
                        error += 1
                    elif status == "skipped":
                        skipped += 1
        except Exception:
            pass
        return total, passed, failed, error, skipped

    def cleanup(self):
        """清理工作目录"""
        try:
            if os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir, ignore_errors=True)
        except Exception:
            pass
