> **llm-platform**: `llm-platform-install`의 리팩터링 사본입니다. 기존 설치본과 동시에 띄울 수 있도록 컨테이너명(`-refac`), 이미지명(`llm-platform-*`), 네트워크(`ai-network-refac`), 호스트 포트가 분리돼 있습니다.
>
> | 서비스 | 설치본 포트 | refac 포트 |
> |---|---|---|
> | 웹/API (nginx) | 4321 | **4331** |
> | MySQL | 3306 | 3316 |
> | LLM 프록시 | 9999 | 9989 |
> | ClickHouse HTTP | 8123 | 8133 |
>
> 프론트(`web-refac/`)는 브랜딩을 제거했고 제품명·지원 연락처를 `web-refac/.env`의 `VITE_APP_NAME`, `VITE_SUPPORT_EMAIL`로 받습니다(비우면 화면 이름만 표시). 랜딩·요금·약관 페이지는 삭제됐고 `/`는 바로 로그인 화면(`/signin`)으로 갑니다. 로그인된 상태면 같은 화면에서 시작 버튼으로 대시보드에 들어갑니다. 파일 저장소는 폴더 트리 + 드래그앤드롭 탐색기로 교체됐습니다.
>
> 두 스택을 동시에 띄우면 Milvus 두 개가 Docker VM 메모리(약 10GB)를 넘겨 죽을 수 있습니다. 한 번에 한 스택만 띄우는 것을 권장합니다.

# LLM Platform - AI 기반 지식 관리 플랫폼

LLM Platform은 채팅 인터페이스, 문서 처리, 벡터 검색 기능을 결합한 종합적인 AI 기반 지식 관리 플랫폼으로 지능형 정보 검색 및 관리 서비스를 제공합니다.

Python 서비스는 3.14와 해시가 포함된 `requirements.lock`으로 빌드합니다.
`sh scripts/validate.sh`로 격리된 환경에서 전체 빌드·부팅·검색·이관·로그인 검증을
실행할 수 있습니다. 설치와 기존 Milvus 데이터 이관 절차는 [API README](api/README.md)를 참고하세요.

## 🏗️ 아키텍처 개요

LLM Platform은 Docker Compose를 사용한 마이크로서비스 아키텍처로 구성되어 있습니다:

- **웹 프론트엔드** - Vue 3 기반 모던 UI
- **API 백엔드** - FastAPI 기반 Python 서비스
- **벡터 데이터베이스** - Milvus 시맨틱 검색
- **관계형 데이터베이스** - MySQL 구조화된 데이터
- **캐시 레이어** - Redis 세션 관리
- **객체 저장소** - MinIO 파일 저장
- **LLM 프록시** - 멀티 프로바이더 LLM 서비스
- **MCP 에이전트** - Model Context Protocol 에이전트 서버
- **리버스 프록시** - Nginx 로드 밸런싱

## 🚀 빠른 시작

### 사전 요구사항

- Docker 및 Docker Compose
- 최소 8GB RAM 권장
- 20GB 이상 여유 디스크 공간

### 설치 방법

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd llm-platform
   ```

2. **Docker 네트워크 생성**
   ```bash
   docker network create ai-network-refac
   ```

3. **환경 변수 설정**
   - 비밀번호·키·토큰·외부 사설 주소는 `env/secret.yaml` 한 곳에 둡니다. `cp env/secret.example.yaml env/secret.yaml` 후 값을 채우세요.
     각 `env/*.yaml`의 `config_node`가 `secret.yaml`의 같은 이름 서비스를 `extends`하므로, 파일이 없으면 `docker compose`가 즉시 실패합니다.
   - `env/secret.yaml`은 커밋하지 않습니다(`.gitignore`). 파일 안 주석대로 같은 값이어야 하는 키(`DB_PASSWORD`=`MYSQL_ROOT_PASSWORD`, `MESSAGE_QUEUE_PASS`=`RABBITMQ_DEFAULT_PASS`, `S3_SECRET_KEY`=`MINIO_ROOT_PASSWORD`, `CLICKHOUSE_PASSWORD` 2곳)를 맞추고, `DB_URI`의 비밀번호는 URL 인코딩(`#`→`%23`, `@`→`%40`, `!`→`%21`)합니다.
   - 설정값(호스트·포트·모델명 등)은 `env/*.yaml`에서 조정합니다. 루트 `.env`는 더 이상 쓰지 않습니다.
   - MCP 서버 bearer 토큰은 `MCP_ADMIN_TOKEN`(읽기·쓰기·관리)과 `MCP_READ_TOKENS`(`토큰:client_id`를 콤마로 나열, 읽기 전용)로 줍니다. 관리 화면에서 회사에 등록하는 MCP 토큰은 이 중 하나여야 합니다. 둘 다 비어 있으면 MCP 컨테이너가 기동을 거부합니다.
   - 프론트 빌드 값은 `cp web-refac/.env.example web-refac/.env` 후 채웁니다. `VITE_*`는 빌드 시 번들에 박히므로 바꾸면 `docker compose build web`을 다시 합니다.
   - 언어 감지 모델(fastText `lid.176.bin`, 약 125MB)은 용량 때문에 저장소에 없습니다. API 빌드 전에 내려받아 두세요.
     ```bash
     curl -L https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin \
       -o api/module/Language/lang_detect_model.bin
     ```
     없으면 API는 뜨지만 언어 감지가 실패해 모든 질문을 한국어로 간주합니다.
   - master 계정은 API 첫 부팅 시 `ADMIN_USER_ID` / `ADMIN_USER_PASSWORD` / `ADMIN_EMAIL_ADDRESS`(`env/api.yaml`)로 생성됩니다.
     **미설정 시 코드 기본값(`admin` / `admin123!@#`)이 쓰이므로 설치 시 반드시 바꾸세요.** 이미 생성된 계정은 env를 바꿔도 갱신되지 않습니다.
   - AI 메일(aimail) 메뉴는 `ADMIN_EMAIL_AVAILABLE=true`(기본)일 때 master 회사에 켜지고, 발신 주소는 `ADMIN_EMAIL_ADDRESS`를 씁니다. 부팅 때마다 적용되므로 끄려면 `false`로 바꾸고 재기동하세요.

4. **서비스 시작**
   ```bash
   docker-compose up -d
   ```

5. **애플리케이션 접속**
   - 웹 UI: http://localhost:4331
   - API 문서: http://localhost:4331/llm-platform-api/docs
   - 벡터 DB 관리자 (Attu): http://localhost:4331/vector/
   - RabbitMQ 관리: http://localhost:4331/mq/
   - Grafana: http://localhost:4331/monitoring
   - MinIO 콘솔: 호스트에 노출하지 않습니다. 필요하면 `docker-compose.yml`의 `s3.ports` 주석을 해제하세요.

## 📋 서비스 구성

### 핵심 서비스

| 서비스 | 설명 | 포트 | 기술 스택 |
|---------|-------------|------|------------|
| **web** | Vue 3 프론트엔드 애플리케이션 | 4331 (nginx 경유, `/`) | Vue 3, Vite |
| **api** | 메인 FastAPI 백엔드 | 4331 (nginx 경유, `/llm-platform-api/`) | Python, FastAPI |
| **nginx** | 리버스 프록시 & 로드 밸런서 | 4331 (컨테이너 4321) | Nginx |

### 데이터 레이어

| 서비스 | 설명 | 포트 | 기술 스택 |
|---------|-------------|------|------------|
| **database** | MySQL 데이터베이스 | 3316 (컨테이너 3306) | MySQL 8.0 |
| **redis** | 캐시 및 세션 저장소 | 6379 (내부 전용) | Redis |
| **vector** | AI 임베딩용 벡터 데이터베이스 | 19530 (내부 전용) | Milvus |
| **etcd** | Milvus용 코디네이션 서비스 | 2379 (내부 전용) | etcd |
| **s3** (MinIO) | 파일용 객체 저장소 | 9000 (내부 전용) | MinIO |

### AI/ML 서비스

| 서비스 | 설명 | 포트 | 기술 스택 |
|---------|-------------|------|------------|
| **llm-proxy** | LLM 프록시 서비스 | 9989 (컨테이너 9999) | Python, FastAPI |
| **mcp** | Model Context Protocol 에이전트 | 8002 (내부 전용) | Python |
| **attu** | Milvus 관리 인터페이스 | 4331 (nginx 경유, `/vector/`) | Attu |

## 🛠️ 개발 환경

### 프론트엔드 개발

```bash
cd web-refac
pnpm install
pnpm run dev
```

### 백엔드 개발

```bash
cd api
pip install -r requirements.txt
python main.py
```

### 환경 설정

다음 환경 파일들을 설정하세요:

- `env/api.yaml` - API 서비스 설정
- `env/database.yaml` - 데이터베이스 설정
- `env/vector.yaml` - 벡터 데이터베이스 설정
- `env/proxy.yaml` - LLM 프록시 설정
- `env/mcp-agent.yaml` - MCP 에이전트 설정

## 📬 메일 수신 설정 (IMAP / SES)

AI 메일 받은편지함은 **master 계정**이 `관리자 > 메일 수신 설정`(`/tool/admin/mail-receive`)에서 등록한 경로로 채워집니다.

- **IMAP**: 메일 서버 호스트·포트·SSL·계정·비밀번호·폴더를 등록합니다. API가 `MAIL_RECEIVER_ENABLED=true`일 때 백그라운드로 주기 폴링하며 `UID` 체크포인트로 새 메일만 가져옵니다.
- **SES**: SES 수신 규칙(S3 action)이 원문을 저장하는 버킷·프리픽스·리전·액세스 키를 등록합니다. 객체의 `LastModified`를 체크포인트로 폴링합니다. 키를 비우면 인스턴스 권한을 씁니다.
- 비밀번호와 시크릿 키는 `SECRET_KEY`로 암호화해 저장하며 API 응답에 포함되지 않습니다. `SECRET_KEY`를 바꾸면 저장된 자격증명을 다시 입력해야 합니다.
- 수신 메일은 본문 HTML과 첨부를 `cx-email-html` 버킷에 올리고 `cx_email`에 `parsed` 상태로 적재합니다. 같은 `Message-ID`는 중복 적재하지 않습니다.
- "연결 테스트"로 저장 전 접속을 확인하고, "지금 수집"으로 즉시 한 번 가져올 수 있습니다. 실패 원인은 화면의 "마지막 오류"에 남습니다.
- **SMTP 발신**: 같은 화면의 "SMTP 발신 서버" 카드에 호스트·포트·STARTTLS/SSL·계정·비밀번호·발신 주소를 등록하면 답장 발송이 SES 대신 이 서버로 나갑니다. 발신 `Message-ID`를 직접 만들어 스레드(`References`)를 이어 줍니다. 설정이 없으면 기존 SES 경로를 씁니다(`env`의 `SMTP_*`는 더 이상 발송에 쓰이지 않음).

## 🗃️ 데이터베이스 스키마

스키마는 `api/migrations/`의 alembic 리비전으로 관리하며 API가 부팅할 때 `upgrade head`를 자동 실행합니다.
베이스라인(`0001`)은 신규 설치에서는 전체 테이블을 만들고, 기존 설치에서는 빠진 테이블·컬럼만 추가합니다.
모델을 바꿨다면 `create_all`에 기대지 말고 새 리비전을 만드세요 (절차는 [API README](api/README.md#db-스키마-마이그레이션)).

시스템은 다음 테이블들과 함께 MySQL을 사용합니다:

- `user_info`, `user_auth` - 사용자 관리
- `chat_history`, `chat_title` - 채팅 대화
- `company_info`, `domain_info` - 조직 데이터
- `drive`, `upload_file` - 파일 관리
- `vector` - 벡터 임베딩 메타데이터
- `plan_info`, `payment` - 구독 관리

## 🔧 설정

### 필수 API 키

- OpenAI API 키 (GPT 모델용)
- Anthropic API 키 (Claude 모델용)
- AWS 자격 증명 (Bedrock, SES용)
- Pinecone API 키 (대체 벡터 DB)

### MinIO 설정

MinIO는 두 가지 목적으로 사용됩니다:
- **Milvus 저장 백엔드** - 벡터 데이터 저장
- **애플리케이션 파일 저장소** - 사용자 업로드 파일

MinIO 포트는 호스트에 노출하지 않습니다. 콘솔이 필요하면 `docker-compose.yml`의 `s3.ports` 주석을 해제한 뒤 접속하세요.

## 🚨 헬스 체크

모든 서비스에는 헬스 체크가 포함되어 있습니다:

```bash
# 모든 서비스 상태 확인
docker-compose ps

# 서비스 로그 보기
docker-compose logs [service-name]

# 헬스 체크 엔드포인트
curl http://localhost:4331/llm-platform-api/check
docker compose exec s3 curl -f http://localhost:9000/minio/health/live
```

## 📊 모니터링

- **애플리케이션 로그** - `docker-compose logs`로 확인 가능
- **데이터베이스 모니터링** - MySQL performance schema 활성화
- **벡터 DB 모니터링** - Attu 인터페이스에서 메트릭 제공
- **시스템 모니터링** - Docker stats를 통한 리소스 사용량

## 🔒 보안

- JWT 기반 인증
- 웹 요청을 위한 CORS 설정
- 시크릿을 위한 환경 변수 관리
- Docker 네트워크를 통한 네트워크 격리
- 서비스 가용성을 위한 헬스 체크 모니터링

## 🛡️ 문제 해결

### 일반적인 문제들

1. **서비스가 시작되지 않는 경우**
   - Docker 네트워크 확인: `docker network ls`
   - 포트 가용성 확인: `netstat -tulpn`
   - 디스크 공간 확인: `df -h`

2. **데이터베이스 연결 오류**
   - MySQL 서비스 실행 상태 확인
   - env 파일의 데이터베이스 인증 정보 확인
   - 데이터베이스 초기화 완료 확인

3. **벡터 검색이 작동하지 않는 경우**
   - Milvus 서비스 헬스 상태 확인
   - MinIO 연결성 확인
   - etcd 서비스 상태 확인

4. **파일 업로드 문제**
   - MinIO 서비스 상태 확인
   - 버킷 권한 확인
   - 디스크 공간 사용량 모니터링

### 서비스 의존성

```
web → api → database, redis, vector, proxy
vector → etcd, minio
attu → vector
api → mcp (선택사항)
```

## 📝 라이선스

[여기에 라이선스를 명시하세요]

## 🤝 기여하기

[여기에 기여 가이드라인을 추가하세요]

## 📞 지원

[여기에 지원 연락처 정보를 추가하세요]
