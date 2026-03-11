import os
import dotenv
from langchain_openai import ChatOpenAI

# 配置项目根目录路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# =============大模型配置================
# 加载环境变量
dotenv.load_dotenv(os.path.join(BASE_DIR, '.env'))

# =============LangSmith 追踪配置================
# 若环境变量中设置了 LANGCHAIN_API_KEY，则自动开启 LangSmith 链路追踪
_langsmith_api_key = os.getenv('LANGCHAIN_API_KEY', '')
if _langsmith_api_key:
    # 必须显式写入 os.environ，LangSmith SDK 才能读取到 API Key
    os.environ['LANGCHAIN_API_KEY'] = _langsmith_api_key
    os.environ.setdefault('LANGCHAIN_TRACING_V2', 'true')
    os.environ.setdefault('LANGCHAIN_PROJECT', 'ai-test-platform')
    os.environ.setdefault('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')

# RAG配置
# 内存输出路径
OUTPUT_PATH = os.path.join(os.path.join(BASE_DIR, "rag"), "output")
# RAG_STORAGE路径
STORAGE_PATH = os.path.join(os.path.join(BASE_DIR, "rag"), "rag_storage")

# ==============通过接口接入rag的配置参数==============
RAG_SERVER_URL = os.getenv('RAG_SERVER_URL', "")
LIGHTRAG_API_KEY = os.getenv('LIGHTRAG_API_KEY')

# ==============飞书开放平台配置==============
FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')

# ==============飞书项目 MCP 配置==============
FEISHU_PROJECT_KEY = os.getenv('FEISHU_PROJECT_KEY', 'research__development')
FEISHU_MCP_KEY = os.getenv('FEISHU_MCP_KEY', '')

# 对话模型
llm: ChatOpenAI = ChatOpenAI(
    model=os.getenv('LLM_MODEL'),
    base_url=os.getenv('BASE_URL'),
    api_key=os.getenv('API_KEY'),
    timeout=300,
    max_retries=2,
)

# 视觉模型（用于UI测试截图分析，若未配置则复用对话模型）
vision_llm: ChatOpenAI = ChatOpenAI(
    model=os.getenv('VISION_LLM_MODEL', os.getenv('LLM_MODEL')),
    base_url=os.getenv('VISION_BASE_URL', os.getenv('BASE_URL')),
    api_key=os.getenv('VISION_API_KEY', os.getenv('API_KEY')),
    timeout=300,
    max_retries=2,
)
