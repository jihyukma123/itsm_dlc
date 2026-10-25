# ITSM Assistant API 문서

## Inbound HTTP API

### 시스템과 정적 화면

| 메서드 | 경로 | 인증 | 요청 | 성공 응답 | 구현 |
|---|---|---|---|---|---|
| GET | `/api/health` | 없음 | 없음 | 앱 상태, ITSM reachable/version, Agent configured/model/reasoning | `app/main.py` |
| GET | `/` | 없음 | 없음 | `static/index.html` | `app/main.py` |
| GET | `/static/*` | 없음 | 경로 | 정적 자산 | FastAPI StaticFiles |

### 사용자와 세션

| 메서드 | 경로 | 인증 | 요청 | 성공 응답 | 주요 오류 |
|---|---|---|---|---|---|
| GET | `/api/users` | 없음 | 없음 | 활성 ITSM 사용자 목록, permissions 제외 | 503 `itsm_unavailable`, 502 `itsm_auth_failed` |
| GET | `/api/session` | 세션 쿠키 | 없음 | 현재 사용자와 permissions | 401 `no_session` |
| POST | `/api/session` | 없음 | `{user_id: int}`; extra 금지 | 새 현재 사용자와 HttpOnly 세션 쿠키 | 404 `user_not_found`, 409 `user_inactive`, ITSM 오류 |
| DELETE | `/api/session` | 없음 | 없음 | 204, 세션 쿠키·대화 제거 | 없음 |

### Agent

| 메서드 | 경로 | 인증 | 요청 | 성공 응답 | 주요 오류 |
|---|---|---|---|---|---|
| POST | `/api/agent/chat` | 세션 쿠키 | `{message}` 1–4000자, extra 금지 | `{reply, context: {user_id, username, role}}` | 401 `no_session`, 503 `agent_not_configured`, 모델 오류 |
| GET | `/api/agent/messages` | 세션 쿠키 | 없음 | user/assistant 메시지 목록 | 401 `no_session` |
| DELETE | `/api/agent/messages` | 세션 쿠키 | 없음 | 204 | 401 `no_session` |

현재 API는 사용자 ID·role·permissions를 채팅 요청 body에서 받지 않는다. 서버 세션의 `CurrentUser`가 유일한 실행 주체다.

## Outbound ITSM API — 현재 구현

`ItsmAuthClient`는 base URL과 timeout을 가진 공유 `httpx.AsyncClient`를 사용한다.

| 메서드 | 경로 | 인증 | 사용 목적 |
|---|---|---|---|
| POST | `/api/v2/auth/token` | client credentials body | 서비스 토큰 또는 사용자 위임 토큰 발급 |
| GET | `/api/v2/me` | 위임 bearer | 현재 위임 사용자·permissions 검증 |
| GET | `/api/v2/users` | 서비스 bearer | 활성 사용자 페이지 순회 |
| GET | `/api/v2/users/{id}` | 서비스 bearer | 전환 대상 사용자 상세 |
| GET | `/api/v2/health` | 없음 | 상태·버전 확인 |

서비스 GET은 만료 60초 전 또는 401 후 한 번 서비스 토큰을 갱신한다. 사용자 위임 토큰은 `session.itsm_token_for()`가 만료 60초 전에 다시 교환하고 SQLite 행을 갱신한다.

## Outbound ITSM API — 문서화됐지만 미구현인 티켓 계약

### 조회

| 모드 | 메서드·경로 | 권한 | 입력 | 응답 |
|---|---|---|---|---|
| 목록·검색 | GET `/api/v2/tickets` | `ticket:read` | `sort`, `limit` 1–100, opaque `cursor`, `q`, 반복 `status`/`priority`, service/component/model, assignment/assignee/requester, classification, major, 시간 필터 | `TicketPage {items: TicketSummaryOut[], page}` |
| 상세 | GET `/api/v2/tickets/{ticket_id}` | `ticket:read` | 대소문자 무시 ID | `TicketOut`, ETag version |

정렬은 `-created_at`, `-updated_at`, `priority`만 허용한다. 같은 검색 조건에서만 cursor를 재사용한다. 가시성 밖 티켓은 부재와 같은 404 `ticket_not_found`다.

### 등록

POST `/api/v2/tickets`, 사용자 위임 토큰과 `ticket:create` 권한을 사용한다.

필수 body: `title`(1–200), `description`(1–5000), `service_id`(1–50), `impact_level`, `urgency`, `impact_note`(1–1000), timezone-aware `occurred_at`.

선택 body: `component_id`, `model`(최대 50), `classification`(`standard` 기본 또는 `restricted`). 추가 필드는 금지된다. ID, 요청자, 상태, 우선순위, 담당 그룹과 서버 시각은 ITSM이 정한다.

선택 `Idempotency-Key`는 동일 사용자 기준 24시간 유효하다. 같은 키·같은 body는 201과 기존 결과를 반환하며 replay header를 보낸다. 같은 키·다른 body는 422 `idempotency_key_reused`다.

### 수정

PATCH `/api/v2/tickets/{ticket_id}`, 위임 토큰과 `If-Match: "<version>"`를 사용한다.

허용 body는 `title`, `description`, `component_id`, `model`, `impact_level`, `urgency`, `impact_note`, `is_major`뿐이며 추가 필드는 금지된다. 빈 수정은 422 `empty_update`다. 일반 수정은 `ticket:update`가 필요하며 요청자 본인은 received 상태에서 제목·설명·영향 범위만 수정할 수 있다. `is_major`는 별도 권한이 필요하다.

`If-Match`가 없으면 428, version이 다르면 412 `version_conflict`와 current version이 반환된다. 성공하면 version이 증가한다.

## ITSM 오류 계약과 안전 경계

ITSM 오류는 `application/problem+json`이며 안정적 `code`, HTTP `status`, 사람용 `detail`, `request_id`와 선택된 구조 필드를 가진다. 대표 코드는 인증 401, 권한 403, 비노출 404, version 412/428, 검증 422, rate limit 429다.

현재 `_error_from()`은 problem 전체와 원문 detail을 보존하고 `itsm_http_error()`는 일부 detail을 사용자에게 보낸다. 티켓 도구에는 다음 안전 경계가 필요하다.

- 모델/사용자 결과는 허용 목록의 code·status·안전 문구·request ID만 사용한다.
- 원본 header, response body, URL query, 예외 문자열, bearer token, client secret을 직렬화하지 않는다.
- 404에서 부재와 권한 부족을 구분하지 않는다.
- 401은 서버에서 토큰 갱신 또는 재로그인 흐름으로 처리하고 토큰 상태를 설명하지 않는다.
- 429의 `Retry-After`는 숫자 대기 정보로만 정제한다.
- POST/PATCH는 성공 여부가 불명확할 때 새 요청으로 무조건 재시도하지 않는다.

## OpenAI Agents SDK API 경계

- `build_agent(model)`은 고정 instructions, model settings와 `list(TOOLS)`로 Agent를 만든다.
- `Runner.run(agent, message, context=AgentUserContext, session=SQLiteSession, tracing_disabled=True)`가 현재 실행 계약이다.
- `TOOLS`는 비어 있다. 향후 정확히 세 function tool의 모델 노출 schema에는 업무 인자만 포함하고 token/client/API key는 포함하지 않아야 한다.
- 현재 `FakeModel.get_response()`는 도구 schema와 input을 기록하지만 tool call output을 만들지는 않는다.

## 응답 스키마와 저장 계약

- FastAPI schema는 `app/schemas.py`의 Pydantic model로 고정한다.
- 서버 세션 DB는 사용자 메타데이터, permissions JSON, conversation ID, 위임 토큰과 만료 시각을 저장한다.
- Agent 대화 이력은 SDK가 관리하며 HTTP API는 user/assistant message만 반환한다.
- 티켓 업무 데이터는 로컬 DB에 저장하지 않는다. 단, 멱등 요청 상태를 보존할 설계가 필요하며 저장 위치는 아직 결정되지 않았다.
