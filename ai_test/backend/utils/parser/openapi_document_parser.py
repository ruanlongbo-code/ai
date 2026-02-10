import json
from typing import Dict, Any, List, Union


class OpenAPIParser:
    """
    OpenAPI 聚合器，用于加载、解析和聚合 OpenAPI 规范中的接口信息。
    参数:
    - openapi_path: OpenAPI 规范文件的路径。
    """

    def __init__(self, openapi_path: str):
        self.openapi_path = openapi_path
        self.openapi = self._load_openapi()
        self.components = self.openapi.get("components", {}).get("schemas", {})
        self.parameter_defs = self.openapi.get("components", {}).get("parameters", {})
        self.request_body_defs = self.openapi.get("components", {}).get("requestBodies", {})
        self.security_schemes = self.openapi.get("components", {}).get("securitySchemes", {})

    def _load_openapi(self) -> Dict[str, Any]:
        """
        加载 OpenAPI 规范文件。

        返回:
        - 解析后的 OpenAPI 规范字典。
        """
        with open(self.openapi_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _resolve_ref(self, ref: str) -> Any:
        """
        解析 $ref 引用。

        参数:
        - ref: 引用字符串，以 #/components 开头。

        返回:
        - 引用所指向的 schema、parameter 或 requestBody。
        """
        if ref.startswith("#/components/schemas/"):
            schema_name = ref.split("/")[-1]
            return self.components.get(schema_name, {"missing_schema": schema_name})
        elif ref.startswith("#/components/parameters/"):
            param_name = ref.split("/")[-1]
            return self.parameter_defs.get(param_name, {"missing_param": param_name})
        elif ref.startswith("#/components/requestBodies/"):
            body_name = ref.split("/")[-1]
            return self.request_body_defs.get(body_name, {"missing_request_body": body_name})
        else:
            return {"unresolved_ref": ref}

    def _parse_security_requirements(self, security_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析安全认证要求，转换为请求头参数格式。

        参数:
        - security_list: 安全要求列表

        返回:
        - 转换后的请求头参数列表
        """
        auth_headers = []

        for security_req in security_list:
            for scheme_name, scopes in security_req.items():
                if scheme_name in self.security_schemes:
                    scheme = self.security_schemes[scheme_name]
                    scheme_type = scheme.get("type", "")

                    if scheme_type == "oauth2":
                        auth_headers.append({
                            "name": "Authorization",
                            "required": True,
                            "type": "string",
                            "description": f"OAuth2认证令牌 (Bearer token) - {scheme_name}"
                        })
                    elif scheme_type == "http":
                        scheme_scheme = scheme.get("scheme", "")
                        if scheme_scheme.lower() == "bearer":
                            auth_headers.append({
                                "name": "Authorization",
                                "required": True,
                                "type": "string",
                                "description": f"Bearer认证令牌 - {scheme_name}"
                            })
                        elif scheme_scheme.lower() == "basic":
                            auth_headers.append({
                                "name": "Authorization",
                                "required": True,
                                "type": "string",
                                "description": f"Basic认证 - {scheme_name}"
                            })
                    elif scheme_type == "apiKey":
                        key_location = scheme.get("in", "header")
                        key_name = scheme.get("name", "X-API-Key")
                        if key_location == "header":
                            auth_headers.append({
                                "name": key_name,
                                "required": True,
                                "type": "string",
                                "description": f"API Key认证 - {scheme_name}"
                            })

        return auth_headers

    def _parse_schema(self, schema: Dict[str, Any]) -> Union[Dict[str, Any], List[Any]]:
        """
        递归解析 schema。

        参数:
        - schema: 待解析的 schema 字典。

        返回:
        - 解析后的 schema。
        """
        if '$ref' in schema:
            schema = self._resolve_ref(schema['$ref'])

        if schema.get('type') == 'object':
            # 获取必填字段列表
            required_fields = schema.get('required', [])
            result = []

            for prop, prop_info in schema.get('properties', {}).items():
                field_info = {
                    "name": prop,
                    "type": prop_info.get("type", "unknown"),
                    "description": prop_info.get("description", ""),
                    "required": prop in required_fields
                }

                # 处理嵌套对象
                if prop_info.get('type') == 'object' and 'properties' in prop_info:
                    field_info["nested_fields"] = self._parse_schema(prop_info)
                elif prop_info.get('type') == 'array' and 'items' in prop_info:
                    # 处理数组中的嵌套对象
                    items_schema = prop_info['items']
                    if items_schema.get('type') == 'object' and 'properties' in items_schema:
                        field_info["array_item_fields"] = self._parse_schema(items_schema)

                result.append(field_info)

            return result

        elif schema.get('type') == 'array' and 'items' in schema:
            return [self._parse_schema(schema['items'])]
        else:
            return {
                "type": schema.get("type"),
                "description": schema.get("description", "")
            }

    def _generate_response_example(self, schema: Dict[str, Any]) -> Any:
        """
        根据schema生成实际的JSON响应示例。

        参数:
        - schema: 响应的schema定义。

        返回:
        - 生成的JSON响应示例。
        """
        if '$ref' in schema:
            schema = self._resolve_ref(schema['$ref'])

        schema_type = schema.get('type')

        if schema_type == 'object':
            result = {}
            properties = schema.get('properties', {})
            required_fields = schema.get('required', [])

            for prop, prop_info in properties.items():
                # 只为必填字段或有默认值的字段生成示例
                if prop in required_fields or 'default' in prop_info:
                    result[prop] = self._generate_response_example(prop_info)

            return result
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            # 生成一个包含示例项的数组
            return [self._generate_response_example(items_schema)]
        elif schema_type == 'string':
            return schema.get('example', 'string_example')
        elif schema_type == 'integer':
            return schema.get('example', 123)
        elif schema_type == 'number':
            return schema.get('example', 123.45)
        elif schema_type == 'boolean':
            return schema.get('example', True)
        else:
            # 对于未知类型，返回空对象
            return {}

    def parser(self) -> List[Dict[str, Any]]:
        """
        聚合 OpenAPI 规范中的接口信息。

        返回:
        - 包含所有接口信息的列表。
        """
        paths = self.openapi.get("paths", {})
        api_list = []

        for path, methods in paths.items():
            for method, details in methods.items():
                api_entry = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description", ""),
                    "parameters": {
                        "header": [],
                        "path": [],
                        "query": []
                    },
                    "requestBody": {},
                    "responses": []
                }

                # parameters - 按类型分类
                for param in details.get("parameters", []):
                    if "$ref" in param:
                        param = self._resolve_ref(param["$ref"])
                    schema = param.get("schema", {})
                    param_info = {
                        "name": param.get("name"),
                        "required": param.get("required", False),
                        "type": schema.get("type"),
                        "description": param.get("description", "")
                    }

                    # 根据参数位置分类
                    param_location = param.get("in", "")
                    if param_location == "header":
                        api_entry["parameters"]["header"].append(param_info)
                    elif param_location == "path":
                        api_entry["parameters"]["path"].append(param_info)
                    elif param_location == "query":
                        api_entry["parameters"]["query"].append(param_info)

                # 解析安全认证要求，添加到请求头参数
                security_requirements = details.get("security", [])
                if security_requirements:
                    auth_headers = self._parse_security_requirements(security_requirements)
                    api_entry["parameters"]["header"].extend(auth_headers)

                # request body - 支持多种内容类型
                req_body = details.get("requestBody", {})
                if "$ref" in req_body:
                    req_body = self._resolve_ref(req_body["$ref"])

                request_body_list = []
                content = req_body.get("content", {})
                for media_type, media_info in content.items():
                    schema = media_info.get("schema", {})
                    parsed_schema = self._parse_schema(schema)
                    request_body_list.append({
                        "media_type": media_type,
                        "required": req_body.get("required", False),
                        "schema": parsed_schema
                    })
                # 如果只有一个内容类型，保持原有格式兼容性但添加类型说明
                if len(request_body_list) == 1:
                    api_entry["requestBody"] = {
                        "content_type": request_body_list[0]["media_type"],
                        "body": request_body_list[0]["schema"]
                    }
                else:
                    api_entry["requestBody"] = request_body_list

                # responses - 改为数组格式，response_body返回实际JSON示例
                responses_list = []
                for status_code, resp in details.get("responses", {}).items():
                    response_content = resp.get("content", {})

                    # 如果没有content，创建一个基本的响应结构
                    if not response_content:
                        responses_list.append({
                            "http_code": int(status_code) if status_code.isdigit() else status_code,
                            "description": resp.get("description", ""),
                            "response_body": {}
                        })
                    else:
                        # 处理每种媒体类型
                        for media_type, media_info in response_content.items():
                            schema = media_info.get("schema", {})
                            # 生成实际的JSON响应示例而不是字段描述
                            response_example = self._generate_response_example(schema)
                            responses_list.append({
                                "http_code": int(status_code) if status_code.isdigit() else status_code,
                                "description": resp.get("description", ""),
                                "media_type": media_type,
                                "response_body": response_example
                            })

                api_entry["responses"] = responses_list

                api_list.append(api_entry)

        return api_list

    def save_to_json(self, output_path: str, data: List[Dict[str, Any]]):
        """
        将聚合后的接口信息保存为 JSON 文件。

        参数:
        - output_path: 输出文件的路径。
        - data: 聚合后的接口信息列表。
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已保存聚合后的接口信息，共 {len(data)} 条接口 → {output_path}")


# 使用示例
if __name__ == "__main__":

    aggregator = OpenAPIParser(r"/tests/datas/openapi.json")
    api_info = aggregator.parser()

    # 查找需要认证的接口作为示例
    auth_apis = [api for api in api_info if api['parameters']['header']]
    non_auth_apis = [api for api in api_info if not api['parameters']['header']]

    print("解析结果示例:")
    print("\n=== 需要认证的接口示例 ===")
    if auth_apis:
        print(json.dumps(auth_apis[:2], ensure_ascii=False, indent=2))
    else:
        print("没有找到需要认证的接口")

    print("\n=== 不需要认证的接口示例 ===")
    if non_auth_apis:
        print(json.dumps(non_auth_apis[:1], ensure_ascii=False, indent=2))

    print(f"\n总共解析了 {len(api_info)} 个接口")
    print(f"其中需要认证的接口: {len(auth_apis)} 个")
    print(f"不需要认证的接口: {len(non_auth_apis)} 个")
