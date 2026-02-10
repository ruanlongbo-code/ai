from typing import Any, List, Dict, Optional
import numpy as np
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
import os, dotenv
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.rerank import generic_rerank_api
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything
from config import settings

dotenv.load_dotenv()


class RAGManager:
    """用于进行检索增强生成的rag类"""

    def __init__(self):
        # 定义一个消息列表(保存历史对话的消息)
        self.messages_list = []

    # 1、定义llm对话的处理函数(一定要定义成异步函数)
    async def llm_model_func(
            self,
            prompt: str,
            system_prompt: str | None = None,
            history_messages: list[dict[str, Any]] | None = None,
            token_tracker: Any | None = None,
            **kwargs: Any):
        """处理rag生成内容的大模型函数"""
        system_prompt = system_prompt or """
        你是一个资深的知识检索助手，请根据用户的问题进行分析去知识库检索结果
        输出规范：
            - 中文回复用，
            - 只返回知识库检索到的内容
        """
        return await openai_complete_if_cache(
            model=os.getenv("LLM_MODEL"),
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
            prompt=prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            token_tracker=token_tracker,
            **kwargs)

    # 2、定义embedding函数(一定要定义成异步函数)
    async def embedding_model_func(self, texts: list[str]) -> np.ndarray:
        return await openai_embed(
            texts,
            model=os.getenv("EMBEDDING_MODEL"),
            base_url=os.getenv("BASE_URL"),
            api_key=os.getenv("API_KEY"),
        )

    # 3、定义重排序函数(一定要定义成异步函数)
    async def re_rank_func(
            self,
            query: str,
            documents: List[str],
            top_n: Optional[int] = None,
            **kwargs,
    ) -> List[Dict[str, Any]]:
        """定义重排序函数"""
        return await generic_rerank_api(
            model=os.getenv("RERANK_MODEL"),
            base_url=os.getenv("BASE_URL") + '/rerank',
            api_key=os.getenv("API_KEY"),
            query=query,
            documents=documents,
            top_n=top_n,
            **kwargs
        )

    # 4、定义视觉模型(作用：往知识库上传文档的时候，用于理解文档中的图片和表格等复杂数据，在进行rag检索的时候，分析图片中的内容)
    async def vision_model_func(self, prompt,
                                system_prompt=None,
                                history_messages: list[dict[str, Any]] | None = None,
                                image_data=None,
                                **kwargs
                                ):
        """定义视觉模型接入的处理函数"""
        # system_prompt = system_prompt or "你是一个资深的知识检索助手，请根据用户的问题进行分析去知识库检索结果，并以中文回复用"
        # 构建图形上传处理的消息
        messages = [
            # 系统提示词
            {"role": "system", "content": system_prompt},
        ]
        if image_data:
            messages.append(
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        },
                    },
                ]}
            )
            return await openai_complete_if_cache(
                # 模型使用视觉模型
                model=os.getenv("VISION_MODEL"),
                base_url=os.getenv("BASE_URL"),
                api_key=os.getenv("API_KEY"),
                prompt="",
                system_prompt="",
                history_messages=[],
                messages=messages,
                **kwargs)
        else:
            messages.append({"role": "user", "content": prompt})
            return await openai_complete_if_cache(
                # 模型使用视觉模型
                model=os.getenv("VISION_MODEL"),
                base_url=os.getenv("BASE_URL"),
                api_key=os.getenv("API_KEY"),
                prompt=prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                **kwargs)

    async def init_rag(self, project, working_dir="./"):
        """初始化rag对象的函数"""
        self.lightrag = LightRAG(
            working_dir=working_dir,
            workspace=project,
            # 配置嵌入模型处理函数
            embedding_func=EmbeddingFunc(
                embedding_dim=int(os.getenv("EMBEDDING_NUMBER", 4096)),
                func=self.embedding_model_func
            ),
            # 配置llm对话处理函数
            llm_model_func=self.llm_model_func,
            # 配置重排模型处理函数
            rerank_model_func=self.re_rank_func,
            # 修改默认的存储方式(部署线上的时候对性能有要求，知识库中的数据量特别大的情况下才需要配置)
        )
        # 初始化rag对象的存储
        await self.lightrag.initialize_storages()
        await initialize_pipeline_status()
        """配置rag多模态处理能力"""
        rag = RAGAnything(
            lightrag=self.lightrag,  # 传递现有的 rag
            # 仅需要视觉模型用于多模态处理
            vision_model_func=self.vision_model_func,
            llm_model_func=self.llm_model_func,
        )
        self.rag = rag
        # 返回rag对象
        return rag

    async def load_documents(self, file_path):
        """加载文档到知识库"""
        # 等待文档加载完成
        await self.rag.process_document_complete(
            file_path=file_path,
            output_dir=settings.OUTPUT_PATH,
            parse_method="auto"
        )

    async def search_text(self, query):
        """知识库文本内容检索"""
        response = await self.lightrag.aquery(
            query=query,
            param=QueryParam(
                stream=True,
                # 传入历史对话记录
                conversation_history=self.messages_list,
                # 上下文中加入多少条历史对话的消息
                history_turns=10
            )
        )
        result = ""
        async for chunk in response:
            result += chunk
            yield chunk
        # 记录历史对话消息
        self.messages_list.append({"role": "user", "content": query})
        self.messages_list.append({"role": "assistant", "content": result})

    async def multi_model_search(self, query, image_path):
        """多模态检索"""
        response = await self.rag.aquery_with_multimodal(
            query=query,
            stream=True,
            multimodal_content=[
                {
                    "type": "image",
                    "img_path": image_path
                }
            ]
        )
        return response


async def main():
    # 初始化rag对象
    rag_manage = RAGManager()
    # 初始化rag对象
    await rag_manage.init_rag("web_shop_v1", settings.STORAGE_PATH)
    # 搜索知识库中的内容
    # response = rag_manage.search_text("用户模块有哪些功能")
    # async for chunk in response:
    #     print(chunk, end="", flush=True)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
