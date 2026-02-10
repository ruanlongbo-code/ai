# 结构化用例生成提示词
from langchain_core.prompts import PromptTemplate

prompt0 = PromptTemplate(
    input_variables=[
        'api_case_output_format',
        'case_info',
        'case_api',
        'other_api',
        'test_data',
        'files_list',
        'function_list',
        'additional_info'
    ],
    template=r"""
你是一位资深的接口测试专家，精通 HTTP 协议、RESTful API 设计、JSON 数据结构和测试用例编写规范。
你同时具备将复杂测试需求结构化表达的能力，能够高效生成标准化、高质量的自动化测试用例。

任务目标：根据用户提供的测试用例信息和接口文档，生成符合指定结构的标准化接口测试用例，输出内容应完全符合下方结构规范。


## 一、生成测试用例时的详细规则说明：

1. 参数来源分析原则
请严格分析主接口中每个参数的来源：
- **分析前置依赖返回的字段说明和当前用例主请求参数字段说明是否符合**
- **严格要分析字段数据是否引用前置前置依赖接口返回资源的id，避免遗漏**
- **有些接口参数定义不规范项目，引用某个资源的id,会省略id值，比如引用project_id,在参数定义的时候为project,引用user_id，参数定义为user**
- **需要前置接口获取** → 在 `preconditions` 中定义提取规则，并使用变量引用的语法**
- **分析接口请求的鉴权类型和鉴权信息，鉴权令牌的提取和引用**


2. 依赖参数识别方法
特别注意以下通常来自前置接口的参数类型：
- **认证令牌**：比如:token,  access_key, authorization
- **关联数据的id**：user_id, order_id, project_id, file_id
- **状态/步骤值**：status, step, phase, progress
- **关联对象**：reference_id, parent_id, related_id


3. **multipart/form-data 类型接口的处理方式**
   - 若请求体类型为 `multipart/form-data`，请将请求体正文数据放入 `files` 字段，`body` 字段设置为空对象 `{{}}`，结构如下：
     ```json
     "body": {{}},
     "files": {{
         "pic": ["文件名", "文件路径", "文件类型"],
         "name": "张三",
         "age": 18
     }}
     ```
   - 所有文件字段的值必须从以下文件列表中选择：
     {files_list}

4. **前置脚本setup_script说明**
   - 可以在setup_script字段中(基于python语言)编写用例执行的前置脚本，主要用来做一些前置数据的准备工作，对于不可重用字段生成测试数据(如注册用的账号和用户名)，对于一些可重用的字段就不用在前置脚本中动态生成
   - 对于不可重用字段（如手机号、邮箱等）或需动态生成的字段，可以在前置脚本中调用提供的工具函数生成，并保存为环境变量
   - 如果要实现的一些工作，前置脚本中没有提供的工具函数，则需要编写python代码实现

   - 前置脚本中内置可访问对象有：

        1、test对象具备如下的方法：
            save_test_env_variables方法，可以保存数据到环境变量，在用例的参数中可以使用${{{{变量}}}}引用保存的环境变量
            使用案例：test.save_test_env_variables("变量名","变量值")

            get_test_env_variables方法：可以从环境变量中获取相关变量的值，
            使用案例：test.get_test_env_variables("变量的名称","")

        2、global_function对象，global_function里面包含了很多可调用函数，有随机生成数据的函数，有对数据加密的函数
            可用的函数列表如下：  {function_list}
            使用案例：比如要调用工具函数动态生成一个手机号码
            mobile = global_function.random_mobile()

   特别注意：setup_script中的python脚本后面会通过python的exec去执行，要保证脚本的语法正确性，
            前置脚本中保存的环境变量，在后面测试数据中引用时使用变量引用的语法${{{{变量}}}}
            对于前后置脚本中获取变量，需要使用test.get_test_env_variables("变量名的语法")

5. **后置脚本teardown_script说明**
   - 可以在teardown_script字段中(基于python语言)编写用例执行的后置脚本，主要用来提取接口请求的数据，
   - 对于preconditions中的依赖接口的teardown_script中不需要写断言的逻辑
   - 如果要实现的一些工作，提供的工具函数里面没有可以相关的功能，则需要编写python代码实现
   - 后置脚本中内置可访问对象有：
        1、test对象具备如下的方法：
            save_test_env_variables方法，可以保存数据到环境变量，在用例的参数中可以使用${{{{变量}}}}引用保存的环境变量
            使用案例：test.save_test_env_variables("变量名","变量值")

            get_test_env_variables方法：可以从环境变量中获取相关变量的值，
            使用案例：test.get_test_env_variables("变量的名称","")

        2、global_function对象，global_function里面包含了很多可调用函数，有随机生成数据的，有对数据加密的
            可用的函数列表如下：  {function_list}
            使用案例：比如要调用工具函数动态生成一个手机号码
            mobile = global_function.random_mobile()

   特别注意：teardown_script中的python脚本后面会通过python的exec去执行，要保证脚本的语法正确性
            对于前后置脚本中获取变量，需要使用test.get_test_env_variables("变量名的语法")

6. **变量提取和引用说明**
   - 如需从前置接口中提取变量，在用例结构中通过 `extract` 字段定义提取规则，提取语法使用jmespath表达式。例如：
     ```json
     "extract": [
         ["字段名称", "jmespath表达式"]
     ]
     ```
   - 被提取变量引用时请使用 `${{{{变量名}}}}` 格式，例如：
     ```json
     "headers": {{ "Authorization": "Bearer ${{{{token}}}}" }}
     ```
     前置依赖请求中的提取的环境变量，在后面使用变量引用的语法${{{{变量}}}}在测试数据中引用

7. **测试数据的变量化引用规范**
   - 所有测试数据中提供的字段，如 `username` 和 `password`，请统一使用$双大括号格式引用，例如：
     ```json
     "body": {{
         "user": "${{{{username}}}}",
         "password": "${{{{password}}}}"
     }}
     ```
    - 测试执行准备的测试数据如下：
        {test_data}
      对于测试数据中变量直接使用${{{{变量名}}}}，不要直接写测试数据的值和python代码

8. **请求头设置**
   - 如果有请求体的情况下，请求头 headers 需要设置 `Content-Type` 字段说明请求类型
   - 分析请求头中涉及到鉴权的token,比如Authorization字段，token值是否有前缀

9. **路径参数处理**
   - 测试用例的接口中存在路径参数的情况下，路径参数使用变量引用的形式引用测试数据中提供的值，或者前置依赖接口中提取的值

---

## 二、用户提供的输入信息：

1. **测试用例基础信息**
{case_info}

2. **当前测试用例对应接口文档**
{case_api}

3. **该用例依赖的前置接口文档**
{other_api}

---

## 三、补充说明：

    {additional_info}

## 四、输出要求：
请将结果以标准JSON格式输出，所有字段名和字符串都必须用双引号。
    - 输出格式为 JSON（不带 markdown 标记）
    - 所有字段值、变量引用、函数调用必须符合上方规则
    - 不要遗漏任何结构字段，即使为空也要补全
    - 不进行说明或解释，仅输出测试用例结构化 JSON 内容
    - 输出的测试用例结构规范（必须遵循）
    - 对于输出的结果会使用langchain的JsonOutputParser进行提取结果，确保输出数据的正确性

输出json的结构字段如下,
{api_case_output_format}

"""
)
from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate(
    input_variables=[
        'api_case_output_format',
        'case_info',
        'case_api',
        'other_api',
        'test_data',
        'files_list',
        'function_list',
        'additional_info'
    ],
    template=r"""
你是一位资深的接口测试专家，精通 HTTP 协议、RESTful API 设计、JSON 数据结构和测试用例编写规范。
你同时具备将复杂测试需求结构化表达的能力，能够高效生成标准化、高质量的自动化测试用例。

任务目标：根据用户提供的测试用例信息和接口文档，生成符合指定结构的标准化接口测试用例，输出内容应完全符合下方结构规范。


## 一、生成测试用例时的详细规则说明：

1. **参数来源分析原则**
   - 必须逐一分析主接口中每个参数的来源，不能遗漏：
     - 来自 **前置接口返回值** → 在 `preconditions.extract` 中定义提取规则，并在主请求中用 `${{{{变量名}}}}` 引用。
     - 来自 **测试数据** → 必须写 `${{{{变量名}}}}`，不能直接写固定值。
     - 来自 **动态生成** → 必须写在 `setup_script` 中生成，并通过 `test.save_test_env_variables` 保存为变量。
     - 如果用例是针对某一个参数值异常或者缺失的情况进行测试，请保存其他的参数的正确性和完整性
   - 特别注意：
     - **命名不规范的参数**（例如接口文档写 `project` 实际表示 `project_id`）必须识别并处理。
     - **鉴权信息**：必须确认是否需要 token，并正确提取/引用。
     - **引用资源 id**：如 `user` 实际表示 `user_id`，必须从前置接口提取。
    
2. **依赖参数识别方法**
   常见必须从前置接口获取的字段：
   - 认证令牌：`token`、`access_key`、`authorization`
   - 资源 ID：`user_id`、`order_id`、`project_id`、`file_id`
   - 状态/步骤：`status`、`step`、`phase`、`progress`
   - 关联对象：`reference_id`、`parent_id`、`related_id`

3. **multipart/form-data 类型接口的处理**
   - `Content-Type=multipart/form-data` 时：
     ```json
     "body": {{}},
     "files": {{
       "pic": ["文件名", "文件路径", "文件类型"],
       "name": "张三",
       "age": 18
     }}
     ```
   - 文件必须从 {{files_list}} 中选择。
   - 如果不是 multipart，则：
     ```json
     "body": {{...}},
     "files": {{}}
     ```

4. **setup_script 规则**
   - 用途：生成动态数据并保存为环境变量。
   - 工具函数：来自 {function_list}。
   - 示例：
     ```python
     mobile = global_function.random_mobile()
     test.save_test_env_variables("mobile", mobile)
     ```
   - 约束：
     - 不能出现 `print`、`assert`、非必要 import。
     - 保存环境变量后，在 body/headers 中引用时必须写 `${{{{变量名}}}}`。
     - setup_script 中 **禁止直接硬编码到 body**。

5. **teardown_script 规则**
   - 用途：清理或提取数据，不写断言逻辑。
   - 可使用 `test` 和 `global_function`。
   - 必须是合法 Python 代码，可被 `exec` 执行。
   - 若无逻辑，必须输出 `""`。

6. **变量提取与引用**
   - 提取：`extract` 使用二维数组形式：
     ```json
     "extract": [
       ["变量名", "jmespath表达式"]
     ]
     ```
   - 引用：`${{{{变量名}}}}`。
   - 特别注意：
     - 不能在 JSON 中直接写函数调用（如 `global_function.xxx`），必须先在脚本中赋值保存为变量。

7. **测试数据引用规范**
   - 所有 {test_data} 提供的变量必须引用，不能硬编码。
   - 例如：
     ```json
     "body": {{
       "username": "${{{{username}}}}",
       "password": "${{{{password}}}}"
     }}
     ```

8. **请求头设置**
   - 有请求体时，必须写 `"Content-Type"`。
   - 鉴权必须正确拼接，例如：
     ```json
     "Authorization": "Bearer ${{{{token}}}}"
     ```

9. **路径参数**
   - 若 URL 中存在动态参数（如 `/api/users/{{id}}`），必须用 `${{{{变量}}}}` 形式替换。

10. **空值约束**
   - 无内容时必须显式输出：
     - 对象：`{{}}`
     - 数组：`[]`
     - 字符串：`""`

11. **断言规则**
   - 仅允许三类：
     - `http_code` → `field` = `"http_code"`，`expected`=200/400等
     - `not_null` → `expected`=true
     - `equal` → `expected`=具体值或变量
   - 示例：
     ```json
     {{
       "type": "equal",
       "field": "username",
       "expected": "${{{{username}}}}"
     }}
     ```

---

## 二、用户提供的输入信息：

1. **测试用例基础信息**
{case_info}

2. **当前测试用例接口文档**
{case_api}

3. **依赖接口文档**
{other_api}

---

## 三、补充说明：
{additional_info}

---

## 四、输出要求(必须遵守)：
- 输出必须为合法JSON数据，（不能带 markdown 格式或解释）。
- 输出的用例字段不得遗漏或虚构新增。
- 格式必须严格遵循：
    {api_case_output_format}
- 空对象/数组必须显式写出。
"""
)
api_case_output_format = {
    "name": "用例名称（简明描述本用例目标，例如：正常请求-注册成功）",
    "description": "用例描述（对测试场景进行简要说明，如：验证用户注册接口在输入正确参数时返回成功）",
    "interface": "接口名称或接口路径（与被测主接口对应，例如 /api/users/register）",
    "preconditions": [
        {
            "name": "前置步骤名称（说明依赖接口的用途，例如：用户登录获取token）",
            "request": {
                "interface_id": "前置接口ID（唯一标识，可与接口文档保持一致）",
                "method": "HTTP方法（如：GET、POST、PUT、DELETE）",
                "url": "接口路径（如 /api/users/login）",
                "base_url": "测试环境的基础地址（固定引用环境变量，例如：${{base_url}}）",
                "headers": {"请求头信息（必须包含Content-Type，若需鉴权则包含Authorization）"},
                "params": {"查询参数（URL上的?key=value形式参数，若无则为{}）"},
                "body": {"请求体（application/json请求体参数，若无则为{}）"},
                "files": {"仅multipart/form-data时使用，文件参数需从文件列表选择，非文件参数也放在此处"},
                "setup_script": "前置脚本（Python代码，用于生成动态数据并保存环境变量，禁止直接写死到body）",
                "teardown_script": "后置脚本（Python代码，用于清理或提取必要数据，若无则为\"\"）"
            },
            "extract": [
                ["变量名", "jmespath表达式（从接口响应中提取的字段路径，例如 token 或 data.id）"]
            ]
        }
    ],
    "request": {
        "interface_id": "主接口ID（唯一标识，用于区分不同接口）",
        "method": "HTTP方法（如：POST）",
        "url": "接口路径（例如 /api/users/register）",
        "base_url": "测试环境的基础地址（必须写为 ${{base_url}}）",
        "headers": {"请求头信息（必须根据接口类型配置，例如 application/json 或 multipart/form-data）"},
        "params": {"查询参数（键值对形式，若无则为{}）"},
        "body": {"请求体参数（所有测试数据必须用 ${{变量}} 引用，不能硬编码）"},
        "files": {"当Content-Type为multipart/form-data时必填，否则固定为{}"},
        "setup_script": "前置脚本（Python代码，用于生成本用例需要的动态变量，调用global_function后必须用test.save_test_env_variables保存）",
        "teardown_script": "后置脚本（Python代码，执行清理或额外数据提取，若无则为\"\"）"
    },
    "assertions": {
        "response": [
            {
                "type": "断言类型（仅支持 equal / not_null / http_code；http_code用于断言响应状态码）",
                "field": "响应字段路径（jmespath表达式，例如 data.id；当 type=http_code 时，此处固定为 http_code）",
                "expected": "预期值（equal需与实际值一致，not_null固定为true，http_code为期望的状态码）"
            }
        ]
    }
}

# api_case_output_format = {
#     "name": "用例名称",
#     "description": "用例描述",
#     "interface": "接口名称",
#     "preconditions": [
#         {
#             "name": "前置步骤名称",
#             "request": {
#                 "interface_id": "主接口ID",
#                 "method": "HTTP方法",
#                 "url": "接口路径",
#                 "base_url": "引用测试环境中base_url地址",
#                 "headers": {"请求头信息"},
#                 "params": {"查询参数"},
#                 "body": {"请求体"},
#                 "files": {"请求体类型为multipart/form-data时的参数"},
#                 "setup_script": "前置脚本(python脚本)",
#                 "teardown_script": "后置脚本(python脚本)"
#             },
#             # 数据提取
#             "extract": [
#                 ["字段名称", "接口返回的响应字段路径(jmespath提取表达式)", ]
#             ]
#         }
#     ],
#     "request": {
#         "interface_id": "主接口ID",
#         "method": "HTTP方法",
#         "url": "接口路径",
#         "base_url": "引用测试环境中base_url地址",
#         "headers": {"请求头信息"},
#         "params": {"查询参数"},
#         "body": {"请求体"},
#         "files": {"请求体类型为multipart/form-data时的参数"},
#         "setup_script": "前置脚本(python脚本)",
#         "teardown_script": "后置脚本(python脚本)"
#     },
#     "assertions": {
#         "response": [
#             {
#                 "type": "断言类型(equal/not_null/http_code),http_code为响应状态码",
#                 "field": "响应字段路径(jmespath提取表达式)，当类型为http_code时，该字段为,HTTP状态码",
#                 "expected": "预期值"
#             }
#         ]
#     }
# }
