"""
通过AI解析接口文档
"""
from typing import Dict, List, Optional, Any
from config.prompts.parser import api_document_parser
from config.settings import llm
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser


class Parameter(BaseModel):
    """用于提取接口参数的模型"""
    name: str = Field(description="参数名称")
    description: str = Field(description="参数描述")
    required: bool = Field(description="参数是否必填")
    type: Dict = Field(description="参数类型")


class BodyParameter(BaseModel):
    """用于提取接口参数的模型"""
    name: str = Field(description="参数名称")
    description: str = Field(description="参数描述")
    required: bool = Field(description="参数是否必填")
    type: Dict = Field(description="参数类型")
    nested_fields: Optional[List[Dict[str, Any]]] = Field(description="嵌套字段", default=None)
    array_item_fields: Optional[List[Dict[str, Any]]] = Field(description="数组项字段", default=None)


class RequestBodyModel(BaseModel):
    """请求体的模型"""
    content_type: str = Field(description="请求体类型，如 application/json，无请求体时为null")
    body: List[BodyParameter] = Field(description="请求体参数")


class ParametersModel(BaseModel):
    """用于提取接口参数的模型"""
    header: List[Parameter] = Field(description="请求头参数")
    path: List[Parameter] = Field(description="路径参数")
    query: List[Parameter] = Field(description="查询参数")


class ResponsesModel(BaseModel):
    """用于提取接口响应的模型"""
    http_code: str = Field(description="响应状态码")
    description: str = Field(description="响应描述")
    media_type: str = Field(description="响应内容类型，如 application/json")
    response_body: Dict = Field(description="响应体参数")


class InterfaceDocumentParserModel(BaseModel):
    """用于提取接口解析结果的模型"""
    path: str = Field(description="接口路径")
    method: str = Field(description="接口请求方式")
    summary: str = Field(description="接口描述")
    parameters: ParametersModel = Field(description="接口的参数分类，包含请求头、路径参数、查询参数")
    requestBody: Optional[RequestBodyModel] = Field(description="接口请求体参数", default_factory=dict)
    responses: ResponsesModel = Field(description="接口响应示例")


class AIAPIDocumentParser:
    """
    通过AI解析接口文档,将接口文档转换为特点的结构化数据
    """

    def parser(self, api_document: str):
        """
        :param api_document:
        :param document_type:
        :return:
        """
        # 定义一个结果提取器
        parser = JsonOutputParser(pydantic_object=InterfaceDocumentParserModel)
        # 创建一个调用链
        chain = api_document_parser.prompt | llm | parser
        # 调用大模型对接口文档进行解析
        return chain.invoke({"input_text": api_document})


if __name__ == '__main__':
    document2 = """
    ### 1.4 修改用户信息

```
PUT /api/users/{userId}
```

**请求参数**:

| 参数名   | 类型   | 必填 | 描述                     | 示例                                |
| -------- | ------ | ---- | ------------------------ | ----------------------------------- |
| nickname | string | 否   | ≤20字符                  | "新昵称"                            |
| avatar   | string | 否   | 图片URL                  | "https://mstest.com/new-avatar.jpg" |
| phone    | string | 否   | 手机号                   | 13800138000                         |
| gender   | string | 否   | "MALE"/"FEMALE"/"SECRET" | "MALE"                              |

**响应示例**:

```json
{
  "message": "更新成功"
}
```

### 
    """

    data = """
           ### 2.1 创建用户档案
           ```
           POST /api/users/{userId}/profile
           ```

           **路径参数**:
           | 参数名 | 类型   | 必填 | 描述   | 示例 |
           | ------ | ------ | ---- | ------ | ---- |
           | userId | string | 是   | 用户ID | 123  |

           **请求头参数**:
           | 参数名        | 类型   | 必填 | 描述         | 示例                    |
           | ------------- | ------ | ---- | ------------ | ----------------------- |
           | Authorization | string | 是   | 认证令牌     | Bearer abc123           |
           | Content-Type  | string | 是   | 内容类型     | application/json        |

           **查询参数**:
           | 参数名       | 类型    | 必填 | 描述           | 示例  |
           | ------------ | ------- | ---- | -------------- | ----- |
           | validate_only| boolean | 否   | 仅验证不保存   | false |

           **请求体 (JSON)**:
           ```json
           {
             "basic_info": {
               "first_name": "张",
               "last_name": "三",
               "birth_date": "1990-05-15",
               "gender": "male"
             },
             "contact_info": {
               "email": "zhangsan@example.com",
               "phone": "+86-13800138000",
               "emergency_contact": {
                 "name": "李四",
                 "relationship": "配偶",
                 "phone": "+86-13900139000"
               }
             },
             "addresses": [
               {
                 "type": "home",
                 "street": "北京市朝阳区建国路88号",
                 "city": "北京",
                 "postal_code": "100025",
                 "is_default": true
               }
             ],
             "preferences": {
               "language": "zh-CN",
               "notifications": {
                 "email_enabled": true,
                 "sms_enabled": false
               }
             },
             "skills": [
               {
                 "name": "Python",
                 "level": "advanced",
                 "certifications": [
                   {
                     "name": "Python Institute PCAP",
                     "issuer": "Python Institute",
                     "issue_date": "2022-03-15"
                   }
                 ]
               }
             ]
           }
           ```

           **请求体字段说明**:
           - basic_info (object, 必填): 用户基本信息
             - first_name (string, 必填): 名
             - last_name (string, 必填): 姓
             - birth_date (string, 可选): 出生日期，格式YYYY-MM-DD
             - gender (string, 可选): 性别，值为 male/female/other
           - contact_info (object, 必填): 联系信息
             - email (string, 必填): 电子邮箱
             - phone (string, 必填): 手机号码
             - emergency_contact (object, 可选): 紧急联系人
               - name (string, 必填): 联系人姓名
               - relationship (string, 必填): 关系
               - phone (string, 必填): 联系人电话
           - addresses (array, 必填): 地址列表
             - type (string, 必填): 地址类型，值为 home/work/billing
             - street (string, 必填): 街道地址
             - city (string, 必填): 城市
             - postal_code (string, 必填): 邮政编码
             - is_default (boolean, 可选): 是否默认地址
           - preferences (object, 可选): 用户偏好
             - language (string, 可选): 首选语言
             - notifications (object, 可选): 通知设置
               - email_enabled (boolean, 可选): 邮件通知开关
               - sms_enabled (boolean, 可选): 短信通知开关
           - skills (array, 可选): 技能列表
             - name (string, 必填): 技能名称
             - level (string, 必填): 技能水平，值为 beginner/intermediate/advanced/expert
             - certifications (array, 可选): 认证列表
               - name (string, 必填): 认证名称
               - issuer (string, 必填): 颁发机构
               - issue_date (string, 可选): 颁发日期

           **响应示例**:
           ```json
           {
             "success": true,
             "message": "用户档案创建成功",
             "data": {
               "profile_id": "prof_123456",
               "user_id": "123",
               "created_at": "2024-01-15T10:30:00Z"
             }
           }
           ```
       """
    api_parser = AIAPIDocumentParser()
    document = api_parser.parser(document2)
    import json

    print(json.dumps(document, indent=4, ensure_ascii=False))
