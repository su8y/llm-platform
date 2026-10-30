import os
# SERVER STAGE
DOCKER = "docker"
DOCKER_LOCAL = "docker-local"
DOCKER_LIST = (DOCKER, DOCKER_LOCAL)

STAGING = "staging"
REAL = "production"

# RESPONSE CODE
SUCCESS_CODE = 200
ERROR_CODE = 500
DATA_ERROR_CODE = 400
FORBIDDEN_ERROR_CODE = 403
LLM_ERROR_CODE = 100
CLOUD_ERROR_CODE = 101
MESSAGE_QUEUE_ERROR_CODE = 102

# gritChain
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.2

# SERVICE
CS_STAGING = "cs-staging"
CS_PRODUCTION = "cs-production"
VOC_STAGING = "voc-staging"
VOC_PRODUCTION = "voc-production"
UXHEATMAP_AIREPORT_STAGING = "uxheatmap-aireport-staging"
UXHEATMAP_AIREPORT_PRODUCTION = "uxheatmap-aireport-production"
JOURNEYMAP_AIREPORT_STAGING = "journeymap-aireport-staging"
JOURNEYMAP_AIREPORT_PRODUCTION = "journeymap-aireport-production"
JOURNEYMAP_DASHBOARD = "journeymap-dashboard"
REPORTCHAT_STAGING = "reportchat-staging"
REPORTCHAT_PRODUCTION = "reportchat-production"
DASHBOARD_STAGING = "dashboard-staging"
DASHBOARD_PRODUCTION = "dashboard-production"
DASHBOARDHELL_STAGING="dashboardhell-staging"
DASHBOARDHELL_PRODUCTION="dashboardhell-production"
DASHBOARDCHAT_STAGING = "dashboardchat-staging"
DASHBOARDCHAT_PRODUCTION = "dashboardchat-production"
SCROLLCHAT_STAGING = "scrollchat-staging"
SCROLLCHAT_PRODUCTION = "scrollchat-production"
FILEPARSER_STAGING = "fileparser-staging"
FILEPARSER_PRODUCTION = "fileparser-production"
LLM_PLATFORM_STAGING = "llm-platform-staging"
LLM_PLATFORM_PRODUCTION = "llm-platform-production"
BAX_STAGING = "bax-staging"
BAX_PRODUCTION = "bax-production"
BAX_OCR_STAGING = "bax-ocr-staging"
GEO_CHAT_STAGING = "geo-chat-staging"
GEO_CHAT_PRODUCTION = "geo-chat-production"
GEO_SIMPLE_STAGING = "geo-simple-staging"
GEO_SIMPLE_PRODUCTION = "geo-simple-production"
GEO_JSON_STAGING = "geo-json-staging"
GEO_JSON_PRODUCTION = "geo-json-production"
JOURNEYMAPMCP_STAGING = "journeymapmcp-staging"
JOURNEYMAPMCP_PRODUCTION = "journeymapmcp-production"
CXDATATRENDMCP_STAGING = "cxdatatrendmcp-staging"
CXDATATRENDMCP_PRODUCTION = "cxdatatrendmcp-production"

DEFAULT = "default"

LLM_PLATFORM_SERVICES = [LLM_PLATFORM_PRODUCTION, LLM_PLATFORM_STAGING]

# CORS 허용 목록. 콤마로 나열한다. 비우면 모두 허용
def _env_list(name: str) -> tuple[str, ...]:
    return tuple(filter(None, (part.strip() for part in os.getenv(name, "").split(",")))) or ("*",)

ALLOWED_FRONT_ADDRESS = _env_list("ALLOWED_FRONT_ADDRESS")
ALLOWED_API_ADDRESS = _env_list("ALLOWED_API_ADDRESS")

LLM_API_PATH = "/playground/chat"
CHATBOT_API_PATH = "/chatbot/chat"
RAG_API_PATH = "/playground/get_retrieval_data"

TIMEOUT = 15

# SERVICE
VLLM = "llm-platform-install"
LLM_PLATFORM = "llm-platform"
CHATBOT = "chatbot"

#VENDOR
OPENAI = "openai"
AZURE = "azure"
ANTHROPIC = "anthropic"
XAI = "xai"
GOOGLE = "google"
BEDROCK = "bedrock"
META = "meta"
VLLM_VENDOR = "vllm"

#MODEL
OPENAI_FLAGSHIP_MODEL_LIST = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"]
OPENAI_REASONING_MODEL_LIST = ["o1", "o1-mini", "o1-pro", "o3-mini", "o4-mini", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
LOCAL_REASONING_MODEL_LIST = ["gpt-oss:20b"]
OPENAI_MODEL_LIST = ["gpt-5.2", "gpt-5.2-pro", "gpt-5-mini", "gpt-5.1", "gpt-5.1-mini", "gpt-5.1-nano", "gpt-5",  "gpt-5-nano", "gpt-4o", "gpt-4o-mini", "o1-mini", "o1-preview", "o3-mini", "o4-mini", "gpt-4.1", "gpt-4.1-mini"]
AZURE_MODEL_LIST = ["gpt-4o", "gpt-4o-mini", "o1-mini", "o1-preview", "o3-mini", "o4-mini", "gpt-4.1", "gpt-4.1-mini"]
ANTHROPIC_MODEL_LIST = ['claude-sonnet-4-6', 'claude-opus-4-6', 'claude-sonnet-4-5', 'claude-haiku-4-5', 'claude-opus-4-5', 'claude-sonnet-4-20250514']
BEDROCK_MODEL_LIST = [
    "anthropic.claude-sonnet-4-6",
    "anthropic.claude-opus-4-6-v1",
    "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "global.anthropic.claude-opus-4-5-20251101-v1:0",
    "apac.anthropic.claude-sonnet-4-20250514-v1:0"
]
GOOGLE_MODEL_LIST = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash-lite",
]
XAI_MODEL_LIST = ["grok-4-latest", "grok-4-fast-non-reasoning", "grok-4-fast-reasoning", "grok-code-fast-1", "grok-3-mini"]
TIKTOKEN_MODEL_LIST = ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1", "o1-pro"]
ANTHROPIC_FALLBACK_MODEL_OBJECT = {
    # "bedrock_model_id": "anthropic_model_id"
    "anthropic.claude-sonnet-4-6": "claude-sonnet-4-6",
    "anthropic.claude-opus-4-6-v1": "claude-opus-4-6",
    "global.anthropic.claude-sonnet-4-5-20250929-v1:0": "claude-sonnet-4-5",
    "global.anthropic.claude-haiku-4-5-20251001-v1:0": "claude-haiku-4-5",
    "global.anthropic.claude-opus-4-5-20251101-v1:0": "claude-opus-4-5",
    "apac.anthropic.claude-sonnet-4-20250514-v1:0": "claude-sonnet-4-20250514"
}
BEDROCK_FALLBACK_MODEL_OBJECT = {
    # "anthropic_model_id": "bedrock_model_id"
    "claude-sonnet-4-6": "anthropic.claude-sonnet-4-6",
    "claude-opus-4-6": "anthropic.claude-opus-4-6-v1",
    "claude-sonnet-4-5": "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "claude-haiku-4-5": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
    "claude-opus-4-5": "global.anthropic.claude-opus-4-5-20251101-v1:0",
    "claude-sonnet-4-20250514": "apac.anthropic.claude-sonnet-4-20250514-v1:0"
}

# IMAGE EXTENSION FORMAT
BASE64 = "base64"
URL = "url"
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
FORMAT_MAP = {
    "VipsForeignLoadJpegBuffer": "jpg",
    "VipsForeignLoadPngBuffer": "png",
    "VipsForeignLoadWebpBuffer": "webp",
    "VipsForeignLoadGifBuffer": "gif",
    "VipsForeignLoadTiffBuffer": "tiff",
}

# EMBEDDING: 변경 시 임베딩 모델 차원(VECTOR_DIMENSION)과 함께 확인
FILESEARCH_CHUNKING_TOKEN = 512
FILESEARCH_CHUNKING_OVERLAPS_TOKEN = 150
EMBEDDING_CHUNKING_MAX_TOKEN = 500
EMBEDDING_CHUNKING_OVERLAPS_TOKEN = 150

# FILE TEMP DIR NAME
FILE_TEMP_DIR_NAME = "tmp"

# MCP TOOLS
HANMI_TOOLS_LIST = ["get_current_time", "query_prescription_data"]
SCHEMA_TOOLS_LIST = ["geo_analyze_page",
                     "get_main_page_guide",
                     "get_list_page_guide",
                     "get_detail_page_guide",
                     "get_info_page_guide",
                     "get_form_page_guide",
                     "get_cta_page_guide",
                     "get_technology_industry_guide",
                     "get_healthcare_industry_guide",
                     "get_finance_industry_guide",
                     "get_education_industry_guide",
                     "get_entertainment_industry_guide",
                     "get_consumer_industry_guide",
                     "get_it_industry_guide",
                     "get_information_industry_guide",
                     "get_leisure_industry_guide",
                     "get_public_industry_guide"]
