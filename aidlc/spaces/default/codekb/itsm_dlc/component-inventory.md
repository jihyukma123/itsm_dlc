# ITSM Assistant 컴포넌트 인벤토리

## 런타임 컴포넌트

### FastAPI 애플리케이션 팩토리

- 위치: `app/main.py`
- 책임: 설정·DB·ITSM client·AgentService 조립, lifespan, router 등록, health와 정적 파일 제공
- 의존: 설정 관리, SQLite 저장소, ITSM HTTP 클라이언트, 세션·위임 토큰 관리, Agent API 라우트
- 소비자: Uvicorn, 테스트 fixture

### 설정 관리

- 위치: `app/config.py`, `.env.local.example`
- 책임: DB/static 경로, 고정 model/reasoning, API key, ITSM 접속 설정 로드
- 의존: python-dotenv, 환경 변수
- 소비자: 앱 팩토리, Agent 실행 서비스, scripts

### SQLite 저장소

- 위치: `app/db.py`
- 책임: 서버 세션 schema, connection/context manager, 초기화와 reset
- 의존: Python sqlite3
- 소비자: 세션·위임 토큰 관리, 앱 팩토리, reset script

### ITSM HTTP 클라이언트

- 위치: `app/itsm_auth.py`
- 책임: 서비스/위임 토큰 발급, 서비스 토큰 cache·refresh, 디렉터리·현재 사용자·health 호출, transport 오류 변환
- 의존: httpx, asyncio
- 소비자: 세션·위임 토큰 관리, 앱 팩토리
- 현재 공백: 티켓 목록·상세·등록·수정과 안전한 티켓 오류 mapping

### 세션·위임 토큰 관리

- 위치: `app/session.py`
- 책임: CurrentUser 복원, 보호 API dependency, 토큰 선제 갱신, 사용자 전환/종료 HTTP API
- 의존: SQLite 저장소, ITSM HTTP 클라이언트, API 스키마, AgentService(app state)
- 소비자: Agent API 라우트, Agent 실행 context, 브라우저

### API 스키마

- 위치: `app/schemas.py`
- 책임: 사용자·세션·Agent 채팅·이력의 Pydantic 입출력과 현재 시각 helper
- 의존: Pydantic
- 소비자: 세션 라우트, Agent API 라우트, Agent 실행 서비스

### Agent 정의

- 위치: `app/agent/assistant.py`
- 책임: Agent 이름·지침·고정 reasoning 설정과 tool 목록 구성
- 의존: Agents SDK, Agent 실행 context, 설정 상수
- 소비자: Agent 실행 서비스
- 현재 공백: `TOOLS`가 빈 목록

### Agent 실행 context

- 위치: `app/agent/context.py`
- 책임: CurrentUser에서 검증된 사용자 ID·이름·role·permissions만 Runner context로 변환
- 의존: 세션·위임 토큰 관리의 CurrentUser
- 소비자: Agent 정의, Agent 실행 서비스, 향후 function tool
- 현재 공백: 갱신 가능한 서버 전용 ITSM capability 없음

### Agent 실행 서비스

- 위치: `app/agent/service.py`
- 책임: 모델 client/Agent 구성, Runner와 SQLiteSession 실행, 이력 조회·삭제, OpenAI 오류 mapping과 key redaction
- 의존: Agents SDK, OpenAI SDK, Agent 정의/context, 설정, 세션 사용자
- 소비자: Agent API 라우트, 세션 전환/종료, 앱 팩토리

### Agent API 라우트

- 위치: `app/agent/routes.py`
- 책임: 보호된 chat/messages/clear HTTP endpoint와 응답 mapping
- 의존: AgentService(app state), 세션 current-user dependency, API 스키마
- 소비자: 정적 웹 클라이언트와 API caller

### 정적 웹 클라이언트

- 위치: `static/index.html`, `static/app.js`, `static/style.css`
- 책임: 사용자 선택, 세션 상태, 채팅/이력 초기화, loading/error 표시
- 의존: FastAPI inbound API, browser DOM/fetch
- 소비자: 사용자

## 지원 컴포넌트

### 자동화 테스트 기반

- 위치: `tests/conftest.py`, `tests/test_agent.py`, `tests/test_session.py`
- 책임: FakeItsm MockTransport, FakeModel, 앱 fixture, 서버 세션·Agent·오류·비노출 회귀 검증
- 의존: pytest, httpx, FastAPI TestClient, 실제 Agents SDK Runner/SQLiteSession
- 현재 공백: Fake ITSM ticket API와 tool-call 응답 loop

### 유지보수·스모크 스크립트

- 위치: `scripts/reset_db.py`, `scripts/agent_smoke.py`
- 책임: 서버 세션/대화 DB reset, 명시적 실제 모델·ITSM 환경 스모크 확인
- 의존: app config/db 또는 httpx
- 주의: 스모크 스크립트는 실제 API 호출과 비용을 발생시키며 자동화 테스트 경로가 아니다.

### ITSM 연동 계약

- 위치: `docs/itsm/integration-guide.md`, `docs/itsm/openapi.json`
- 책임: 인증·권한·가시성·오류·티켓 semantics와 OpenAPI 3.1 요청/응답 schema 정의
- 의존: 외부 ITSM 팀이 제공하는 계약
- 소비자: ITSM client 구현, function tool schema, 계약 테스트, README

## 컴포넌트 의존 관계

| 컴포넌트 | 직접 의존 | 데이터/비밀 경계 |
|---|---|---|
| 정적 웹 클라이언트 | FastAPI inbound API | 쿠키는 session ID만, role은 응답 표시용 |
| FastAPI 애플리케이션 팩토리 | session/agent router, settings, clients | 앱 state에 Settings와 clients 보관 |
| 세션·위임 토큰 관리 | SQLite, ITSM client | 위임 token 원문은 서버 DB/메모리에만 |
| Agent API 라우트 | CurrentUser, AgentService | client body에서 사용자 권한을 받지 않음 |
| Agent 실행 서비스 | Agent/context, SDK session, OpenAI | API key는 모델 client 생성에만 사용 |
| Agent 실행 context | CurrentUser | 현재는 token/key/secret 필드 없음 |
| ITSM HTTP 클라이언트 | httpx, external ITSM | client secret과 bearer token을 request 경계에서 사용 |
| 자동화 테스트 기반 | app factory와 test doubles | 실제 ITSM/OpenAI 호출 없음 |

## 의도 관련 소유 경계

티켓 tool은 Agent 정의가 모델에 노출하지만 실행 권한은 Agent 실행 context의 서버 capability가 소유해야 한다. capability는 세션·위임 토큰 관리와 ITSM HTTP 클라이언트를 조율한다. 티켓 업무의 권한·가시성·priority·server-managed field는 ITSM 연동 계약이 소유하며 Assistant가 재구현하지 않는다.
