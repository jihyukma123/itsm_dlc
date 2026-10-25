# ITSM Assistant 의존성 분석

## 직접 외부 의존성

| 의존성 | 버전 | 사용 위치 | 책임 |
|---|---:|---|---|
| fastapi | 0.162.0 | `app/main.py`, routes, session | HTTP routing, DI, schema response, static files |
| uvicorn | 0.54.0 | 실행 명령 | ASGI server |
| openai-agents | 0.24.0 | `app/agent/*`, tests | Agent, Runner, model abstraction, SQLiteSession, tool 확장점 |
| python-dotenv | 1.2.4 | `app/config.py` | local env file parsing |
| pytest | 9.1.1 | `tests/` | 자동화 test runner |
| httpx | 0.28.1 | `app/itsm_auth.py`, tests, smoke | async HTTP, MockTransport, sync smoke client |

`requirements.txt`는 위 직접 의존성의 transitive graph를 고정한다. 핵심 transitive 항목은 OpenAI 3.37.0, Pydantic 2.14.1, Starlette 1.10.0, AnyIO 4.15.1, MCP 2.3.0이다.

## 내부 의존성 그래프

```text
app.config <- app.main, app.agent.assistant, app.agent.service, scripts
app.db <- app.main, app.session, scripts.reset_db
app.itsm_auth <- app.main, app.session, tests
app.schemas <- app.session, app.agent.routes, app.agent.service
app.session <- app.main, app.agent.context, app.agent.routes, app.agent.service
app.agent.context <- app.agent.assistant, app.agent.service, tests
app.agent.assistant <- app.agent.service, tests
app.agent.service <- app.main, app.agent.routes, app.session(app.state callback), tests
```

정적 client는 HTTP 경로에 의존할 뿐 Python module에 직접 결합하지 않는다. Tests는 앱 팩토리의 주입 인자로 외부 모델과 ITSM을 대체한다.

## 외부 서비스 의존성

### ITSM API v2

- 동기화 경계: 사용자 목록·상세, token exchange, `/me`, health.
- 의도 관련 미구현 경계: ticket list/detail/create/update.
- 가용성 영향: 사용자 목록·전환은 ITSM이 없으면 실패하지만 앱 health 자체는 200으로 degraded 상태를 표시한다.
- 신뢰 경계: 권한·가시성·server-managed fields는 ITSM이 소유한다.
- 제한: 10초 기본 timeout, 주체별 분당 300회, 429 Retry-After, cursor condition consistency.

### OpenAI Responses API

- 채팅마다 Agents SDK Runner가 호출한다.
- 설정이 없으면 chat만 503이고 session/UI는 동작한다.
- 모델은 고정되며 auth/permission/not found/bad request/rate/connection 오류별 API 응답으로 변환된다.
- 실제 자동화 테스트는 FakeModel로 대체한다.

## 데이터 의존성

| 저장소 | owner | 내용 | 생명주기 |
|---|---|---|---|
| 서버 세션 SQLite | app | 검증된 사용자, permissions, conversation ID, 위임 token·expiry | 사용자 전환마다 이전 행 삭제 후 새 행, session 종료 시 삭제 |
| SDK 이력 SQLite | Agents SDK | user/assistant conversation items | conversation ID별, 전환·clear·session 종료 시 삭제 |
| ITSM 원장 | 외부 ITSM | 사용자 directory, tickets, catalog, permissions | Assistant가 HTTP 계약으로만 접근 |

## 티켓 도구 도입 의존성

1. `function_tool` schema는 ITSM OpenAPI의 enum·길이·nullable·extra-forbidden 계약에 맞아야 한다.
2. tool 실행은 `AgentUserContext`에서 server capability를 얻되 secret 값을 field/repr/model schema에 포함하지 않아야 한다.
3. capability는 현재 request와 `itsm_token_for()`를 연결하거나 동등한 갱신 가능한 session abstraction을 사용해야 한다.
4. ITSM client는 JSON body뿐 아니라 ETag/Location/replay/Retry-After 같은 필요한 response header를 안전하게 읽을 수 있어야 한다.
5. 등록 retry는 conversation/request에 보존되는 idempotency state에 의존한다.
6. 수정은 detail read가 제공한 version과 PATCH `If-Match`를 동일 use case에 유지해야 한다.
7. FakeModel은 function tool call과 tool output round trip을 생성할 수 있어야 하고 FakeItsm은 ticket 계약을 구현해야 한다.

## 결합 위험

- `AgentService`는 생성 시 Agent와 tools를 고정하므로 request별 dependency는 global tool object가 아니라 typed context로 전달해야 한다.
- frozen CurrentUser의 token snapshot은 refresh 뒤 stale하므로 장기 tool chain은 매번 갱신 함수를 사용해야 한다.
- httpx client가 앱 단위로 공유되므로 request별 bearer header를 client default header에 저장하면 사용자 간 누출 위험이 있다. 현재처럼 호출 인자로 전달해야 한다.
- SQLite write는 동기식이며 FastAPI async 경로에서 짧은 transaction으로만 사용한다. 멱등 상태를 추가하면 경쟁 요청과 transaction 범위를 설계해야 한다.
- current `ItsmApiError.problem`과 detail은 untrusted upstream data이므로 모델 결과나 logs로 직접 전달하면 안 된다.

## 발견된 순환과 중복

정적 Python import 순환은 발견되지 않았다. 설정·세션·AgentService가 앱 팩토리에서 조립되는 구조는 명확하다. ITSM 오류 → FastAPI 오류 mapping은 `session.py`에 있어 향후 tool-safe 오류와 HTTP route 오류가 같은 원문 detail 규칙을 무심코 공유할 위험이 있다.
