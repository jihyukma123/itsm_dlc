# ITSM Assistant

사내 IT 서비스 관리(ITSM) 시스템을 쓰는 동료들을 돕는 대화형 도우미입니다.
OpenAI Agents SDK(`Agent` + `Runner`)로 실제 모델과 대화하며, 기존 ITSM 시스템에 **연동 클라이언트(`client_id=itsm-agent`)로 붙는 별도 서비스**입니다.

- 현재 상태: 사용자 전환·세션, ITSM 위임 토큰 발급·갱신, 채팅 API·화면, 대화 이력까지 동작합니다.
- **Agent 에는 아직 도구가 없습니다** (`app/agent/assistant.py` 의 `TOOLS = []`). 그래서 지금은 ITSM 데이터를 조회하거나 바꿀 수 없습니다.
- ITSM 시스템의 소스 코드는 이 프로젝트에 없습니다. ITSM 에 대해 알 수 있는 것은 ITSM 팀이 전달한 **`docs/itsm/` 의 연동 문서**와 실행 중인 ITSM API 뿐입니다.

> ⚠️ ITSM 개발 환경의 티켓은 모두 실험용 모의 데이터입니다.

---

## 1. 구조

```
브라우저 ──(쿠키: itsm_agent_session)──▶ ITSM Assistant (이 프로젝트, :8100)
                                          ├─ app/session.py      사용자 전환 · 서버 측 세션 · ITSM 위임 토큰 보관/갱신
                                          ├─ app/itsm_auth.py    ITSM 인증·디렉터리용 최소 HTTP 클라이언트
                                          ├─ app/agent/
                                          │    ├─ routes.py      /api/agent/* (세션 필수)
                                          │    ├─ service.py     Runner.run 실행, SDK SQLiteSession 대화 이력, 오류 → 원인 안내
                                          │    ├─ assistant.py   Agent 정의, 지침, TOOLS = [] (도구 추가 위치)
                                          │    └─ context.py     AgentUserContext (실행 context)
                                          ├─ app/db.py           data/agent.db (sessions)
                                          └─ app/config.py       설정, .env.local 에서 OPENAI_API_KEY · ITSM 접속 정보 로드
                                                 │ HTTP  Authorization: Bearer <위임 토큰>
                                                 ▼
                                        기존 ITSM 시스템의 ITSM API (기본 http://127.0.0.1:8001)
```

### 요청 흐름

1. 화면에서 테스트 사용자를 고르면 `POST /api/session {user_id}` → ITSM 디렉터리에서 사용자를 확인하고,
   ITSM `POST /api/v2/auth/token`(grant_type=`token_exchange`, subject=username)으로 그 사용자의 **위임 토큰**을 받아
   `GET /api/v2/me` 의 역할·권한과 함께 `sessions` 테이블에 저장합니다. 쿠키에는 세션 ID만 들어갑니다.
2. `app/session.py` 의 `itsm_token_for(request, user)` 가 현재 사용자의 유효한 위임 토큰을 돌려줍니다(만료 60초 전이면 다시 교환해 세션에 저장).
3. `POST /api/agent/chat` → 세션 확인 → `AgentUserContext`(user_id, username, display_name, role, permissions) 생성
   → `Runner.run(agent, message, context=..., session=SQLiteSession(conversation_id))`.
4. 사용자를 전환하면(같은 사용자를 다시 선택해도) 새 세션과 새 대화가 시작되고 이전 대화 이력은 지워집니다.

### 주요 선택과 근거

| 선택 | 근거 |
|---|---|
| ITSM 과는 HTTP API 로만 연동, 자기 `client_id` 사용 | 기존 시스템에 나중에 붙는 연동 서비스. ITSM 내부 구현에 의존하지 않음 |
| 위임 토큰을 서버 측 세션에 보관 | ITSM 이 대화 중인 사용자의 권한·가시성으로 판단하게 함. 토큰은 브라우저·모델 입력에 노출하지 않음 |
| 모델을 `OpenAIResponsesModel(model="gpt-6-luna", openai_client=AsyncOpenAI(api_key=...))`로 명시 생성 | 키를 `.env.local` 에서만 읽고 `os.environ` 에 쓰지 않음. 대체 모델 로직 없음 |
| 대화 이력에 SDK `SQLiteSession` 사용 | 자체 이력 관리·Agent loop 를 만들지 않고 SDK 기능을 그대로 사용 |
| SDK 트레이싱 비활성(`RunConfig(tracing_disabled=True)`) | 대화 데이터를 외부 트레이싱으로 보내지 않음. 필요하면 `app/agent/service.py` 에서 켤 수 있음 |
| `create_app()` 팩토리 + `uvicorn --factory` | 테스트에서 DB 경로·모델·ITSM 클라이언트를 주입하기 쉬움 |

---

## 2. 설치·실행

요구 사항: Python 3.13 (`.python-version`), [uv](https://docs.astral.sh/uv/) 권장. **ITSM API 가 실행 중이어야** 사용자 목록·세션이 동작합니다.

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r requirements.txt

cp .env.local.example .env.local      # OPENAI_API_KEY 입력 (이미 있으면 덮어쓰지 마세요)

.venv/bin/uvicorn app.main:create_app --factory --port 8100
# → http://127.0.0.1:8100
```

| 환경 변수 / `.env.local` | 기본값 | 설명 |
|---|---|---|
| `OPENAI_API_KEY` (`.env.local` 에만) | – | 없으면 채팅이 503 `agent_not_configured`. 서버 시작 시 한 번 읽음 |
| `ITSM_BASE_URL` | `http://127.0.0.1:8001` | ITSM API 주소 |
| `ITSM_CLIENT_ID` / `ITSM_CLIENT_SECRET` | `itsm-agent` / `itsm-agent-dev-secret` | ITSM 연동 클라이언트 자격증명 (ITSM 개발 환경 값) |
| `ITSM_TIMEOUT_SECONDS` | `10` | ITSM API 호출 시간 제한 |
| `AGENT_DATA_DIR` | `./data` | `agent.db`, `agent_history.db` 위치 |

- 키·secret 은 `os.environ`, 로그, API 응답, Agent 실행 context, 대화 이력에 넣지 않습니다. OpenAI 오류 메시지에 키 일부가 섞이면 `sk-***` 로 가립니다.
- 모델 `gpt-6-luna`, reasoning effort `high` 는 고정입니다(`app/config.py`). 사용할 수 없으면 **다른 모델로 대체하지 않고** 원인을 응답합니다.
- 세션·대화 초기화: `.venv/bin/python scripts/reset_db.py` (ITSM 데이터는 건드리지 않음)

---

## 3. ITSM 연동 문서 (`docs/itsm/`)

| 파일 | 내용 |
|---|---|
| `integration-guide.md` | 연동 방식(클라이언트·토큰), 테스트 사용자·역할·권한, 가시성 규칙, v2 API 규칙, 오류 형식과 코드, 상태 전이, 우선순위·SLA, 문제·내보내기, 레거시 v1, 이 서비스에 발급된 개발 환경 자격증명 |
| `openapi.json` | ITSM API 전체 요청·응답 스키마 (OpenAPI 3) |

ITSM 운영팀이 전달한 문서이며 이 프로젝트에서 수정하지 않습니다.

---

## 4. API

| 메서드·경로 | 세션 | 설명 |
|---|:-:|---|
| `GET /api/health` | | `{status, itsm: {base_url, reachable, version}, agent: {configured, model, reasoning_effort}}` |
| `GET /api/users` | | 전환할 수 있는 테스트 사용자(ITSM 디렉터리의 활성 사용자) |
| `POST /api/session` | | `{user_id}` → 사용자 전환. 없는 사용자 404 `user_not_found`, 비활성 409 `user_inactive` |
| `GET /api/session`, `DELETE /api/session` | ✔ / | 현재 사용자(`permissions` 포함) / 세션 종료(항상 204) |
| `POST /api/agent/chat` | ✔ | `{message}`(1–4000자) → `{reply, context: {user_id, username, role}}` |
| `GET /api/agent/messages`, `DELETE /api/agent/messages` | ✔ | 현재 대화 이력 / 초기화 |

| HTTP | code | 의미 |
|---|---|---|
| 401 | `no_session` | 세션 없음 (키 설정 여부보다 먼저 검사) |
| 503 | `itsm_unavailable` | ITSM API 연결 실패 |
| 502 | `itsm_auth_failed` | ITSM 이 이 서비스의 자격증명을 거부 |
| 503 | `agent_not_configured` | `.env.local` 에 `OPENAI_API_KEY` 없음 |
| 502 | `model_unavailable` / `model_access_denied` / `model_request_rejected` / `agent_auth_failed` / `model_api_error` | OpenAI API 오류 (404 / 403 / 400 / 401 / 기타) |
| 503 | `model_rate_limited` | OpenAI 사용 한도 초과 |
| 504 | `model_connection_failed` | OpenAI 연결 실패·시간 초과 |
| 500 | `agent_run_failed` | SDK 실행 오류 |

502 계열 모델 오류 메시지에는 "다른 모델로 대체하지 않았습니다"가 포함됩니다.

---

## 5. 테스트

```bash
.venv/bin/python -m pytest -q
```

ITSM 이나 OpenAI 를 호출하지 않습니다. ITSM 은 인증·디렉터리 엔드포인트만 흉내 내는 `tests/conftest.py` 의 `FakeItsm`(`httpx.MockTransport`)으로,
모델은 호출 인자를 기록하는 `FakeModel` 로 바꾸고 SDK 의 `Agent`/`Runner`/`SQLiteSession` 은 그대로 씁니다.

| 파일 | 확인 내용 |
|---|---|
| `tests/test_session.py` | ITSM 디렉터리 사용자 목록, 사용자 전환·세션, 위임 토큰 서버 보관·갱신, 세션 필수, 위조 쿠키, ITSM 연결 실패·자격증명 거부, 화면 |
| `tests/test_agent.py` | 키 없음 안내, 모델·reasoning 구성, 백엔드 확인 context 전달, 메시지로 신원 변경 불가, 도구 없음, 대화 이력, 모델 오류 비대체, 키 비노출 |

실제 모델 연결 확인(비용 발생): ITSM API 와 이 서버를 띄운 뒤 `.venv/bin/python scripts/agent_smoke.py`.

---

## 6. 도구를 추가할 위치

| 위치 | 할 일 |
|---|---|
| `app/agent/assistant.py` 의 `TOOLS` | `@function_tool` 로 만든 도구를 등록 (현재 빈 목록) |
| `app/agent/assistant.py` 의 `INSTRUCTIONS` | 필요하면 도구 사용 지침 추가 (현재는 페르소나 한 줄만 있음) |
| `app/agent/tools.py` (새 파일 권장) | 도구 구현. `RunContextWrapper[AgentUserContext]` 의 `ctx.context` 로 실행 주체 확인 |
| `app/itsm_auth.py` 또는 새 ITSM 클라이언트 모듈 | ITSM 업무 API 호출. 현재는 인증·디렉터리 호출만 있음 |
| `app/session.py` 의 `itsm_token_for` | 현재 사용자의 유효한 ITSM 위임 토큰을 얻는 방법. 도구가 토큰·클라이언트를 얻는 방법은 구현하면서 결정 (현재 context 에는 사용자 정보만 있음) |
| `app/agent/service.py` | `Runner.run` 호출 위치 (실행 설정, 오류 처리) |
| `tests/test_agent.py` | `test_agent_has_no_tools` 는 도구 추가 시 기대값을 바꿔야 함 |
