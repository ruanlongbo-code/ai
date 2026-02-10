"""
通过api接口去接入rag知识库系统
"""
import json
from config import settings
import requests


class RAGClient:
    """通过api接口去接入rag知识库"""

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": settings.LIGHTRAG_API_KEY
        }
        self.url = settings.RAG_SERVER_URL

    def get_requests_body(self, query: str, conversation_history=None, history_turns=10):
        """获取请求参数"""
        return {
            "query": query,
            "mode": "global",
            "only_need_context": False,
            "only_need_prompt": False,
            "response_type": "Multiple Paragraphs",
            "top_k": 10,
            "chunk_top_k": 5,
            "max_entity_tokens": 10000,
            "max_relation_tokens": 10000,
            "max_total_tokens": 40000,
            "conversation_history": [] if conversation_history is None else conversation_history,
            "history_turns": history_turns,
            "ids": [],
            "user_prompt": "请用中文回复结果",
            "enable_rerank": True
        }

    def query(self, query: str, conversation_history=None, history_turns=10):
        """ rag搜索接口 """
        url = self.url + "/query"
        params = self.get_requests_body(query, conversation_history, history_turns)
        res = requests.post(url, json=params, headers=self.headers)
        return res.json()

    def query_stream(self, query: str, conversation_history=None, history_turns=10):
        url = self.url + "/query/stream"
        params = self.get_requests_body(query, conversation_history, history_turns)
        # 发请求，流式获取结果
        result = requests.post(url, json=params, headers=self.headers, stream=True)
        for item in result.iter_lines():
            content = json.loads(item.decode()).get("response")
            yield content

    # 添加文档到知识库中
    def add_document(self, data: dict):
        """插入文档到知识库，并获取到文档的id"""
        url = self.url + "/documents/text"
        body = {
            "file_source": data.get("file_source", ''),
            "text": data.get("text", ''),
        }
        response = requests.post(url, json=body, headers=self.headers, stream=True)
        datas = response.json()
        if response.status_code == 200 and datas.get("status") == "success":
            # 获取返回的track_id，用来查询知识库中文档的id
            track_id = datas.get("track_id")
            url2 = self.url + f"/documents/track_status/{track_id}"
            # 发送请求获取文档的id
            track_response = requests.get(url2, headers=self.headers)
            track_datas = track_response.json()
            if len(track_datas.get("documents")) > 0:
                doc_on = track_datas.get("documents")[0]["id"]
                return {"status": "success", "doc_on": doc_on}
            else:
                # 更新知识库中的文档
                return {"status": "update"}
        else:
            return {"status": "error"}

    # 删除知识库中的文档
    def delete_document(self, doc_id):
        url = self.url + f"/documents/delete_document"
        body = {
            "doc_ids": [
                doc_id
            ],
            "delete_file": False
        }
        response = requests.delete(url, json=body, headers=self.headers)
        return response.status_code == 200


if __name__ == '__main__':
    rag_client = RAGClient()
    result = rag_client.query("用户模块接口有哪些？")
    print(result["response"])
    # result = rag_client.query_stream("商品模块接口有哪些？")
    # for item in result:
    #     print(item, end="")
