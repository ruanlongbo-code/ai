import json
from typing import Dict, List, Any, Union


class SwaggerV2Parser:
    """适配 Swagger 2.0 接口文档，提取路径、方法、参数和响应"""

    def __init__(self, swagger_path: str):
        with open(swagger_path, "r", encoding="utf-8") as f:
            self.spec = json.load(f)
        self.definitions = self.spec.get("definitions", {})

    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        """解析 $ref 引用。"""
        ref_name = ref.split("/")[-1]
        return self.definitions.get(ref_name, {"unresolved": ref})

    def _parse_schema(self, schema: Dict[str, Any]) -> Union[Dict[str, Any], List[Any]]:
        """递归解析 schema，支持嵌套结构。"""
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

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

    def parse(self) -> List[Dict[str, Any]]:
        """解析所有接口，输出格式与OpenAPI解析器保持一致。"""
        results = []
        for path, methods in self.spec.get("paths", {}).items():
            for method, info in methods.items():
                api_entry = {
                    "path": path,
                    "method": method.upper(),
                    "summary": info.get("summary", ""),
                    "description": info.get("description", ""),
                    "parameters": {
                        "header": [],
                        "path": [],
                        "query": []
                    },
                    "requestBody": {},
                    "responses": []
                }

                # 处理 parameters - 按类型分类
                body_params = []
                for param in info.get("parameters", []):
                    if "$ref" in param:
                        param = self._resolve_ref(param["$ref"])

                    param_info = {
                        "name": param.get("name"),
                        "required": param.get("required", False),
                        "type": param.get("type", "string"),
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
                    elif param_location == "body":
                        # Swagger 2.0 的 body 参数
                        schema = param.get("schema", {})
                        parsed_schema = self._parse_schema(schema)
                        body_params.append({
                            "media_type": "application/json",
                            "required": param.get("required", False),
                            "schema": parsed_schema
                        })
                    elif param_location == "formData":
                        # Swagger 2.0 的 formData 参数转换为 requestBody
                        body_params.append({
                            "name": param.get("name"),
                            "type": param.get("type", "string"),
                            "description": param.get("description", ""),
                            "required": param.get("required", False)
                        })

                # 处理 requestBody
                if body_params:
                    if len(body_params) == 1 and "schema" in body_params[0]:
                        # 如果是单个 body 参数（JSON）
                        api_entry["requestBody"] = {
                            "content_type": body_params[0]["media_type"],
                            "body": body_params[0]["schema"]
                        }
                    else:
                        # 如果是多个 formData 参数
                        api_entry["requestBody"] = {
                            "content_type": "application/x-www-form-urlencoded",
                            "body": body_params
                        }

                # 处理 responses - 改为数组格式，response_body返回实际JSON示例
                responses_list = []
                for status_code, resp in info.get("responses", {}).items():
                    schema = resp.get("schema", {})

                    # 如果没有schema，创建一个基本的响应结构
                    if not schema:
                        responses_list.append({
                            "http_code": int(status_code) if status_code.isdigit() else status_code,
                            "description": resp.get("description", ""),
                            "response_body": {}
                        })
                    else:
                        # 生成实际的JSON响应示例而不是字段描述
                        response_example = self._generate_response_example(schema)
                        responses_list.append({
                            "http_code": int(status_code) if status_code.isdigit() else status_code,
                            "description": resp.get("description", ""),
                            "media_type": "application/json",
                            "response_body": response_example
                        })

                api_entry["responses"] = responses_list
                results.append(api_entry)

        return results


if __name__ == "__main__":
    import os

    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建swagger.json的绝对路径
    swagger_path = os.path.join(current_dir, r"/tests/datas/swagger.json")
    swagger_path = os.path.normpath(swagger_path)

    if os.path.exists(swagger_path):
        parser = SwaggerV2Parser(swagger_path)
        api_list = parser.parse()
        print(json.dumps(api_list, ensure_ascii=False, indent=2))
        print(f"\n解析完成，共解析了 {len(api_list)} 个接口")
    else:
        print(f"错误：找不到文件 {swagger_path}")
        print("当前目录:", current_dir)
        print("查找的文件路径:", swagger_path)
