# LLM Platform - RAG 지식 플랫폼 & AI 메일 CX (SaaS → 설치형)

> 설치 및 실행 절차는 [INSTALL.md](INSTALL.md), 서비스별 상세는 [api/README.md](api/README.md), [llm-proxy/README.md](llm-proxy/README.md), [mcp-agent/README.md](mcp-agent/README.md)를 참고하세요.

## 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 프로젝트명 | LLM Platform |
| 역할 | 리드 개발 (Backend / LLM Proxy / Vector / Infra) — 프론트엔드와 엑셀 파일 임베딩(파서 측)을 제외한 전 영역 설계·구현 |
| 기간 | 2024.12 ~ 2026.03 |
| 한 줄 요약 | 사내 문서·게시글·고객 메일을 하나의 벡터 인덱스로 묶어 LLM이 근거를 들어 답하고, 고객 문의 메일의 답장 초안까지 만들어 주는 멀티테넌트 RAG 플랫폼 |

LLM Platform은 기업이 가진 지식(파일, 게시글, 웹사이트, 고객 메일)을 업로드하면 자동으로 파싱·청킹·임베딩해 두고, 플레이그라운드 채팅·외부 공개 챗봇·AI 메일 답변 초안에서 같은 지식을 재사용하는 SaaS입니다. 백엔드(`api`), 멀티 벤더 LLM 프록시(`llm-proxy`), 벡터 저장소 계층(Pinecone → Milvus)과 인프라를 설계하고 구현했습니다. 단순 챗봇이 아니라 문서 파이프라인, 하이브리드 검색, MCP 도구 호출, 메일 수집·발송, 요금제·크레딧 과금까지 하나의 백엔드에서 처리합니다.

## 포트폴리오 개요

| 항목 | 내용 |
|---|---|
| 포트폴리오명 | LLM Platform 설치형 전환 및 리팩터링 (`llm-platform`) |
| 소속 | zeongzaehoon |
| 역할 | ALL |
| 기간 | 2026.10 ~ |
| 한 줄 요약 | SaaS 전용 의존(Pinecone·S3·Slack)을 걷어내고 폐쇄망에서 `docker compose up` 한 번으로 올라가는 설치형 배포판 |

이전 직장에서 개발한 LLM Platform을 고객사 폐쇄망에 설치할 수 있도록 외부 의존을 교체(Pinecone → Milvus, S3 → MinIO)하고, 스키마 드리프트·메일 수집 누락·인증 세션 끊김 같은 운영 결함을 잡으며 리팩터링하고 있습니다. 브랜딩을 제거해 화이트라벨로 배포할 수 있게 했고, 모니터링·로그 수집 스택을 번들에 포함했습니다.

`Playground` `Drive` `Reference` `Chatbot` `AI Mail` `MCP` `Hybrid Search` `Plan/Credit` `Monitoring`

## 기술 스택

**Backend**
`Python 3.14` `FastAPI` `Gunicorn + Uvicorn` `asyncio` `SQLAlchemy(async) + aiomysql/asyncmy` `Alembic` `Redis` `aio-pika(RabbitMQ)` `aioboto3(S3/MinIO/SES)` `PyMilvus 2.6` `Pinecone` `python-jose(JWT)` `aiosmtplib` `fastText` `tiktoken` `Pydantic 2` `httpx`

**LLM Proxy**
`FastAPI` `openai` `anthropic` `boto3(Bedrock Converse)` `google-genai(Gemini + FileSearch)` `xAI` `vLLM(OpenAI 호환)` `FastMCP client` `NDJSON streaming`

**Frontend** (동료 구현, 리팩터링 단계에서 일부 기여)
`Vue 3` `Vite` `Vuex` `vue-router` `vue-i18n` `axios` `ECharts` `CKEditor 5` `pnpm`

**Infra / DevOps**
`Docker Compose(18 services)` `Nginx` `MySQL` `Milvus 2.6 + etcd + Attu` `MinIO` `RabbitMQ` `Prometheus` `Grafana` `cAdvisor` `ClickHouse` `uv + hash-pinned requirements.lock`

## 시스템 아키텍처

```
┌───────────────────────────────────────────────────────────────┐
│                  Vue 3 Frontend (web :3333)                   │
│  Playground / Drive / Reference / AI Mail / Admin / Chatbot   │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│               Nginx Reverse Proxy (host :4331)                │
│  /            → web            /llm-platform-api/ → api (180s SSE) │
│  /vector/     → Attu(Milvus)   /mq/          → RabbitMQ UI    │
│  /monitoring  → Grafana                                       │
└───────────────────────────────┬───────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────┐
│                  FastAPI Backend (api :8888)                  │
│                                                               │
│  user · admin · company · plan · prompt · monitoring · geo    │
│  drive · reference · playground · chatbot · email · emailrag  │
│                                                               │
│  ┌────────────┐ ┌────────────┐ ┌─────────────┐ ┌───────────┐  │
│  │  RunLLM    │ │  RunMCP    │ │ RunLLMEmail │ │ Retrieval │  │
│  │ RAG+Stream │ │ Tool Loop  │ │ Mail Draft  │ │ BM25+Dense│  │
│  └─────┬──────┘ └─────┬──────┘ └──────┬──────┘ │   (RRF)   │  │
│        └──────────────┼───────────────┘        └─────┬─────┘  │
│                       │                              │        │
│  ┌────────────────────▼──────────┐   ┌───────────────▼──────┐ │
│  │  MailReceiverRunner (IMAP/SES)│   │ Parser (RabbitMQ →   │ │
│  │  lifespan 백그라운드 폴링       │   │ callback_from_parser)│ │
│  └───────────────────────────────┘   └──────────────────────┘ │
└───┬─────────┬──────────┬──────────┬──────────┬────────────────┘
    │         │          │          │          │
┌───▼───┐ ┌───▼───┐ ┌────▼────┐ ┌───▼───┐ ┌────▼─────┐
│ MySQL │ │ Redis │ │ Milvus  │ │ MinIO │ │ RabbitMQ │
│ 36 tbl│ │ 대화   │ │ dense + │ │ 파일   │ │ 파서 큐   │
│       │ │ 컨텍스트│ │ sparse  │ │ 메일   │ │          │
└───────┘ └───────┘ └─────────┘ └───────┘ └──────────┘
                                              │
            ┌─────────────────┐     ┌─────────▼────────┐
            │  MCP Agent      │◀───▶│  LLM Proxy       │
            │  (FastMCP, 32   │     │  OpenAI/Claude/  │
            │   tools)        │     │  Bedrock/Gemini/ │
            └─────────────────┘     │  xAI/vLLM        │
                                    └──────────────────┘

  Observability: cAdvisor + container-name-exporter → Prometheus → Grafana
                 logs 컨테이너(docker logs 주기 수집, 30일 보존) · ClickHouse
```

## 주요 기능

| 영역 | 기능 | 구현 포인트 |
|---|---|---|
| **플레이그라운드** | 사내 지식 기반 RAG 채팅, 근거 문서 패널, 대화 제목 자동 생성, 평점·코멘트 | `RunLLM`이 프롬프트·검색·대화 이력을 병렬 조회 후 스트리밍. 근거는 게시글·파일 페이지·메일·사이트맵 4종을 하나의 응답으로 통합 |
| **파일 드라이브** | 폴더 트리 업로드, 비동기 파싱, 페이지 단위 벡터화, 파싱 실패 재시도, 파일 크레딧 | 업로드 즉시 응답 → RabbitMQ → 파서 → 콜백 → 청킹(500 토큰, 150 겹침) → 임베딩 배치 → 벡터 upsert |
| **Reference** | 마크다운/리치텍스트 게시글, 카테고리, 임시저장, 토큰 수 미리보기 | 저장 시 벡터 인덱스와 (SaaS) Gemini FileSearch 스토어에 동시 적재. 삭제 시 크롤러 사이트맵 행까지 정리 |
| **공개 챗봇** | 외부 사이트에 심는 위젯, 익명 세션 | Redis 세션 키(TTL 30분)로 로그인 없이 회사 지식에 답변. 크레딧·플랜 검사 동일 적용 |
| **AI 메일** | IMAP/SES 수집, 받은편지함·스레드, RAG 답장 초안, 담당자·상태 워크플로, SMTP/SES 발송, 바운스 회수, 대시보드 | `RunLLMEmail`이 과거 답변·참고자료·문서 검색을 합쳐 HTML 답장 생성. 수집 설정·커서는 DB 암호화 저장 |
| **MCP 에이전트** | 회사별 MCP 서버·토큰·허용 툴 등록, 도구 선택 채팅, 사용 도구 기록 | `RunMCP` → 프록시 `/chat_mcp`가 벤더별 tool-calling 포맷으로 변환해 다중 스텝 실행 |
| **요금제·크레딧** | 플랜 조회/변경/업그레이드, 월 단위 전환, 결제 이력, 답변당 크레딧 차감, 파일 크레딧 | 답변 완료 콜백에서 `credit_available` 원자적 감소 + `credit_history` 기록 |
| **관리** | 멤버 초대 메일·수락·권한 변경·언어, 프롬프트/인사말 버전, 대화 모니터링(상위 질문·평점·건수) | 초대 키를 서명해 수락 URL 생성, 모니터링은 주간 집계 |
| **다국어** | 질문 언어 자동 감지, 언어별 지시문 | fastText 모델을 부팅 시 스레드에서 로드, 일본어 등 언어별 시스템 메시지 분기 |
| **기타** | 클라이언트 IP 지리정보(캐시), 이미지 입력(멀티모달) 채팅 | 프록시 `OcrChatPayload`로 base64/URL 이미지 최대 20장 |

## 핵심 성과 및 기술적 도전

### 0. 요약

```
[프로젝트] 멀티 LLM 프록시 설계 (llm-proxy)
  + OpenAI·Azure·Anthropic·Bedrock·Gemini·xAI·vLLM 8개 클라이언트를 단일 NDJSON 스트림 계약으로 통일
  + 1차/2차 벤더 폴백, 첫 청크 타임아웃, 컨텍스트 초과 사전 차단, 스트림 중 에러 청크
[프로젝트] RAG 오케스트레이션 (api)
  + 프롬프트·벡터 검색·대화 이력·언어 감지를 asyncio.gather 로 병렬화해 첫 토큰까지 지연 최소화
  + 게시글·파일·메일·사이트맵 4개 출처를 하나의 근거 묶음으로 통합, 답변에서 원본 페이지 역참조
[프로젝트] 벡터 저장소 계층 (api, vector)
  + Pinecone/Milvus 를 같은 메서드 계약(insert/find/find_lexical/fetch/update/remove)으로 추상화
  + Milvus 2.6 BM25 sparse + dense 하이브리드, RRF 융합, 지문 기반 증분 reindex
[프로젝트] 문서 파싱 비동기 파이프라인 (api, message-queue)
  + 업로드 → 큐 → 파서 → 콜백 → 청킹·임베딩 → upsert, 상태 머신·부분 실패·재시도·크레딧을 DB 로 추적
[프로젝트] MCP 에이전트 (api, llm-proxy, mcp-agent)
  + 회사별 MCP 서버·허용 툴을 DB 로 관리, 벤더별 tool-calling 포맷 변환, 32개 툴 FastMCP 서버
[프로젝트] AI 메일 CX (api)
  + IMAP/SES 수집기(lifespan 백그라운드), RAG 답장 초안, SMTP/SES 발송·바운스, 대시보드
[프로젝트] 멀티테넌트 운영 (api)
  + 회사 단위 인덱스/네임스페이스 격리, 플랜·크레딧 과금, 멤버 초대, 프롬프트 버전, 모니터링
[프로젝트] SaaS → 설치형 전환과 운영 안정성 (api, compose)
  + SERVER_STAGE 분기로 Pinecone/S3/Slack → Milvus/MinIO 교체, 18 컨테이너 번들
  + Alembic, Python 3.14 + 해시 고정 lock, 격리 컨테이너 통합 테스트, 관측성 번들
```

### 1. 멀티 LLM 프록시(llm-proxy): 벤더 종속 제거와 스트리밍 계약

**문제**: OpenAI, Azure OpenAI, Anthropic, AWS Bedrock, Google Gemini, xAI, 그리고 사내 vLLM까지 벤더마다 메시지 포맷·이미지 입력·tool-calling·스트리밍 이벤트가 전부 달랐습니다. 벤더 장애가 그대로 서비스 장애가 되고, 모델 교체 때마다 비즈니스 코드를 고쳐야 했습니다.

**해결**: 별도 프로세스인 LLM Proxy가 벤더를 감추고, 서비스는 `vendor`/`model` 문자열만 넘깁니다.

```python
# llm-proxy/helper/llm.py
async def safe_stream(first_client, second_client, session_key=None):
    try:
        async for chunk in first_client.stream(is_retry=False):
            yield chunk
    except FirstTryError:                      # 폴백 트리거는 이 예외뿐
        try:
            async for chunk in second_client.stream(is_retry=True):
                yield chunk
        except OverTokenLimitError:            # 재시도해도 실패할 예외는 원형 유지
            raise
        except Exception as e:
            raise ProxyServerError() from e    # 2차 실패는 정규화
```

- `client/` 의 벤더별 클라이언트(OpenAI, Azure, Anthropic, Bedrock, Google, xAI, 로컬, vLLM)가 같은 인터페이스(`stream`, `stream_with_mcp`, `chat`, `embeddings`, `function_call`)를 구현합니다. 각 클라이언트가 대화 이력·시스템 프롬프트·이미지·툴 정의를 자기 벤더 포맷으로 변환합니다.
- 모든 벤더가 같은 청크 스키마 `{"iteration", "text", "model", "vendor", "tool_name", "tool_text", "is_end", "is_error"}`를 NDJSON으로 내보내므로 프론트는 벤더를 모릅니다.
- `set_client`가 stage·벤더에 따라 1차/2차 클라이언트 쌍을 고르고, `safe_*` 래퍼는 `FirstTryError`에만 폴백합니다. 재시도는 2차까지로 제한합니다.
- `check_token_length`가 tiktoken으로 입력 길이를 재서 모델 컨텍스트(200k/128k)를 넘기면 호출 전에 `OverTokenLimitError`로 끊습니다. 벤더 과금 없이 사용자 안내가 나갑니다.
- `iter_with_first_text_timeout`으로 첫 텍스트 청크가 제때 오지 않으면 폴백 경로로 넘깁니다.
- 스트림 시작 후에는 HTTP 상태를 바꿀 수 없으므로 `is_error` 청크로 한국어 안내 문구를 내려 화면에 표시합니다. 서러게이트 문자는 직렬화 전에 정리합니다.
- 멀티모달: base64/URL 이미지를 판별·확장자 추론 후 벤더 포맷으로 넣습니다(최대 20장). Gemini FileSearch 스토어 생성·업로드·삭제 API도 프록시가 감쌉니다.
- `/chat_on_queue`는 대량 생성 작업을 RabbitMQ로 넘깁니다.

**API 쪽 클라이언트**(`client/groxy.py`)는 용도별 named connection(`stream`, `embedding` 등)에 `httpx.Limits`/`Timeout`과 `asyncio.Semaphore`(스트리밍 30, 임베딩 10)를 두고, `ConnectError`/`RemoteProtocolError`에서 재연결 후 1회만 재시도합니다.

**성과**: 회사별 `plan_info.model` 값만 바꾸면 벤더가 바뀌고, 설치형에서는 vLLM으로 완전 오프라인 운용이 가능합니다. 벤더 장애 시 사용자는 2차 벤더 응답을 받습니다.

### 2. RAG 오케스트레이션(RunLLM): 4개 출처 통합과 병렬 조회

**문제**: 질문 하나에 시스템 프롬프트(MySQL), 벡터 검색(Pinecone/Milvus), 근거 원문(MySQL + S3), 대화 이력(Redis), 언어 감지(fastText)가 모두 필요했습니다. 순차 조회는 첫 토큰이 늦고, 근거는 게시글·파일·메일·사이트맵으로 저장 위치가 제각각이었습니다.

**해결**: `module/LLM/activate.py`의 `RunLLM`이 한 번의 `activate()`로 전 단계를 묶습니다.

```
RunLLM.activate()
  ├─ _get_language_message   fastText 감지 → 언어별 지시문
  ├─ _get_retrieval_data     query_vector → match → 출처별 원문 조회
  │     post(refer_id) · parser(drive 페이지, S3) · email · sitemap  ← asyncio.gather
  ├─ _get_conversation_history   Redis 리스트 (rpush/lrange)
  ├─ _get_prompt             회사 프롬프트 버전 + placeholder 치환 + 현재 UTC 시간 주입
  └─ _run → LLM Proxy 스트리밍 → callback: 크레딧 차감 · chat_history 저장 · Redis 갱신
```

- 벡터 검색 결과의 메타데이터(`data_type`, 원본 ID, 페이지)로 출처별 원문 조회기를 호출하고, 파일 원문은 S3에서 해당 페이지만 내려받습니다.
- 같은 `chatDomain`을 플레이그라운드·공개 챗봇·MCP가 공유해 검색·이력·과금 코드가 한 벌입니다.
- 답변 콜백은 `UPDATE company_info SET credit_available = credit_available - 1 WHERE ... AND credit_available > 0`로 원자적으로 차감하고 `credit_history`를 남깁니다.
- `chat_history`에 `refer_id/parser_id/email_id/sitemap_id`, 소요 시간(`elapsed_info`), 모델·토큰을 기록해 화면에서 근거와 비용을 추적합니다.

**성과**: 지연이 가장 긴 소스 기준으로 응답이 시작되고, 한 답변 안에서 "이 게시글 · 이 PDF 3페이지 · 이 메일"을 함께 근거로 보여줍니다.

### 3. 벡터 저장소 계층: Pinecone → Milvus 하이브리드 검색

**문제**: SaaS는 Pinecone dense 검색만 썼습니다. 제품명·오류코드처럼 정확히 일치해야 하는 질의에서 재현율이 떨어졌고, 설치형에서는 외부 벡터 DB를 쓸 수 없었습니다.

**해결**: 벡터 클라이언트 계약을 먼저 고정하고 구현을 바꿨습니다.

- `client/pinecone.py`와 `client/milvus.py`가 같은 메서드(`insert/insert_many/find/find_lexical/fetch/update/remove`)를 제공해 `RunLLM`·파서 콜백·게시글 저장은 저장소를 모릅니다. 회사별 `vector_db_index/namespace`로 테넌트를 격리합니다.
- Milvus 2.6의 BM25 Function으로 sparse 벡터를 서버 측에서 생성하고, dense와 sparse를 **Reciprocal Rank Fusion**으로 합칩니다.

```python
schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dimension)      # VECTOR_DIMENSION, 기본 1024
schema.add_field("sparse", DataType.SPARSE_FLOAT_VECTOR)
schema.add_function(Function(input_field_names=["text"], output_field_names=["sparse"],
                             function_type=FunctionType.BM25))
indexes.add_index("sparse", index_type="SPARSE_INVERTED_INDEX", metric_type="BM25")
```

- `module/Retrieval/core.py`는 dense·lexical 백엔드를 `Protocol`로 받아 병렬 실행하고, 점수 단위가 다른 BM25/코사인을 비교하지 않고 **순위만** 융합합니다. `SearchScope`로 회사·문서 범위를 제한합니다.
- 레거시 dense 전용 컬렉션은 감지해 경고하고, `scripts/reindex.py`가 메타데이터 지문(fingerprint)으로 바뀐 청크만 증분 이관합니다. 임베딩 차원은 환경변수로 받아 로컬 임베딩 모델 교체에 대응합니다.
- 동기 SDK 호출은 `asyncio.to_thread`로 감싸 이벤트 루프를 막지 않습니다.

**성과**: 외부 의존 없이 키워드·의미 검색을 동시에 만족하는 단일 인덱스. `tests/test_milvus_integration.py`가 실제 Milvus 2.6.11에서 BM25·벡터·이관을 검증합니다.

### 4. 문서 파싱 비동기 파이프라인

**문제**: PDF·오피스 문서 파싱은 수십 초가 걸리고 실패도 잦습니다. 요청-응답 안에서 처리하면 타임아웃과 중복 과금이 발생했습니다.

**해결**: 업로드와 파싱을 분리한 콜백 파이프라인을 만들었습니다. (엑셀 전용 파싱·임베딩은 파서 담당 동료가 구현)

```
POST /drive/upload_file
  → S3/MinIO 저장 + drive/upload_file 행(status=대기), 파일 크레딧 선차감
  → RabbitMQ(PARSER_RABBITMQ_QUEUE_NAME)에 작업 발행 (callbackUrl 포함)
파서 완료 → POST /drive/callback_from_parser
  → 페이지별 chunking_text(500 토큰, 150 겹침, tiktoken)
  → LLM Proxy /embeddings 배치 호출(세마포어 10) → 벡터 upsert → vector 테이블 매핑
  → PARSER_PARTIAL_ERROR 는 error_page 기록, 실패는 /drive/retry 로 재투입
```

- `drive`·`drive_path`로 폴더 트리, 이동·이름변경·삭제 예약(`will_be_deleted_date`)을 지원합니다.
- 같은 청크 ID를 벡터 DB와 MySQL `vector` 테이블이 공유해 검색 결과에서 원본 페이지로 역참조합니다.
- `file_credit_history`로 파일 단위 과금 이력을 남기고, 회사의 `parser_credit_available`로 기능을 켜고 끕니다.

**성과**: 업로드 응답은 즉시 반환되고 파싱 상태를 화면에서 폴링합니다. 파서 장애가 API 가용성에 영향을 주지 않습니다.

### 5. MCP 에이전트: 회사별 도구 관리와 벤더별 tool-calling

**문제**: 문서 Q&A를 넘어 통계 조회·외부 발행처럼 도구를 호출하는 요청이 늘었고, 고객사마다 허용할 도구가 달랐습니다. 벤더마다 tool-calling 스키마도 달랐습니다.

**해결**:

- `company_info.mcp_server / mcp_token / mcp_allowed_tools`로 회사별 서버·인증·허용 툴을 관리하고 `/playground/get_mcp_tools`가 목록을 돌려줍니다.
- `RunLLM`(단일 스텝)과 `RunMCP`(다중 스텝)를 같은 `chatDomain`으로 분기합니다. `RunMCP`는 프록시 `/chat_mcp`에 서버 URL·토큰·허용 툴을 넘기고, 프록시의 `FastMCPClient`가 `list_tools`/`call_tool`을 타임아웃과 함께 수행합니다.
- 각 벤더 클라이언트의 `stream_with_mcp`가 MCP 툴 정의를 OpenAI function, Bedrock Converse `toolSpec`, Gemini function declaration으로 변환하고, 툴 호출 → 결과 주입 → 재호출 루프를 돌며 `tool_name/tool_text` 청크로 진행 상황을 스트리밍합니다.
- `chat_history.is_mcp / mcp_tools`에 사용 도구를 남겨 모니터링 화면에서 추적합니다.
- 동봉한 `mcp-agent`(FastMCP)는 지식베이스 검색, 게시글·이메일 통계, 응답시간 분석, 페이지 GEO(생성형 엔진 최적화) 가이드, SNS/WordPress 발행 등 32개 툴을 제공합니다.

**성과**: 소스 배포 없이 관리 화면에서 도구를 켜고 끄는 에이전트. 도구 호출 과정이 텍스트가 아니라 구조화된 청크로 화면에 흘러갑니다.

### 6. AI 메일 CX: 수집 → RAG 답변 초안 → 발송

**문제**: 고객 문의 메일을 사람이 전부 읽고 답하던 흐름을, 회사 지식과 과거 답변을 근거로 초안을 만들어 담당자가 검토·발송하는 흐름으로 바꿔야 했습니다. 설치형에서는 수집 서비스가 없어 받은편지함이 비어 있었습니다.

**해결**:

- **수집**: `mail_receive_setting`에 IMAP(호스트·폴더·UIDVALIDITY·last_uid) 또는 SES(버킷·prefix·last_modified) 커서를 저장하고, `MailReceiverRunner`가 `lifespan`에서 떠서 활성 설정마다 `poll_interval_sec` 간격으로 폴링합니다. 비밀번호·시크릿은 `*_enc` 컬럼에 암호화합니다. 본문 HTML·첨부·CID 이미지는 S3/MinIO에 두고 `cx_email`에 적재합니다.
- **초안**: `RunLLMEmail`이 과거 답변(`cx_email_history`)·참고 자료(`cx_email_references`)·문서 벡터 검색을 합쳐, 인사말·본문·맺음말 구조의 HTML 답장을 스트리밍 생성합니다. 회사별 메일 프롬프트는 버전 관리됩니다.
- **워크플로**: 담당자 배정, 상태 변경(action code), 코멘트, 임시 저장, 첨부 diff 반영, 스레드 중복 답변 방지(`HasThreadError`).
- **발송**: 회사별 SMTP(`mail_smtp_setting`, `aiosmtplib`) 또는 SES. 바운스는 `/get_ses_bounce`로 회수하고 `email_send_history`에 남깁니다. 대시보드(`/get_dashboard_chart|line|manager_count`)로 처리량을 봅니다.

**성과**: 관리자가 메일 계정만 등록하면 받은편지함이 채워지고 답장 초안이 생성됩니다. `tests/test_mail_receiver.py`, `test_mail_send_smtp.py`로 수집·발송을 단위 검증합니다.

### 7. 멀티테넌트 운영: 플랜·크레딧·초대·모니터링

- **테넌트 격리**: 모든 테이블이 `company_key`를 갖고, 벡터 인덱스/네임스페이스·MCP 설정·프롬프트·발신 주소가 회사 단위입니다.
- **플랜/크레딧**: `plan_info`(모델·최대 토큰·초기 크레딧)와 월 단위 전환 로직(`helper_upgrade_next_month_plan_update`), 결제·변경 이력. 답변·파일 단위로 크레딧을 차감하고 소진 시 `NoCreditError`, 만료 시 `ExpiredPlanError`로 사내 코드(9000대) 응답.
- **멤버 초대**: 초대 키를 서명해 수락 URL을 만들고 메일 발송, 재초대·권한 변경·언어 설정.
- **공개 챗봇**: 회사 키로 발급한 세션 키를 Redis에 TTL 30분으로 두고 익명 세션을 유지합니다.
- **모니터링**: 세션별 대화 조회(head/tail 페이지네이션), 평점·건수 주간 집계, 상위 질문 키워드(`ask_top`).
- **인증**: JWT access 1일 / refresh 3일, `Depends` 체인(`get_current_user → get_user_info`)에서 회사·플랜·크레딧 정보를 한 번에 주입, `TokenError`는 전역 핸들러로 401.

### 8. 에러 체계와 로깅 규약

- 모든 예외는 `AppError`를 상속하고 `code`에 실제 HTTP 상태를 둡니다: `DBError`, `MemoryDBError`, `VectorDBError`, `AWSError`, `MessageQueueError`, `LLMProxyError`, `LLMStreamingError`, `TokenError`(401), `ForbiddenError`(403), `DataError`(400), 도메인 거부(`ExpiredPlanError`, `NoCreditError`, `HasThreadError`).
- 레이어별 정책: `client/*`는 IO 예외만 변환, `queries/*`는 `DBError`, `helper/*`는 통과, `api/*`는 `@handle_errors()` 하나. 스트리밍 시작 후 예외만 라우트에서 잡아 `asyncio.gather`로 보상(레코드 삭제·Slack 알림)합니다.
- 로그는 `[모듈.클래스.메서드] 이모지 메시지` + `session_key` 포맷으로 요청 단위 추적이 됩니다. 시크릿·프롬프트 본문은 남기지 않습니다.
- IO 클라이언트는 클래스 레벨 싱글턴 + `asyncio.Lock`, `check_connection()` 재연결, 풀 획득 시 ping 검증 + 백오프 3회, 트랜잭션은 컨텍스트 매니저로만.

### 9. SaaS → 설치형(폐쇄망) 전환

**문제**: SaaS 코드는 Pinecone, AWS S3/SES, Slack, Google FileSearch 같은 외부 서비스를 전제로 작성돼 있었습니다. 고객사 폐쇄망에는 인터넷이 없고, 설치 담당자는 명령 하나로 띄우기를 기대합니다.

**해결**: `SERVER_STAGE=docker` 하나로 인프라 조합이 바뀌도록 `lifespan`에서 클라이언트 묶음을 분기했습니다.

```python
clients = [
    (LLMProxyClient.connect, LLMProxyClient.disconnect),
    (MySQLClient.connect, MySQLClient.disconnect),
    (RedisClient.connect, RedisClient.disconnect),
    (RabbitMQClient.connect, RabbitMQClient.disconnect),
]
if os.getenv("SERVER_STAGE", DEV) == DOCKER:
    clients.append((MilvusClientConnector.connect, MilvusClientConnector.disconnect))
else:
    clients.extend([(S3Client.initialize, S3Client.close),
                    (PineconeClientConnector.initialize, PineconeClientConnector.disconnect),
                    (SlackClient.connect, SlackClient.disconnect)])
for connect, disconnect in clients:
    resources.push_async_callback(disconnect)   # AsyncExitStack: 획득 역순으로 정리
    await connect()
```

- `AsyncExitStack`으로 초기화 중 실패해도 이미 획득한 커넥션은 역순으로 정리됩니다.
- 부팅 시 `init_db()`로 테이블을, `init_admin()`으로 master 회사·관리자 계정을 `ADMIN_*` 환경변수에서 멱등 생성합니다.
- 서비스 18개를 compose 한 벌로 묶고 호스트에는 nginx(4331)·MySQL·LLM 프록시·ClickHouse 포트만 노출했습니다. 기존 설치본과 동시 검증할 수 있도록 컨테이너명·이미지명·네트워크·포트를 `-refac`로 분리했습니다.
- 프론트 브랜딩(로고·마스코트·회사 정보·도입상담)을 제거하고 제품명을 `VITE_APP_NAME`으로 받는 화이트라벨로 바꿨습니다.

**성과**: 빈 MySQL·빈 Milvus 상태에서 `docker compose up -d` 후 바로 로그인·업로드·검색이 되는 설치본.

### 10. 스키마 드리프트, 빌드 재현성, 관측성

- **Alembic** 도입(`0001_baseline` → `0004_mail_smtp_setting`). 모델 자동 import로 등록 누락을 막고, 문자열 `"NULL"` 기본값 같은 함정을 제거했습니다. `create_all`만으로는 기존 설치본에 컬럼이 추가되지 않아 로그인까지 깨지던 문제의 근본 해결입니다.
- **Python 3.14 + 해시 고정 lock**: API·프록시·MCP·exporter 각각 `uv pip compile --generate-hashes`로 만든 `requirements.lock`으로만 설치하고 Docker 빌드도 같은 파일을 씁니다.
- **격리 통합 테스트**: `compose.test.yaml`은 운영 볼륨·env를 절대 마운트하지 않는 일회용 인프라로, `scripts/validate.sh`가 빌드→부팅→Milvus 검색·이관→회원가입·로그인→`/user/get_info`까지 확인합니다. 단위 테스트 13개(lifespan, retrieval, milvus, mail, proxy transport 등).
- **관측성 번들**: cAdvisor + 자체 `container-name-exporter` → Prometheus → Grafana(provisioning), `logs` 컨테이너의 `docker logs` 주기 수집(30일 보존), Attu·RabbitMQ UI를 nginx 뒤에 배치.
- **세션 안정화**(web-refac): JWT를 쿠키에서 localStorage로 옮기고 401 응답 인터셉터가 `/user/refresh_token`으로 재발급 후 1회 재시도. 서버 `to_orjson()`이 실제 HTTP 상태코드를 싣도록 고쳐 응답 계약을 맞췄습니다.

## 데이터 모델

### MySQL (36 테이블, Alembic 관리)

```
MySQL
├── 계정/조직     user_info · user_auth · company_info · invite_history · login_history
│                 password_reset_history
├── 요금/크레딧   plan_info · plan_change_history · payment · payment_history
│                 credit_history · file_credit_history
├── 지식          post · post_category · drive · drive_path · upload_file · vector
│                 domain_info · domain_sitemap_info · domain_sitemap_link_info
├── 대화          chat_history · chat_title · ask_top · prompt_history
├── AI 메일       cx_email · cx_email_history · cx_email_prompt · cx_email_references
│                 cx_email_temp · email_cid_images · email_send_history
│                 mail_prompt_history · mail_receive_setting · mail_smtp_setting
└── 기타          inquire_history (레거시, 마이그레이션 호환용)
```

**핵심 테이블**

| 테이블 | 역할 | 설계 포인트 |
|---|---|---|
| `company_info` | 테넌트 | `vector_db_index/namespace`로 검색 격리, `mcp_server/mcp_token/mcp_allowed_tools`, `credit_available`, `parser_credit_available`, `email_available`, `store_name`(FileSearch), `on_llm_platform_system` 등 기능 플래그를 회사 단위로 보관 |
| `chat_history` | 대화 이력 | `session_key`로 세션, `role`로 질문/답변 구분, `refer_id/parser_id/email_id/sitemap_id`로 근거 출처 역참조, `is_mcp/mcp_tools`로 도구 사용 기록, `model/token/elapsed_info`로 비용·지연, `rating/memo/assessor_id`로 품질 평가 |
| `drive` / `drive_path` | 파일 저장소 | 폴더 트리, 파싱 `status`, `error_page`, 삭제 예약 `will_be_deleted_date` |
| `vector` | 청크 매핑 | 벡터 DB 청크 ID ↔ `upload_file_id/post_id/page/chunk`, `data_type`(drive/post/email) |
| `post` | 게시글 | 마크다운/HTML, 임시저장(`is_temp`), 노출 플래그, 사용 횟수(`use_count`), 크롤러 연결(`sitemap_id`) |
| `cx_email` | 고객 메일 | `message_id/references`로 스레드 연결, `status/issue_status/manager`로 CX 워크플로, 첨부·CID 이미지는 오브젝트 스토리지 키 |
| `mail_receive_setting` | 수집 설정 | IMAP(`imap_uidvalidity/imap_last_uid`) 또는 SES(`ses_last_modified`) 커서, 시크릿은 `*_enc` |
| `plan_info` / `credit_history` | 과금 | 플랜별 모델·최대 토큰·초기 크레딧, 답변·파일 단위 차감 이력 |
| `prompt_history` | 프롬프트 버전 | 회사별 시스템 프롬프트·인사말 버전 관리 |

**관계도**

```
company_info ─┬─ user_info ─── login_history / invite_history
              ├─ plan_info ─── credit_history / file_credit_history
              ├─ drive ─── upload_file ─── vector ──▶ Milvus / Pinecone (chunk id)
              ├─ post ─── post_category        │
              │     └──────────────────────────┘
              ├─ cx_email ─── cx_email_history / cx_email_references / email_cid_images
              │     └── mail_receive_setting · mail_smtp_setting
              └─ chat_history ─── chat_title · ask_top
                     │  refer_id / parser_id / email_id / sitemap_id  (답변 근거 역참조)
                     └─ prompt_history
```

### 벡터 컬렉션 (Milvus)

| 필드 | 타입 | 비고 |
|---|---|---|
| `id` | 청크 ID | MySQL `vector`와 공유 |
| `text` | VARCHAR | BM25 Function 입력 |
| `vector` | FLOAT_VECTOR(`VECTOR_DIMENSION`, 기본 1024) | dense |
| `sparse` | SPARSE_FLOAT_VECTOR | BM25로 서버 측 자동 생성, `SPARSE_INVERTED_INDEX` |
| metadata | company_key, data_type, 원본 ID, page | `SearchScope` 필터 |

Pinecone(SaaS)은 회사별 인덱스 + 네임스페이스로 같은 메타데이터를 담습니다.

### Redis / RabbitMQ / 오브젝트 스토리지

| 저장소 | 용도 |
|---|---|
| Redis | 세션별 멀티턴 대화 컨텍스트(리스트), 공개 챗봇 세션 키(TTL 30분), IP 지리정보 캐시 |
| RabbitMQ | 문서 파서 작업 큐(콜백 URL 포함), LLM 큐 작업(`/chat_on_queue`) |
| S3 / MinIO | 업로드 원본·파싱 결과(페이지 단위), 메일 본문 HTML·첨부·CID 이미지, 게시글 이미지 (presigned URL) |

## 프론트엔드 (동료 구현)

Vue 3 + Vite 프론트는 동료가 구현했습니다. 리팩터링 단계에서 제가 기여한 부분: 브랜딩 제거(`AppLogo.vue`), JWT 저장소 localStorage 전환과 401 refresh 인터셉터, 루트 경로의 로그인 직행, 스트리밍 `fetch` 경로의 토큰 재발급.

## 프로젝트 구조

```
llm-platform/
├── api/                          # FastAPI 백엔드
│   ├── main.py                   # lifespan(AsyncExitStack) · 라우터 등록 · CORS
│   ├── api/                      # 13개 라우터 (user, admin, company, plan, prompt, monitoring,
│   │                             #   drive, reference, playground, chatbot, email, emailrag, geo)
│   ├── auth/                     # JWT 발급/검증 (access 1일, refresh 3일), Depends 체인
│   ├── client/                   # mysql · redis · milvus · pinecone · aws(S3/SES) · rabbit · smtp · groxy · slack · ipapi
│   ├── module/
│   │   ├── LLM/                  # RunLLM: 프롬프트 + RAG + 대화이력 + 스트리밍 + 과금 콜백
│   │   ├── MCP/                  # RunMCP: 도구 호출 루프
│   │   ├── Mail/                 # RunLLMEmail: 답장 초안
│   │   ├── MailReceiver/         # IMAP/SES 수집 루프
│   │   ├── Retrieval/            # dense+lexical 병렬 검색, RRF, reindex
│   │   ├── Parser/               # 파서 큐 발행 · 콜백 처리 · 청킹 · 임베딩
│   │   └── Language/             # fastText 언어 감지
│   ├── helper/ · queries/ · models/ · payload/ · domain/   # 비즈니스 로직 · SQL · ORM · 요청/도메인 스키마
│   ├── migrations/               # Alembic 0001~0004
│   ├── tests/                    # 13개 테스트 (lifespan, retrieval, milvus, mail, proxy …)
│   └── scripts/reindex.py
├── llm-proxy/                    # 멀티 벤더 LLM 프록시
│   ├── api/llm.py · api/file.py  # /chat /chat_mcp /embeddings /chat_on_queue · FileSearch 스토어
│   ├── client/                   # open_ai · azure · anthropic · bedrock · google · x · local · vLLM · fastmcp
│   └── helper/llm.py             # set_client · safe_stream/chat/embeddings/function_call · 토큰 가드
├── mcp-agent/                    # FastMCP 서버 (32 tools)
├── web-refac/                    # Vue 3 + Vite 프론트
├── database/ redis/ message-queue/ vector/ s3/ nginx/   # 서비스별 Dockerfile·설정
├── monitoring/                   # prometheus · grafana provisioning · cadvisor · name-exporter
├── logs/ clickhouse/             # 로그 수집기 · 분석 저장소
├── env/                          # 서비스별 compose env 조각. 비밀번호·키·외부 주소는 env/secret.yaml(미추적)로 분리
├── compose.test.yaml · scripts/validate.sh   # 격리 통합 검증
└── docker-compose.yml            # 18 services, ai-network-refac
```

## 기술적 의사결정 요약

| 결정 | 이유 |
|---|---|
| LLM Proxy를 별도 프로세스로 | 벤더 SDK·키·폴백·스트리밍 스키마를 한 곳에서 통제, 서비스는 `vendor/model` 문자열만 다룸 |
| 폴백 트리거를 `FirstTryError` 하나로 | 토큰 초과처럼 재시도가 무의미한 실패까지 폴백하면 비용만 두 배 |
| 컨텍스트 초과를 호출 전에 차단 | 벤더 과금 없이 사용자 안내, 2차 벤더로 넘어가도 같은 실패 |
| 스트림 중 에러는 `is_error` 청크 | 헤더 전송 후 상태코드를 바꿀 수 없음, 사용자에게 빈 화면 대신 안내 |
| 벡터 클라이언트 메서드 계약 고정 | Pinecone → Milvus 교체 시 호출부 변경 0 |
| Milvus BM25 Function + RRF | 서버 측 sparse 생성으로 애플리케이션 부담 없이 하이브리드, 점수 대신 순위 융합 |
| 파서를 RabbitMQ + 콜백으로 분리 | 긴 파싱을 요청 수명에서 떼고 파서 장애를 격리, 부분 실패·재시도 추적 |
| 청크 ID를 벡터 DB와 MySQL이 공유 | 검색 결과 → 원본 페이지 역참조, 삭제·재색인 정합성 |
| 근거 4종을 하나의 retrieval 묶음으로 | 게시글·파일·메일·사이트맵을 같은 프롬프트 슬롯으로, 출처별 조회기만 추가하면 확장 |
| 크레딧 차감을 조건부 UPDATE로 | 동시 요청에서 음수 크레딧 방지, 이력 테이블로 감사 |
| MCP 설정을 회사 테이블에 | 고객사별 허용 도구를 배포 없이 관리 화면에서 제어 |
| 메일 수집기를 API 프로세스 내 루프로 | 설치형에 컨테이너를 더 늘리지 않고 설정·커서를 DB 한 곳에서 관리 |
| `SERVER_STAGE` 분기로 인프라 조합 교체 | SaaS/설치형을 같은 코드베이스로 유지 |
| Alembic + 해시 고정 lock + 격리 통합 테스트 | 설치본 업그레이드 재현성과 드리프트 회귀 방지 |
| 모니터링 스택 번들 | 폐쇄망에서도 Grafana·로그로 장애를 추적 |

## 배운 점

- **LLM 서비스의 안정성은 모델이 아니라 경계에서 결정된다**: 벤더 장애, 컨텍스트 초과, 첫 토큰 지연, 스트림 중단은 모두 모델 밖에서 일어납니다. 프록시에 폴백·타임아웃·사전 차단·에러 청크를 모아 두니 서비스 코드는 "질문을 넘기고 청크를 받는" 일만 남았습니다.
- **추상화는 인터페이스를 먼저 고정할 때만 값을 한다**: 벡터 클라이언트와 LLM 클라이언트의 메서드 계약을 먼저 정하고 구현을 갈아 끼웠기 때문에 Pinecone → Milvus, OpenAI → vLLM 전환이 호출부 수정 없이 끝났습니다. 반대로 계약 없이 시작한 메일 수집은 설치형에서 통째로 다시 만들어야 했습니다.
- **비동기는 "병렬로 부르는 것"보다 "안전하게 끝내는 것"이 어렵다**: `asyncio.gather`로 지연을 줄이는 건 금방이지만, 커넥션 싱글턴·세마포어·`AsyncExitStack` 역순 정리·`finally`의 None 가드가 없으면 부하 때 조용히 무너집니다. 규칙을 문서화하고 모든 클라이언트에 같은 패턴을 강제했습니다.
- **검색 품질은 인덱스 설계에서 결정된다**: dense만으로는 정확 일치 질의를 놓치고, 두 점수를 섞는 순간 튜닝 지옥이 됩니다. 순위 융합(RRF)이 단순하면서 안정적이었습니다. 청크 크기·겹침·메타데이터 설계가 프롬프트 튜닝보다 답변 품질에 더 크게 작용했습니다.
- **긴 작업은 요청 밖으로**: 파싱·임베딩·메일 수집·대량 생성처럼 수십 초 넘는 작업은 큐와 콜백, 백그라운드 루프로 빼고 상태를 DB에 남겨야 재시도·부분 실패·과금을 설명할 수 있습니다.
- **멀티테넌트는 모든 테이블의 첫 컬럼이다**: `company_key`를 처음부터 모든 테이블·인덱스·설정에 넣어 두니 플랜·크레딧·MCP·프롬프트·메일 설정을 회사 단위로 켜고 끄는 일이 쿼리 조건 하나로 끝났습니다.
- **스키마 드리프트는 가장 늦게 발견되는 장애**: `create_all`은 새 설치에서만 동작합니다. 마이그레이션 도구와 로그인까지 찍는 통합 테스트가 없으면 업그레이드 때 반드시 터집니다.
- **인증 버그의 절반은 토큰이 아니라 저장소 문제**: 로그로 "토큰 없음"과 "토큰 만료"를 구분하고 나서야 쿠키 공유 문제를 찾았습니다. 재발급 경로를 실제로 쓰도록 만드는 것까지가 인증 구현입니다.
- **운영 도구도 제품의 일부**: 폐쇄망 고객은 Grafana·로그·큐 UI가 없으면 장애를 설명할 방법이 없습니다. 번들에 포함하는 비용이 지원 비용보다 쌉니다.
