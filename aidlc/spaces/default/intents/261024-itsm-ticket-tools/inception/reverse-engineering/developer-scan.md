## Developer Code Scan Results

### Scan Coverage

- **Analyzed deeply**:
  - `README.md`, `requirements.in`, `requirements.txt`, `pytest.ini`, `.python-version`, `.env.local.example`
  - `app/` — FastAPI 진입점, 설정, SQLite 세션 저장소, ITSM 인증 클라이언트, 세션/위임 토큰, API 스키마
  - `app/agent/` — Agent 정의, 실행 context, Runner/SQLiteSession 서비스, 채팅 라우트
  - `tests/` — Fake ITSM, FakeModel, 세션·Agent·오류·회귀 테스트
  - `static/` — 기존 사용자 전환·대화 화면의 HTML, JavaScript, CSS
  - `scripts/` — DB 초기화와 실제 모델 스모크 스크립트
  - `docs/itsm/integration-guide.md`, `docs/itsm/openapi.json` — 전체 API 표면과 티켓 목록·상세·등록·수정 계약
- **Skimmed only**: None. OpenAPI는 전체 경로·스키마 목록을 확인하고 이번 의도에 직접 관련된 티켓 작업과 입력·응답 스키마를 상세 분석했다.
- **Left out**:
  - `.venv/`, `.pytest_cache/`, 모든 `__pycache__/`, `*.pyc` — 의존성·캐시·컴파일 산출물
  - `.git/` — 버전관리 내부 데이터
  - `.env.local` — gitignore 대상이며 실제 비밀정보를 포함할 수 있어 열지 않음
  - `data/` — gitignore 대상 런타임 SQLite 데이터(현재 디렉터리도 없음)
  - `.codex/`, `.agents/`, `aidlc/`, `AGENTS.md`와 `.gitignore`의 AI-DLC 관리 구간 — AI-DLC 자체 설치·워크플로 기록

### Packages Found

- `app` — 애플리케이션 패키지 — Python — FastAPI 앱, 설정, 세션, ITSM HTTP 연동, SQLite 저장
- `app.agent` — 애플리케이션 패키지 — Python — OpenAI Agents SDK Agent·Runner·대화 이력·채팅 API
- `tests` — 테스트 패키지 — Python — pytest, FastAPI TestClient, FakeModel, `httpx.MockTransport`
- `static` — 정적 웹 클라이언트 — HTML/CSS/JavaScript — 사용자 전환과 대화 UI
- `scripts` — 운영·개발 유틸리티 — Python — 로컬 DB 초기화와 명시적 실제 모델 스모크 실행
- `docs/itsm` — 외부 계약 문서 — Markdown/OpenAPI JSON — ITSM API v2 인증·권한·가시성·티켓 계약

### Build System

- **Type**: Python 3.13 + pip/uv. 패키지 빌드는 없고 `requirements.in`에서 고정 `requirements.txt`를 생성한다.
- **Config Files**: `.python-version`, `requirements.in`, `requirements.txt`, `pytest.ini`, `.env.local.example`
- **Build Dependencies**: `app` → FastAPI/Pydantic/httpx/OpenAI Agents SDK; `tests` → `app` + pytest/FastAPI TestClient/httpx; `static`은 빌드 도구 없이 FastAPI가 직접 제공한다.

### APIs Discovered

- FastAPI inbound API — `app/main.py`, `app/session.py`, `app/agent/routes.py` — 9개 공개 라우트: health, 사용자 목록, 세션 조회·전환·종료, Agent 채팅·이력 조회·초기화, 정적 루트
- ITSM outbound API — `app/itsm_auth.py` — 현재 6개 인증·디렉터리·상태 호출: 토큰, 사용자 목록/상세, 현재 사용자, 상태 확인
- ITSM 티켓 계약 — `docs/itsm/` — API v2의 목록, 상세, 등록, 수정 엔드포인트가 문서화됐지만 애플리케이션 클라이언트와 Agent 도구에는 미구현
- OpenAI outbound API — `app/agent/service.py` — Agents SDK `Runner.run`이 고정 Responses 모델을 호출하며 SDK 트레이싱은 비활성

### Frameworks & Libraries

- Python — 3.13 — 런타임
- FastAPI — 0.162.0 — HTTP 앱과 의존성 주입
- Uvicorn — 0.54.0 — ASGI 서버
- OpenAI Agents SDK — 0.24.0 — Agent, Runner, function tool 확장 지점, SQLiteSession
- OpenAI Python — 3.37.0 — Responses 모델 클라이언트와 오류 계층
- Pydantic — 2.14.1 — API 입출력 검증
- httpx — 0.28.1 — 비동기 ITSM HTTP 클라이언트와 MockTransport 테스트
- pytest — 9.1.1 — 자동화 테스트
- python-dotenv — 1.2.4 — `.env.local` 설정 로드
- SQLite — Python 표준 라이브러리 + Agents SDK — 서버 세션과 대화 이력
- 브라우저 표준 API — 빌드 없는 HTML/CSS/JavaScript 클라이언트

### Test Coverage

- **Test Directories**: `tests/` (`conftest.py`, `test_agent.py`, `test_session.py`)
- **Test Frameworks**: pytest, FastAPI TestClient, `httpx.MockTransport`, Agents SDK를 실제로 통과하는 FakeModel
- **Coverage Config**: 없음. 문서화된 기준선은 기존 37개 통과이며 이번 읽기 전용 스캔에서는 테스트나 coverage를 실행하지 않았다.

### Code Quality Indicators

- **Linting**: 전용 formatter/linter 설정 없음. `scripts/reset_db.py`의 두 `# noqa: E402` 외 억제 표시는 발견되지 않았다.
- **CI/CD**: 저장소에 프로젝트 소유 CI/CD 구성 없음.
- **Documentation**: 한국어 README가 구조·실행·API·테스트·확장 지점을 상세히 설명하고, ITSM 팀의 연동 가이드와 OpenAPI 3.1 계약이 함께 있다.
- **구조**: 작은 단일 FastAPI 서비스로 책임이 비교적 분리되어 있고 `create_app()` 주입 경계가 테스트 대역 사용을 쉽게 한다.

### Technical Debt Signals

- `app/agent/assistant.py`의 `TOOLS`가 비어 있고, `test_agent_has_no_tools` 및 여러 테스트가 빈 도구 목록을 명시적으로 고정한다.
- `AgentUserContext`는 검증된 사용자 메타데이터만 담고 요청/ITSM 클라이언트/갱신 가능한 위임 capability가 없어 도구가 안전하게 업무 API를 호출할 경계가 없다.
- `ItsmAuthClient`는 인증·디렉터리만 구현하며 티켓 목록·상세·등록·수정, 멱등키, `If-Match`, 412/428/429 처리 메서드가 없다.
- `ItsmApiError`가 원본 `detail`과 전체 problem 객체를 보유하고 일부 현재 오류 매핑이 detail을 사용자 응답으로 전달하므로, 티켓 도구에는 허용 목록 기반 안전 오류 DTO가 필요하다.
- 개발용 클라이언트 secret 기본값이 코드와 문서에 존재한다. 현재 파일은 `repr=False`를 사용하지만 운영 자격증명과 도구 오류/로그 경계는 별도 검증이 필요하다.
- 기존 redaction은 OpenAI 키 형태만 가리며 bearer 토큰이나 ITSM client secret을 일반적으로 탐지하지 않는다.
- 동시 세션 요청 간 토큰 갱신을 직렬화하는 per-session 잠금이나 등록 멱등 상태 저장 구조가 아직 없다.
- coverage 설정, lint 설정, 프로젝트 CI가 없어 자동 품질 기준은 pytest 결과에 의존한다.
- 정적 UI는 기본 채팅 동작은 갖췄지만 live region/alert와 명시적 heading/landmark 강화가 현재 구현에는 없다.

## Handoff Summary

- **Intent-relevant finding**: 가장 작은 변경 경로는 기존 `ItsmAuthClient`, `AgentUserContext`, `AgentService.chat()`, `assistant.TOOLS`를 확장하고 `tests/conftest.py`의 FakeItsm/FakeModel 기반을 재사용하는 것이다. 현재 실행 경로는 `app/agent/routes.py` → `AgentService.chat()` → `Runner.run(..., context=AgentUserContext, session=SQLiteSession)`이며 도구·업무 API만 비어 있다.
- **Risks / follow-up**: 서버 요청과 갱신 가능한 위임 토큰을 모델과 분리한 capability, 등록 멱등 상태의 수명주기, 수정 전 version/`If-Match`, 원본 오류 비노출, 정확히 세 도구만 노출하는 회귀 계약을 Inception 설계에서 먼저 확정해야 한다. 기존 테스트 기대는 의도적으로 갱신하되 사용자 전환·세션·대화 이력·고정 모델 동작은 유지해야 한다.
