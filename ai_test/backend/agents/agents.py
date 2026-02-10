import uuid
from langgraph.prebuilt import create_react_agent
from config.prompts.agent import case_generator_agent, api_case_generator_prompt, main_agent_prompt
from config.settings import llm
from mcp_tools.tools import search_requirement, generator_case, search_api_document, api_document_to_cases, load_env_data
from langgraph.store.memory import InMemoryStore
from dataclasses import dataclass
from langgraph.checkpoint.memory import InMemorySaver
from langgraph_supervisor import create_supervisor
from config import settings

# 开发阶段使用内置的InMemoryStore来存储以及，部署上线可以改成redis
memory = InMemoryStore()


@dataclass
class RuntimeContext:
    project_id: str
    module_id: str
    user_id: str | None = None
    session_id: str | None = None
    memory_key: str = "chat_history"


class AgentManage:
    """agent管理类"""

    @staticmethod
    def create_case_generator_agent():
        """创建一个功能用例生成的agent"""
        # 创建agent
        agent = create_react_agent(
            name="case_generator_agent",
            model=llm.bind_tools([search_requirement, generator_case]),
            tools=[search_requirement, generator_case],
            prompt=case_generator_agent.prompt,
            checkpointer=InMemorySaver()
        )
        return agent

    @staticmethod
    def create_api_case_generator_agent():
        """创建一个api用例生成的智能体"""
        agent = create_react_agent(
            name="api_case_generator_agent",
            model=llm.bind_tools([search_api_document, load_env_data, api_document_to_cases]),
            tools=[search_api_document, load_env_data, api_document_to_cases],
            prompt=api_case_generator_prompt.prompt,
            checkpointer=InMemorySaver()
        )
        return agent

    @classmethod
    def create_supervisor_agent(cls):
        """创建一个主管的多agent程序"""
        supervisor = create_supervisor(
            agents=[
                cls.create_case_generator_agent(),
                cls.create_api_case_generator_agent()
            ],
            model=settings.llm,
            prompt=main_agent_prompt.prompt
        ).compile()
        return supervisor

    @staticmethod
    def agent_chat(agent, query, context: RuntimeContext):
        # 获取历史聊天记录
        namespace = (context.user_id, context.session_id)
        # 获取历史对话记录
        history_message = memory.search(namespace)
        if history_message is None:
            history_message = []
        else:
            history_message = [item.value for item in history_message]
        # 组装包含历史对话的messages消息
        messages = history_message + [{"role": "user", "content": query}]
        response = agent.invoke({"messages": messages},
                                subgraphs=True,
                                stream_mode=['messages', 'custom', 'tool_call'],
                                config={"configurable": {"thread_id": "1"}},
                                context={"project_id": "web_shop", "module_id": "user01"})

        result = ''
        print(response)
        # for chunk in response:
        #     if chunk[1] == 'custom':
        #         result += chunk[2]
        #         yield {"type": "custom", "content": chunk[2]}
        #     elif chunk[1] == 'messages':
        #         result += chunk[2][0].content
        #         yield {"type": "messages", "content": chunk[2][0].content}
        #     elif chunk[1] == 'tool_call':
        #         result += chunk[2]
        #         yield {"type": "tool_call", "content": chunk[2]}
        # 保存当前的问题到记忆中
        memory.put(namespace, str(uuid.uuid4()), {"role": "user", "content": query})
        # 保存ai的回答到记忆中
        memory.put(namespace, str(uuid.uuid4()), {"role": "assistant", "content": result})


if __name__ == '__main__':
    agent = AgentManage.create_supervisor_agent()
    # 创建运行上下文参数
    context = RuntimeContext(project_id="web_shop",
                             module_id="user01",
                             user_id="user01",
                             session_id="00001"
                             )
    # ================测试功能用例成功的智能体=============

    # print("===================1===================")
    # result = AgentManage.agent_chat(agent=agent, query="请查询订单功能的需求文档？", context=context)
    # for i in result:
    #     if i["type"] == "custom":
    #         print(i["content"])
    #     elif i["type"] == "messages":
    #         print(i["content"], end="", flush=True)
    #
    # print("===================2===================")
    # result2 = AgentManage.agent_chat(agent=agent, query="我刚刚问的是什么？", context=context)
    # for i in result2:
    #     if i["type"] == "custom":
    #         print(i["content"])
    #     elif i["type"] == "messages":
    #         print(i["content"], end="", flush=True)
    #
    # print("===================3===================")
    # result3 = AgentManage.agent_chat(agent=agent, query="我是干什么的？", context=context)
    # for i in result3:
    #     if i["type"] == "custom":
    #         print(i["content"])
    #     elif i["type"] == "messages":
    #         print(i["content"], end="", flush=True)
    # ===============测试api用例生成的智能体=============
    result4 = AgentManage.agent_chat(agent=agent, query="获取用户登录的需求文档，生成功能测试用例", context=context)
    # for i in result4:
    #     if i["type"] == "custom":
    #         print(i["content"], end="")
    #     elif i["type"] == "messages":
    #         print(i["content"], end="", flush=True)
