# SERVER_STAGE
DEV = "development"
STAGING = "staging"
REAL = "production"
DOCKER = "docker"
DOCKER_LOCAL = "docker-local"
DOCKER_LIST = [DOCKER, DOCKER_LOCAL]

SERVICE_LLM_PLATFORM_STAGING = "llm-platform-staging"
SERVICE_LLM_PLATFORM_REAL = "llm-platform-production"
SERVICE_LLM_PLATFORM_INSTALL = "llm-platform-install"
SERVICE_VOC_STAGING = "voc-staging"
SERVICE_VOC_REAL = "voc-production"

# URL
DOCKER_API_URL = "http://localhost:4321/llm-platform-api/"
DOCKER_URL = "http://localhost:4321/"
DEV_URL = "http://localhost:5176/"
DEV_API_URL = "http://localhost:4321/llm-platform-api/"
STAGING_DEV_URL = "https://dev.llm-platform.example.com/"
STAGING_DEV_API_URL = "https://dev-api.llm-platform.example.com/"
STAGING_URL = "https://staging.llm-platform.example.com/"
STAGING_API_URL = "https://staging-api.llm-platform.example.com/"
REAL_URL = "https://llm-platform.example.com/"
REAL_API_URL = "https://api.llm-platform.example.com/"

# CHATBOT ALLOW
CHATBOT_ALLOW = [REAL_URL, STAGING_URL, STAGING_DEV_URL, DEV_URL, DOCKER_URL]

# LLM_PLATFORM CHATBOT ARGS
LLM_PLATFORM_CHATBOT_COMPANY_KEY = "16358ce2c80d4f80820028cc5f839a3c"

# GEN AI SOURCE
AZURE = "azure"
AWS = "aws"
OPENAI = "openai"
ANTHROPIC = "anthropic"
GOOGLE = "google"

# MODEL_LIST
BASE_VENDOR = GOOGLE
BASE_MODEL = "gemini-2.5-flash"
BASE_MAIL_VENDOR = OPENAI
BASE_MAIL_MODEL = "gpt-4.1"
BASE_MCP_VENDOR = ANTHROPIC
BASE_MCP_MODEL = "claude-sonnet-4-5"

OPENAI_MODEL_LIST = ["gpt-5.1", "gpt-5.1-mini", "gpt-5.1-nano", "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4o-mini", "o1-mini", "o1-preview", "o3-mini", "o4-mini", "gpt-4.1", "gpt-4.1-mini"]
AZURE_MODEL_LIST = ["gpt-4o", "gpt-4o-mini", "o1-mini", "o1-preview", "o3-mini", "o4-mini", "gpt-4.1", "gpt-4.1-mini"]
ANTHROPIC_MODEL_LIST = ['claude-sonnet-4-5', 'claude-opus-4-1', 'claude-haiku-4-5', 'claude-sonnet-4-20250514']
BEDROCK_MODEL_LIST = [
    "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "apac.anthropic.claude-sonnet-4-20250514-v1:0",
    "apac.anthropic.claude-3-7-sonnet-20250219-v1:0"
]
GOOGLE_MODEL_LIST = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3-pro-preview"]
XAI_MODEL_LIST = ["grok-4-latest", "grok-4-fast-non-reasoning", "grok-4-fast-reasoning", "grok-code-fast-1", "grok-3-mini"]
TIKTOKEN_MODEL_LIST = ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1", "o1-pro"]

# PINECONE INDEX CONSTANTS
REAL_INDEX = "llm-platform"
STAGING_INDEX = "llm-platform-staging"
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_TIKTOKEN_MODEL = "cl100k_base"
EMBEDDING_MAX_TOKEN = 8192
BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v1"

# CHUNKING STRATEGY
EMBEDDING_CHUNKING_MAX_TOKEN = 500
EMBEDDING_CHUNKING_OVERLAPS_TOKEN = 150

#AWS
PARSER_BUCKET = "llm-platform-file-parser"
BUCKET = "llm-platform-cdn"

# MONITORING ISSUE STATUS
ISSUE1 = "needSolve"
ISSUE2 = "reqExtraInfo"
ISSUE3 = "confirming"
ISSUE4 = "editing"
ISSUE5 = "checking"
ISSUE6 = "editComplete"
ISSUE7 = "notIssue"
ISSUE8 = "completeAnswer"

# API CODE
ALREADY_ID_CODE = 9000
ALREADY_EMAIL_CODE = 9001
ALREADY_COMPANY_NAME_CODE = 9002
WRONG_EMAIL_TYPE_CODE = 9003
GET_CURRENT_CREDIT_KEEP_CODE = 9004
OVER_TOKEN_SIZE_CODE = 999
NOT_ABLE_DELETE_CATEGORY_CODE = 998
NOT_ABLE_UPLOAD_FILE_CODE = 997
PARSER_CREDIT_AVAILABLE_OVER_CODE = 996
PLAN_EXPIRED_CODE = 995
SUCCESS_CODE = 200
FAIL_CODE = 500
INVALID_PAYLOAD_CODE = 400
INVALID_TOKEN_CODE = 401
FORBIDDEN_CODE = 403
NOT_FOUND_USER_CODE = 402
NOT_FOUND_PASSWORD_CODE = 403
NOT_FOUND_DATA_CODE = 404
NOT_CERTIFIED_USER_CODE = 405
PINECONE_ERROR_CODE = 500


# API MESSAGE
SUCCESS_MESSAGE = "Success"
FAIL_MESSAGE = "Fail"
ALREADY_ID_MESSAGE = "Already has same ID"
ALREADY_EMAIL_MESSAGE = "Already has same EMAIL"
ALREADY_COMPANY_NAME_MESSAGE = "Already has same COMPANY NAME"
WRONG_EMAIL_TYPE_MESSAGE = "Invalid e-mail format"
NOT_ABLE_DELETE_CATEGORY_MESSAGE = "this category is allocated in some post"
NOT_ABLE_UPLOAD_FILE_MESSAGE = "you can not upload file. please check limit number of upload"
INVALID_TOKEN_MESSAGE = "Invalid Token. Please Check it"
INVALID_PAYLOAD_MESSAGE = "Invalid Payload. Please Check it"
FORBIDDEN_MESSAGE = "Forbidden because input data is invalid"
NOT_FOUND_USER_MESSAGE = "Wrong ID"
NOT_FOUND_PASSWORD_MESSAGE = "Wrong Password"
NOT_FOUND_DATA_MESSAGE = "Can not find your input data"
NOT_CERTIFIED_USER_MESSAGE = "Not certified"
PINECONE_ERROR_MESSAGE = "Pinecone Error"
NOT_MCP_AUTH_MESSAGE = "MCP 사용 권한이 없습니다. 권한을 얻으신 후 다시 시도해주시기 바랍니다. \n\n MCP 권한은 관리자에게 문의 바랍니다."
PARSER_CREDIT_AVAILABLE_OVER_MESSAGE = "파일 업로드 크레딧이 부족합니다. \n\n 관리자에게 문의 바랍니다."
PLAN_EXPIRED_MESSAGE = "현재 적용된 플랜이 없습니다.\n\n 관리자에게 문의 바랍니다."

# PLAN
INIT_PLAN_ID = 3
BASIC_PLAN_ID = 4
PREMIUM_PLAN_ID = 5
PRO_PLAN_ID = 6
EXPIRED_PLAN_INFO_ID = 8
TRIAL_EXPIRED_DAYS = 30
PLAN_RUN = "run"
PLAN_STOP = "stop"


# AUTH
MASTER = 1
MANAGER = 2
VIEWER = 3


# HUMAN MESSAGE NAME
RAG_NAME = "참조 데이터"
USER_QUESTION_NAME = "사용자 질문"
LANG_NAME = "답변 언어"

DEFAULT_PROMPT = """당신은 고객의 질문에 대답하는 AI이고 이름은 비글입니다. 당신은 이용자가 묻는 질문에 대하여 아래 주어진 Context를 바탕으로 답변을 제공해야 합니다.

답변시 주의할 점은 고객이 남긴 이메일 주소와 뷰저블측의 공식 이메일 주소를 서로 혼동하여 답변하면 안됩니다. 고객이 수신 이메일을 남겼을 경우, 뷰저블의 공식 이메일 주소를 제시하여 한 번 더 문의 요청을 달라고 제안해줘야 합니다.
또한, 답변을 할 땐 마크다운을 최대한 이용해서 가시성이 확보된 답변을 해야 합니다. 특히 줄바꿈 및 들여쓰기를 적절히 활용해 주세요. 그리고 대답할 때 리스트 사이에 줄바꿈 간격 없이 대답해주세요. 답변은 아래 ‘맺음말’ 중 대화 본문에 자연스럽게 이어질 수 있는 하나를 골라 그것으로 마무리 해주세요. 맺음말을 고를때 유의할 점은 이전 대화에서 썼던 맺음말은 제외하고 나머지 맺음말중 자연스럽게 이어지는 하나를 골라 적용해야 합니다. 그리고 맺음말은 줄바꿈한 후에 덧붙여야 합니다.

‘맺음말’ 예시
1. 다른 궁금하신 사항이 또 있으실까요?
2. 답변이 도움이 되었을까요?

마지막으로 상담 전문가라는 자아를 스스로 부여하여 마치 사람처럼 답변해야 하고 답변 하기전 사실에 근거한 것인지 논리적으로 문제는 없는지 등을 한번 더 검토한 후 답변해주세요."""

DEFAULT_PROMPT_COMMENT = "[Sample Prompt] 작성하신 데이터(reference)에 맞게 프롬프트를 직접 작성해 사용하시면 더 좋은 답변을 얻으실 수 있습니다."
DEFAULT_MAIL_PROMPT_COMMENT = "[Sample Prompt] 기존 응대 스타일 및 톤에 맞게 프롬프트를 직접 작성해 사용하시면 더 좋은 답변을 얻으실 수 있습니다."

RAG_PROMPT = f"""<{RAG_NAME}>
{RAG_NAME}로 당신이 참고해야할 데이터를 전달했습니다. {USER_QUESTION_NAME} 답변에 필요한 데이터를 선별하고 이를 참고해 답변해주시길 바랍니다.
만약 참고해야할 {RAG_NAME}에 답변에 필요한 답변이 없다면 아래 사과문 예시 중 하나를 골라 답변해주시길 바랍니다.
'사과문' 예시
1. 죄송합니다. 제가 잘 알지 못하는 내용이에요. 질문주신 내용도 더 잘 답변할 수 있도록 열심히 공부할게요!
2. 제가 답변드리기 어려운 질문이네요.
</{RAG_NAME}>"""

CONVERSATION_HISTORY = """<대화 이력>
대화이력을 보고 대화흐름에 맞는 답변을 해주시길 바랍니다.
단, 가장 중요한건 사용자가 현재한 질문 내용입니다.
이 전에 같은 질문을 했다면 만족하지 못하고 다시 질문한 것일 수 있으니 이전 대화이력에 있는 대답을 똑같이 하지말고 다시 한번 생각해 대답해주시길 바랍니다.
</대화 이력>"""

CONVERSATION_HISTORY_MCP = f"""<도구 호출 전 대화 이력 확인>
도구 호출 전, 반드시 대화 이력을 확인해주세요.
사용자가 앞선 대화 맥락을 이어서 질문한다고 판단되는 경우, 도구 호출 전에 대화 이력을 확인해주세요.
특히, "이거", "그거", "아까", "방금", "이전에" 같은 대명사가 {USER_QUESTION_NAME}에 있다면 주의해서 대화이력을 봐주세요.
불명확한 경우, 사용자에게 확인 요청 후 답변해주세요.
- 예) "어떤 것을 말씀하시는건가요? 이 전에 물어본 OOO을 말씀하시는건가요?"
</도구 호출 전 대화 이력 확인>"""

URL_LINK_PROMPT = """<URL 링크 작성방법: 마크다운>
사용자가 당신이 작성한 답변에 있는 URL 링크를 클릭하면 해당 웹페이지로 이동할 수 있도록 마크다운 문법에 맞게 작성해 답변해주시길 바랍니다.
예를들어, 'https://example.com/ko/'란 웹페이지를 작성할 땐 [https://example.com/ko/](https://example.com/ko/)로 마크다운 문법에 맞게 작성해 답변해주시길 바랍니다.
</URL 링크 작성방법: 마크다운>"""

IMAGE_PROMPT = """<image_url 표출방법>
이미지 표출방법에 대해 설명드리겠습니다.
당신의 답변은 Markdown 형식으로 화면에 표출하고 있습니다.
따라서 마크다운에 맞춰 [참고 데이터]에 있는 데이터 중 답변에 활용한 데이터 내 imageURL이 있으면 이미지를 표출할 수 있도록 아래 내용을 추가해주시기 바랍니다.
![대체 텍스트](이미지 URL "선택적 제목")
</image_url 표출방법>"""

MULTI_LANG_PROMPT = f"""<답변 언어 선택>
가장 최신의 HumanMessage 내 {USER_QUESTION_NAME} 언어에 맞춰 답변을 해주시길 바랍니다.
만약 {USER_QUESTION_NAME}이 영어로 작성됐으면 답변을 영어로 번역해 답변해주시길 바랍니다.
만약 {USER_QUESTION_NAME}이 일본어로 작성됐으면 일본어로 대답해주세요.
만약 {USER_QUESTION_NAME}이 한국어로 작성됐으면 한국어로 대답해주세요.
다시 한번 말씀드립니다. 가장 최신의 HumanMessage 내 {USER_QUESTION_NAME}에 담긴 사용자 질문 언어에 맞춰 답변해주세요!
가장 최신의 HumanMessage 내 {USER_QUESTION_NAME} 아래에 사용자가 어떤 언어로 질문했는지 힌트를 남겨뒀으니 이를 참고해도 좋습니다.
반드시 사용자가 가장 최근에 질문한 언어에 맞춰 답변해주세요.
</답변 언어 선택>"""

TIME_PROMPT = f"""<날짜, 시간>
{RAG_NAME}에 '현재 UTC 시간'이란 title이 달린 데이터가 있습니다.
해당 데이터 content는 UTC 기준 사용자가 질문한 시간을 의미하며 hour는 0시부터 23시로 표현해 전달되니 참고바랍니다.
사용자가 시간 관련된 답변을 원할 시 활용해주시기 바랍니다.
사용자가 한국어로 질문했으면 한국시간, 일본어로 질문했으면 일본시간으로 바꿔서 답변해주세요. 
</날짜, 시간>"""


#ASK TOP3 PROMPT
SYSTEM_CONTENT = """
    넌 User Message에 담긴 질문들을 3가지로 요약해 정리하는 AI 에이전트야.
    
    User Message엔 ["질문1", "질문2", "질문3", "질문4", ...] 이런식으로 사람들의 질문들이 담겨있어.
    내가 원하는 답변 형태는 아래와 같아
    {"rank1": "", "rank1_count": "", "rank2": "", "rank2_count": "", "rank3": "", "rank3_count": ""}
    
    각 키에 대한 설명을 할게
    rank1: 요약했을 때 가장 많이 나온 질문1
    rank2: 요약했을 때 두번째로 많이 나온 질문2
    rank3: 요약했을 때 세번째로 많이 나온 질문3
    이때, 전체 질문 갯수 대비 각 카테고리에 대한 비율은 아래와 같아. % 없이 표현해줘
    rank1_count: rank1에 속해 요약된 질문들 갯수
    rank2_count: rank2에 속해 요약된 질문들 갯수
    rank3_count: rank3에 속해 요약된 질문들 갯수
    
    넌 다음과 같은 프로세스를 거쳐서 질문들을 정리해줘야해.
    1. 모든 질문을 파악해
    2. 의미가 유사한 질문들끼리 모아.
        - ["안녕?", "안녕하세요!", "안녕하세요", "잘가요", "안녕히가세요"] 이런 질문이 있으면 모아서 ["안녕?", "안녕하세요!", "안녕하세요"], ["잘가요", "안녕히가세요"] 이렇게 만들어줘
    3. 묶어둔 질문들의 대표질문들을 각각 만들어
        - ["안녕?", "안녕하세요!", "안녕하세요"] -> "안녕하세요"
        - ["잘가요", "안녕히가세요"] -> "안녕히가세요"
    4. 각 질문들의 빈도수를 세어
        - {"안녕하세요": 3, "안녕히가세요": 2}
    5. 빈도수가 높은 질문 순서대로 정렬해 순위를 매겨
        - {"안녕하세요": 3, "안녕히가세요": 2} -> {"rank1": "안녕하세요", "rank1_count": 3, "rank2": "안녕히가세요", "rank2_count": 2, "rank3": "", "rank3_count": 0}
    
    너가 답변해준 데이터는 answer 변수에 담아 다음과 같이 처리할거야
    parsed_answer = ast.literal_eval(answer)
    insert_value = (
        company_key,
        parsed_answer["rank1"],
        parsed_answer["rank1_count"],
        parsed_answer["rank2"],
        parsed_answer["rank2_count"],
        parsed_answer["rank3"],
        parsed_answer["rank3_count"],
        self.target_date,
        self.period,
        self.questions[company_key]["count"]
    )
    
    너가 정해진 답변 이외 형태로 답변을 하면 에러가 발생하겠지? 그러니 정해진 답변 형태로 답변해줘
    다시 한번 강조할게 정해진 답변 형태는 아래와 같아!
    {"rank1": "", "rank1_count": "", "rank2": "", "rank2_count": "", "rank3": "", "rank3_count": ""}
"""

# LANGUAGE
KOREAN = "ko"
ENGLISH = "en"
JAPANESE = "ja"

# LANGUAGE_MESSAGE
KOREAN_MESSAGE = "사용자가 한글로 질문했으니, 한글로 답변해주세요."
ENGLISH_MESSAGE = "Since the user asked in English, please respond in English."
JAPANESE_MESSAGE = "ユーザーが日本語で質問したので、日本語で答えてください。"
OTHER_MESSAGE = "[질문]에 사용자가 요청하는 언어가 있으면 요청하는 언어로 답변해주세요. 만약 [질문]에 요청하는 언어가 없으면 시스템 프롬프트에 지정한 언어가 있는지 확인하고 해당 언어로 답변해주세요. 만약 시스템 프롬프트에 지정한 언어가 없으면 사용자 질문의 언어와 동일한 언어로 답변해주세요."

# GREETING
INIT_GREETING_KO = """안녕하세요, LLM Platform입니다!
저에게 궁금한 점이 있다면 질문해주세요 🥰"""
INIT_GREETING_JA = """こんにちは、LLM Platformです！
何か気になることがあれば、ぜひ質問してくださいね 🥰"""
INIT_GREETING_EN = """Hello, this is LLM Platform!
If you have any questions, feel free to ask me 🥰"""


# OPERATION CONSTANTS
RESULT = "result"
PROMPT = "prompt"
QUERY = "query"
REFER = "refer"


# EMAIL ADDRESS
CERTIFICATION_EMAIL_TEMPLATE_NAME = "llmPlatformUserCertification"
INVITATION_EMAIL_TEMPLATE_NAME = "llmPlatformUserInvite"
FIND_PASSWORD_EMAIL_TEMPLATE_NAME = "llmPlatformUserFindPassword"
EMAIL_SERVICE_CODE = 1
EMAIL_ADDRESS="noreply@example.com"
EMAIL_INVITE_SUBJECT_KO = "[LLM Platform] 서비스 가입을 위한 인증 메일입니다."
EMAIL_INVITE_SUBJECT_JA = "[LLM Platform]メールアドレス認証のご案内"
EMAIL_INVITE_SUBJECT_EN = "[LLM Platform] This is a verification email for service registration."
EMAIL_CERTIFI_SUBJECT_KO = "[LLM Platform] 이메일 인증 안내"
EMAIL_CERTIFI_SUBJECT_JA = "[LLM Platform]メールアドレスを認証してください。"
EMAIL_CERTIFI_SUBJECT_EN = "[LLM Platform] Email Verification Instructions"
EMAIL_THREAD_SPLITTER = "-----Original Message-----"

# parser
PARSER_RABBITMQ_QUEUE_NAME = "llm-platform-file-parser"
PARSER_S3_BUCKET_NAME = "llm-platform-file-parser"

# PARSER ERROR
SUCCESS = "success"
ERROR = "error"
PARTIAL_ERROR = "partial_error"

# FILE STATUS IN DRIVE
FAILED = 0
PENDING = 1
SUCCESS_TO_S3 = 2
ANALYZING=3
FINISHED = 4

PARSER_FAILED = 5
PARSER_FAILED_NOT_SAME_COUNT = 6
PARSER_FAILED_UPDATE_TO_VECTOR_DB = 7
PARSER_FAILED_DECREASE_PARSER_CREDIT_AVAILABLE = 8
PARSER_PARTIAL_ERROR = 12

FAIL_TO_UPLOAD_TO_S3 = 9
FAIL_TO_DB = 10
FAIL_TO_SEND_MESSAGE = 11

ERROR_STATUS_LIST = [PARSER_FAILED, PARSER_FAILED_NOT_SAME_COUNT, PARSER_FAILED_UPDATE_TO_VECTOR_DB, PARSER_FAILED_DECREASE_PARSER_CREDIT_AVAILABLE, PARSER_PARTIAL_ERROR, FAIL_TO_UPLOAD_TO_S3, FAIL_TO_DB, FAIL_TO_SEND_MESSAGE]


# CX_EMAIL_STATUS
EMAIL_RECIEVED = "parsed"
EMAIL_PENDING = "pending"
EMAIL_ANSWERING = "answering"
EMAIL_SENT = "sent"
EMAIL_CLOSED = "close"
EMAIL_SPAM = "spam"

# EMAIL RAG
EMAIL_HISTORY_SET_MANAGER = 1
EMAIL_HISTORY_CREATE_CONTENT = 2
EMAIL_HISTORY_EDIT_CONTENT = 3
EMAIL_HISTORY_SENT = 4
EMAIL_HISTORY_EDIT_TO_PENDING = 5
EMAIL_HISTORY_EDIT_TO_ANSWERING = 6
EMAIL_HISTORY_EDIT_TO_SENT = 7
EMAIL_HISTORY_EDIT_TO_CLOSED = 8
EMAIL_HISTORY_EDIT_TO_SPAM = 9
EMAIL_HISTORY_EDIT_TO_UPDATE_RECEIVED_COMMENT = 10

# MAIL RECEIVE SOURCE
MAIL_SOURCE_IMAP = "imap"
MAIL_SOURCE_SES = "ses"
MAIL_SOURCE_LIST = [MAIL_SOURCE_IMAP, MAIL_SOURCE_SES]
MAIL_RECEIVE_MIN_INTERVAL_SEC = 15
MAIL_RECEIVE_FETCH_LIMIT = 50
