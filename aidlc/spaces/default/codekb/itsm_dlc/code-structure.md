# ITSM Assistant 코드 구조

## 저장소 구조

```text
app/                    Python FastAPI 애플리케이션
  agent/                Agents SDK 경계와 Agent HTTP API
docs/itsm/              외부 ITSM 연동 계약
scripts/                DB 초기화와 실제 모델 스모크 실행
static/                 빌드 없는 브라우저 UI
tests/                  pytest 통합·회귀 테스트와 테스트 대역
README.md               구조, 실행, API, 테스트, 확장 안내
requirements.in/.txt    직접 및 잠금 의존성
pytest.ini              테스트 탐색 설정
```

## 파일 분류

| 파일 | 분류 | 주요 제공 항목 | 직접 의존 |
|---|---|---|---|
| `app/config.py` | Configuration | `Settings`, 모델·reasoning 상수, 환경 설정 로드 | pathlib, dotenv |
| `app/db.py` | Repository/DAO | 세션 SQLite schema, 연결, 초기화, reset | sqlite3 |
| `app/itsm_auth.py` | Adapter/Service | `ItsmAuthClient`, 토큰 발급, 디렉터리·health 호출, ITSM 오류 | httpx, asyncio |
| `app/main.py` | Controller/Configuration | `create_app`, lifespan, health, 정적 파일 mount | FastAPI, app 서비스 |
| `app/schemas.py` | Model/DTO | 세션·Agent API Pydantic 입출력 | Pydantic |
| `app/session.py` | Controller/Service | CurrentUser, 세션 의존성, 위임 토큰 갱신, 사용자 API | FastAPI, db, ITSM client |
| `app/agent/assistant.py` | Configuration | Agent 지침, `TOOLS`, `build_agent` | Agents SDK, context |
| `app/agent/context.py` | Model/DTO | `AgentUserContext` | CurrentUser |
| `app/agent/routes.py` | Controller | 채팅·이력·초기화 API | FastAPI, schemas, session |
| `app/agent/service.py` | Service/Adapter | Runner 실행, SQLiteSession, 모델 오류 매핑, 이력 | Agents SDK, OpenAI, session |
| `static/index.html` | Static/UI | 페이지 구조와 사용자/대화 컨트롤 | app.js, style.css |
| `static/app.js` | Static/UI | API helper, 사용자 전환, 채팅, 이력 초기화 | 브라우저 fetch/DOM |
| `static/style.css` | Static/UI | 단일 패널 채팅 스타일 | 없음 |
| `tests/conftest.py` | Test/Fixture | FakeItsm, FakeModel, 앱·클라이언트 fixture | pytest, httpx, app |
| `tests/test_agent.py` | Test | Agent 구성/context/이력/오류/비노출 | app.agent, test fixtures |
| `tests/test_session.py` | Test | 사용자 전환, 세션, 토큰 갱신, UI/health | app.session, test fixtures |
| `scripts/reset_db.py` | Utility | 로컬 세션·대화 DB 초기화 | config, db |
| `scripts/agent_smoke.py` | Utility | 명시적 실제 모델 E2E 스모크 | httpx |
| `docs/itsm/*` | Contract/Documentation | ITSM API v2 정책과 OpenAPI 스키마 | 외부 ITSM 팀 계약 |

## 모듈 의존성

```text
app.main
 ├─ app.config
 ├─ app.db
 ├─ app.itsm_auth
 ├─ app.session
 └─ app.agent.routes
      └─ app.agent.service (app.state를 통해)
           ├─ app.agent.assistant
           │    └─ app.agent.context
           │         └─ app.session.CurrentUser
           ├─ app.config
           ├─ app.schemas
           └─ app.session

app.session
 ├─ app.db
 ├─ app.itsm_auth
 └─ app.schemas
```

Python import 수준의 순환 참조는 발견되지 않았다. `AgentUserContext`가 `CurrentUser`를 import하고 `AgentService`도 `CurrentUser`를 사용하지만 `session.py`는 agent 패키지를 import하지 않는다. `app.main`이 조립 루트다.

## 코드 패턴

- 앱 팩토리: import 시 전역 app/DB를 만들지 않고 `create_app()`에서 조립한다.
- 의존성 주입: FastAPI `Depends`로 DB/current user를 받고, 앱 팩토리 인자로 Settings/AgentService/ITSM client를 바꿀 수 있다.
- 외부 어댑터: `ItsmAuthClient`가 httpx 세부를 숨긴다.
- 서버 권위 세션: 보호 라우트는 cookie → SQLite session → `CurrentUser` 경로만 신뢰한다.
- SDK-native Agent: Agent/Runner/SQLiteSession을 직접 사용하고 자체 loop를 두지 않는다.
- Pydantic 경계 검증: 요청 model은 extra field를 금지하고 메시지 길이를 제한한다.
- 네트워크 대역: FakeModel과 MockTransport가 실제 SDK/HTTP 호출 경계를 대체한다.

## 티켓 기능 변경 표면

| 변경 지점 | 현재 상태 | 예상 책임 |
|---|---|---|
| `app/agent/assistant.py` | `TOOLS = []` | 정확히 세 function tool 등록과 도구 사용 지침 |
| `app/agent/context.py` | 사용자 메타데이터만 | 모델과 분리된 서버 ITSM capability 참조 |
| `app/agent/service.py` | `chat(user, message)`가 context 생성 | 요청/세션 결합 capability 구성 및 Runner 전달 |
| `app/itsm_auth.py` 또는 인접 모듈 | auth/directory만 | 목록·상세·등록·수정, 멱등키, `If-Match`, 안전 오류 |
| `app/session.py` | 요청 기반 `itsm_token_for()` | 도구 실행 중 갱신 가능한 위임 토큰 접근 경계 |
| `tests/conftest.py` | 업무 API 미구현 FakeItsm | 티켓 계약/권한/가시성/멱등/충돌 대역 |
| `tests/test_agent.py` | 빈 도구 계약 | 세 도구 schema·호출·비밀 비노출·기존 동작 회귀 |
| `README.md` | 추가 위치만 안내 | 실제 기능·설정·사용·테스트 문서 |

## 변경 시 주의할 결합

- 사용자 전환은 서버 세션과 이전 conversation 이력을 함께 삭제한다.
- `AgentService`가 만드는 Agent는 서비스 생성 시 고정되므로 도구 dependency를 전역 mutable 상태로 두면 테스트 격리가 깨질 수 있다.
- `CurrentUser`의 토큰은 frozen dataclass에 snapshot으로 들어 있어 갱신 뒤 동일 객체가 최신 토큰을 반영하지 않는다. capability는 `itsm_token_for()`의 반환값을 매 호출 사용해야 한다.
- `ItsmAuthClient._request()`는 현재 성공 응답을 항상 JSON으로 가정한다. 티켓 응답 header(ETag, Location, replay 표시)가 필요하면 응답 메타데이터 처리 경계를 확장해야 한다.
- 기존 `FakeModel`은 assistant 메시지만 반환해 function tool 호출 loop 검증을 위해 응답 구성 확장이 필요하다.
