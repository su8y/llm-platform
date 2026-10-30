# 1. llm-platform api
- LLM Service API
- Chat, Chat Management, Retrieval Data Management, etc...

## Python 3.14

API·LLM 프록시·MCP·모니터링 exporter의 Docker 실행 버전을 3.14로 맞춘다.
로컬 버전은 상위 `.python-version`을 따른다. 기존 3.11/3.12 가상환경은 재사용하지
않고 각 서비스에서 `uv venv --python 3.14` 후 lock 파일을 설치한다.

Pydantic 2.12 이상을 사용하며 ConfigDict와 nullable 필드의 명시적 기본값으로
기존 모델 계약을 유지한다. fastText는 동일한 `fasttext` import를 제공하는
`fasttext-community`로 교체했다. HTTP 파서는 Uvicorn 기본 의존성인 h11을 쓴다.
사용하지 않는 transformers·httptools·fastapi-jwt-auth 의존성은 제거했다.
PyMilvus 2.6 계열과 서버 2.6.11을 맞췄다. 기존 Milvus 볼륨은 업그레이드 전에
백업하고 공식 업그레이드 절차를 적용한다. 이 변경은 실제 볼륨을 업그레이드하지 않는다.

API·프록시·MCP·exporter는 각각 해시가 포함된 `requirements.lock`을 사용한다.
Docker 빌드도 이 파일로 설치한다. MCP의 패키지 메타데이터는
`requirements.txt`를 읽어 의존성 정의가 갈라지지 않게 한다.

```sh
uv venv --python 3.14 .venv-314
uv pip sync --python .venv-314/bin/python --require-hashes requirements.lock
# requirements.txt를 변경했을 때 lock 갱신
uv pip compile requirements.txt --python-version 3.14 --universal --generate-hashes -o requirements.lock
```

2026-10-29 설치형 로컬 DB의 스키마 드리프트를 고치며 alembic 도입, 모델 자동 import,
`server_default="NULL"`(문자열) 제거, 시크릿의 루트 `.env` 분리를 적용했다.
`validate.sh`의 통합 테스트는 로그인 후 `/user/get_info`까지 확인해 드리프트 회귀를 잡는다.

2026-10-23에 Python 3.14 로컬 설치와 네 서비스 Docker 이미지 빌드·부팅을
검증했다. API는 `lifespan`에서 연결을 열고 역순으로 닫으며, 초기화 중 실패해도
이미 획득한 자원을 정리한다. 빈 MySQL의 테이블·관리자 생성, 재시작,
신규 회원가입·로그인과 실제 Milvus 2.6.11의 BM25·벡터 검색·이관도 검증했다.

새 Milvus 컬렉션의 차원은 `VECTOR_DIMENSION`을 따른다(미설정 시 1024).
설치 env의 1536 설정도 반영하며, 잘못된 값은 컬렉션 생성 전에 거부한다.
이 값은 임베딩 서버가 반환하는 벡터 차원과 같아야 한다. 기존 컬렉션의 차원은
이 설정으로 변경되지 않으므로 차원을 바꿀 때는 새 컬렉션으로 이관해야 한다.

## DB 스키마 마이그레이션

스키마는 alembic으로 관리한다(`alembic.ini`, `migrations/`). `lifespan`의 `init_db()`가
`models/` 패키지의 모든 모델을 자동 import한 뒤 `alembic upgrade head`를 실행하므로,
모델 파일을 추가할 때 `models/__init__.py`에 import를 적을 필요가 없다.

`SQLAlchemy create_all`은 없는 테이블만 만들고 기존 테이블의 컬럼은 추가하지 않는다.
설치형에서 이 차이로 모델과 DB가 어긋나 로그인까지 실패한 사례(2026-10-29)가 있어
베이스라인 리비전 `0001`은 `create_all(checkfirst)` 후 모델에만 있는 컬럼을
`ADD COLUMN`으로 보정한다. 이후의 스키마 변경은 새 리비전으로만 반영한다.

```sh
cd api
# 모델 변경 후 리비전 생성 (DB_URI 는 비교 대상 DB)
DB_URI='mysql+aiomysql://root:change-me@localhost:3306/llm_platform' \
  python3 -m alembic revision --autogenerate -m "add xxx column"
# 생성된 migrations/versions/*.py 를 검토한 뒤 적용 (API 부팅 시에도 자동 적용)
DB_URI='...' python3 -m alembic upgrade head
```

autogenerate는 컬럼 타입 변경·이름 변경을 완전히 잡지 못하므로 생성된 리비전을 반드시 읽고 고친다.
베이스라인은 되돌리지 않는다(`downgrade`는 no-op). 운영 DB에는 백업 후 적용한다.

## 하이브리드 검색

채팅과 메일 검색은 `module/Retrieval/service.py`의 `Retriever`를 사용한다.
질문 원문으로 벡터 검색과 BM25를 병렬 실행하고 RRF로 순위를 합친다.
llm-proxy가 질문·최근 대화·검색 근거를 보고 보완 검색어를 제안하면 한 번만
재검색한다. 원래 검색 결과도 최종 순위에 함께 반영한다.

- `core.py`: 검색 범위, RRF, 최대 2회 검색과 태스크 정리. 외부 패키지 없음.
- `service.py`: 임베딩·LLM 판단을 기존 llm-proxy에 요청. 벤더 SDK 없음.
- `client/milvus.py`: Milvus 2.6의 BM25 기능과 원문·벡터 upsert 사용.

모든 검색은 회사·활성 상태·지정 파일·문서 유형 조건을 적용한다.
결과에서도 같은 조건을 검사한 뒤에만 LLM에 근거를 전달한다.
게시물·발송 메일·파서 등록·파일 수정 시 임베딩한 청크를 `content` 메타데이터에
저장하며 Milvus의 `text` 필드에도 함께 반영한다. 메타데이터 변경 시 원문을
보존하고 삭제/비활성화는 벡터와 BM25에 함께 적용한다.

LLM 판단은 최대 4초, 전체 검색은 최대 20초다. 잘못된 JSON·과도한 출력·판단
시간 초과는 원래 결과를 유지한다. 실제 IO 장애는 기존 AppError로 전달한다.
LLM이 충분하다고 판단해도 근거 정확도가 보장되지는 않으며 RRF 점수도 신뢰도
확률이 아니다. 한국어 조사·활용형과 검색 품질은 별도 평가 데이터가 필요하다.

### 기존 데이터

새 컬렉션에는 `text`·`sparse` 필드와 BM25 함수를 생성한다. 기존 컬렉션은
자동 삭제하거나 변경하지 않으며 BM25 필드가 없으면 경고와 함께 벡터 검색을
유지한다. 기존 Pinecone 인덱스도 벡터 검색을 유지한다.

기존 컬렉션에 문서를 다시 넣기만 해서는 BM25 함수가 생기지 않는다.
이관하려면 새 네임스페이스의 컬렉션을 만들고, 원본 문서·메일·파서 결과를
재처리해 청크와 벡터를 채운 뒤 회사의 검색/등록 네임스페이스를 함께 전환한다.
`python -m scripts.reindex --source OLD --target NEW --company COMPANY`로
원문·회사 범위를 먼저 검사한다. `--write`를 추가하면 새 컬렉션에 재임베딩하고,
청크 ID·메타데이터 해시·문서 수를 원본과 대조한다. 회사 네임스페이스는 자동
전환하지 않는다. 원본에 `company_key`가 없으면 이 도구로 이관할 수 없다.
원문이 없으면 `--texts chunks.jsonl`로 벡터 청크 ID와 원문을 제공한다:

```json
{"id":"post-123","content":"해당 청크의 원문"}
```

이관 중에는 원본 쓰기를 중단한다. 임베딩은 동시 요청 없이 순차 실행한다.
기존 대상 컬렉션에는 쓰지 않는다. 실패한 대상은 불완전할 수 있으므로 새 이름으로
재시도한다. 대상 검증 성공 후 검색·등록 네임스페이스를 함께 수동 전환한다.
공유 컬렉션에서는 회사 하나만 이관하므로 전체 컬렉션을 일괄 전환하면 안 된다.
DB·벡터·S3 간 분산 트랜잭션/장애 보상은 기존 흐름의 후속 개선 대상이다.

### 검증

`cd api && python3 -m unittest discover -s tests -v`

의존성이 설치된 Python 3.14 가상환경에서 실행한다. 실제 IO 테스트는 아래의
격리된 검증 환경에서 실행하며 로컬 실행 시에는 해당 엔드포인트가 없으면 건너뛴다.

프로젝트 루트(`llm-platform-install`)에서 전체 검증:

```sh
sh scripts/validate.sh
```

`compose.test.yaml`은 새 MySQL·Milvus·Redis·RabbitMQ와 네 Python 서비스를
별도 Compose 프로젝트로 생성한다. 기존 env 파일과 데이터 볼륨을 사용하지 않고
호스트 포트를 열지 않는다. exporter 검증에는 Docker 소켓을 읽기 전용으로 연결한다.
초기 부팅·API 재시작 후 단위/통합 테스트를 실행하고 종료 시 테스트 컨테이너와
볼륨을 제거한다. Docker와 이미지/패키지를 받을 네트워크가 필요하다.
MCP는 이 검증 환경에서만 인증 없는 debug HTTP 모드로 실행한다.

테스트용 `vendor-fixture`는 정해진 임베딩과 분할된 스트리밍 JSON을 반환한다.
실제 프록시 HTTP·Base64 벡터 변환·Milvus·Retriever를 연결해 검색과 한 차례의
보완 검색, 잘못된 판단 JSON의 처리, 회사/활성 상태/파일/문서 유형 경계와
HTTP 임베딩을 이용한 이관을 검증한다. 이 테스트는 실제 모델의 추론 품질을
평가하지 않는다.

단위 테스트는 실제 검색 모듈을 로드하고 외부 SDK/IO를 모킹한다.
실제 Milvus 계약 테스트는 의존성이 설치된 환경에서
`LLM_PLATFORM_TEST_MILVUS_URI=http://localhost:19530`을 지정해 실행한다.
계약 테스트는 임시 컬렉션만 생성·정리한다. 실제 LLM 벤더 추론·외부 파일 파서·
SMTP 전송은 이 검증에 포함하지 않는다. 실제 운영 볼륨의 Milvus 업그레이드와
회사별 네임스페이스 전환도 검증 스크립트에서 수행하지 않는다.

2026-10-27 실제 연동 확인에서는 설정된 추론 서버의 TCP 연결이 시간 초과됐고
임베딩 서버의 호스트는 DNS로 확인되지 않았다. 사내망/VPN 등 서버에 접근할 수
있는 환경에서 실제 임베딩 차원과 모델의 보완 검색 판단을 확인해야 한다.

SMTP는 현재 발송용이다. 이 저장소의 API에서는 IMAP/POP 수집기가 확인되지
않았다. 외부 수집기의 UID/UIDVALIDITY·중복·MIME·첨부 제한·저장 체크포인트를
확인한 뒤 수집 경로를 연결한다.

참고: [Milvus BM25](https://milvus.io/docs/full-text-search.md),
[RRF](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/).

# 2. infra structure
- python: 3.14
- api: fast-api
- database: mysql
- cache database: redis
- vector database: pinecone, milvus
- message queue: rabbitMQ
- cloud service: AWS
- llm: llm-proxy (multi-vendor)
- env
```
FLASK_CONFIG = #"staging" #"production", #"development"

OPENAI_API_KEY=""
# CLAUDE_API_KEY = ""
# GEMINI_API_KEY = ""

PINECONE_API_KEY=""
PINECONE_ENV=

SESSION_STORAGE_HOST=""
SESSION_STORAGE_PORT=
SESSION_STORAGE_DB_NUMBER=

DB_URI = ""
STAGING_DB_URI = ""
# for pymysql: llm module can not use flask-sqlalchemy
DB_HOST=""
DB_PORT=
DB_USERNAME=""
DB_PASSWORD=""
DB_DATABASE=""

AWS_DEFAULT_REGION=""
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_SES_ACCESS_KEY_ID=""
AWS_SES_SECRET_ACCESS_KEY=""
AWS_SES_REGION=""

SLACK_TOKEN=""
```

# 3. server, script structure
- client: infra side such as aws, vectorDB, Database, Redis, Message Protocol, etc
- models: business database ORM models.
- queries: CRUD method script through ORM.
- api: router side.
- auth: JWT middleware side
- payload: request data such as payload, quary params.
- helper: business logic side.
- domain: domain side dataclass for business logic.
- utils: common method script.
- **module: core business logic class. such as to request proxy-server for Inferencing LLM, to send Message for activating FILE-PARSER
