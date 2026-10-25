# ITSM Assistant 코드 품질 평가

## 종합 평가

현재 코드는 작은 FastAPI 애플리케이션에 맞는 명확한 모듈 경계, 앱 팩토리 기반 의존성 주입, 외부 서비스 대역을 활용한 테스트 기반을 갖추고 있어 전반적으로 **양호(Good)** 하다. 다만 티켓 도구를 추가할 때 사용자 위임 토큰의 수명주기, upstream 오류 정제, 쓰기 멱등성 및 낙관적 동시성 같은 보안·정합성 요구를 기존 경계에 명시적으로 보강해야 한다.

README에 기록된 현재 기준선은 자동화 테스트 37개 통과이다. Reverse Engineering 단계의 읽기 전용 원칙에 따라 이번 분석에서는 프로젝트 테스트, 빌드 또는 프로그램을 실행하지 않았으므로 이 수치를 재검증하지 않았다.

## 품질 특성별 평가

| 항목 | 평가 | 근거 |
|---|---|---|
| 명명과 가독성 | Good | 모듈·함수 이름이 역할을 직접 드러내며 request, session, agent 경계가 구분된다. |
| 함수와 모듈 크기 | Fair | 대부분 작지만 `app/session.py`는 약 240줄이고 일부 경로 함수는 인증·저장·오류 변환을 함께 처리한다. |
| 오류 처리 | Fair | OpenAI 및 ITSM 오류를 HTTP 응답으로 구분하지만 upstream `detail`/`problem`을 신뢰 경계 밖으로 전달할 여지가 있다. |
| 테스트 가능성 | Good | `create_app()` 주입점, `FakeModel`, `httpx.MockTransport`로 실제 OpenAI 호출 없이 주요 흐름을 시험한다. |
| 중복 | Good | 공통 설정, DB 연결, 사용자 로딩, Agent 실행이 각각 한 경계에 모여 있다. |
| 불용·잔여 코드 | Good | 명시적인 TODO/FIXME/HACK은 발견되지 않았고, reset script의 두 `noqa`는 import 위치를 설명하는 제한적 예외다. |
| 타입·계약 표현 | Good/Fair | Pydantic과 dataclass를 사용하지만 ITSM ticket 입력·출력 모델과 tool schema는 아직 없다. |
| 보안 기본값 | Good/Fair | token은 server-side SQLite에 있고 context repr에서 제외되지만 일반 upstream 오류와 비-OpenAI secret 정제 규칙은 보강이 필요하다. |

## 강점

- 앱 팩토리가 model provider와 ITSM transport를 주입할 수 있어 테스트와 운영 구성이 분리된다.
- model 설정이 없을 때 임의 모델로 fallback하지 않고 chat 기능만 명시적으로 503을 반환한다.
- server-side session이 현재 사용자와 위임 token의 권위 있는 저장소이며 브라우저에는 session cookie만 전달한다.
- `FakeModel`과 `MockTransport`가 실제 OpenAI·ITSM 호출 없는 자동화 테스트 패턴을 이미 제공한다.
- 사용자 context는 token을 repr과 모델 입력에서 제외하도록 설계되어 secret 노출 면적이 작다.
- integration guide와 OpenAPI가 인증, 오류, pagination, idempotency, ETag 조건을 상세히 정의한다.
- 사용자 전환 시 기존 conversation과 SDK session을 폐기하는 흐름이 테스트되어 사용자 간 이력 누출을 방지한다.

## 확인된 격차와 위험

- `Agent`의 tool 목록은 현재 비어 있다. 이는 기존 결함이라기보다 이번 intent가 채워야 할 확장점이다.
- `AgentUserContext`에는 request마다 갱신 가능한 ITSM capability가 없어, frozen user의 token snapshot만 사용하면 refresh 이후 stale credential이 될 수 있다.
- `ItsmApiError.problem`과 upstream detail은 외부 입력이다. 모델 도구 결과, 로그 또는 클라이언트 오류에 원문을 그대로 전달하면 credential·내부 정보 노출 위험이 있다.
- 개발용 설정에는 고정된 기본 credential이 존재한다. 값 자체는 이 분석에 재기록하지 않았지만 운영 환경에서는 명시적 환경변수와 fail-safe 검증이 필요하다.
- 현재 redaction과 오류 분류는 주로 OpenAI API 오류에 초점이 있다. bearer token, client secret, OpenAI key를 공통으로 다루는 정제 경계가 필요하다.
- formatter, linter, type checker, coverage threshold, CI 구성이 repository에 명시되어 있지 않다.
- 동시에 여러 요청이 만료 직전 token을 갱신할 때 중복 exchange와 session overwrite 경쟁이 가능하다.
- ticket list/detail/create/update와 function-tool round trip을 검증하는 자동화 테스트는 아직 없다.
- 정적 UI는 기본적인 label과 상태 표시는 제공하지만 focus 관리, live-region 세분화, 키보드 상호작용에 대한 자동 접근성 검증은 없다.
- `scripts/smoke.sh`에는 수동 확인을 위한 예시 질의가 있으나 제품 지침이나 tool code의 특정 ticket ID 하드코딩은 발견되지 않았다.

## 테스트 자산과 공백

| 영역 | 현재 자산 | 티켓 도구 도입 시 필요한 보강 |
|---|---|---|
| HTTP 앱 | FastAPI TestClient 기반 session/chat/health 검증 | 기존 endpoint 회귀와 tool-enabled Agent 조립 검증 |
| OpenAI | `FakeModel`로 응답을 합성해 실제 API 호출 방지 | function call → tool result → final response의 다중 turn fixture |
| ITSM | `FakeItsm` 및 `MockTransport`로 인증·사용자 API 대체 | ticket v2 endpoint, pagination, 404, 409, 412, 422, 429, timeout 대역 |
| 세션 | 생성·전환·종료·이력 삭제 검증 | token refresh와 tool 실행의 동일-user binding, 동시 refresh |
| 보안 | context repr에서 token 제외, 오류 메시지 일부 검증 | token·client secret·OpenAI key가 tool output/log/error에 없는지 sentinel 검사 |
| 쓰기 정합성 | 해당 없음 | idempotency replay/conflict와 PATCH `If-Match` 성공/실패 검증 |

## 기술 부채 우선순위

1. **P0 — 비밀정보 경계:** tool context에 secret을 직접 노출하지 않고, ITSM 오류를 allow-list 기반의 안전한 결과로 변환한다.
2. **P0 — 쓰기 정합성:** create의 `Idempotency-Key`, update의 `If-Match`와 version 전달을 계약대로 구현하고 테스트한다.
3. **P0 — 정확한 권한 위임:** 도구 호출마다 현재 server session과 refresh 가능한 사용자 token을 사용하며 권한·가시성 판단은 ITSM에 맡긴다.
4. **P1 — 계약 모델:** OpenAPI와 일치하는 enum, 길이, nullable, extra-field 금지, pagination 모델을 한 곳에 정의한다.
5. **P1 — 도구 테스트:** 정확히 세 tool의 schema 및 성공·오류·redaction 경로를 FakeModel/FakeItsm으로 검증한다.
6. **P2 — 품질 자동화:** formatter/linter/type-checker/coverage 및 CI 기준을 별도 작업으로 명시한다.
7. **P2 — 접근성:** chat 상태 변화와 오류 공지를 보조기술이 확실히 인식하도록 자동 검사 범위를 추가한다.

## 변경 시 유지해야 할 품질 게이트

- 새 Agent나 별도 service를 만들지 않고 기존 `AgentService`, context, session 경계를 확장한다.
- Agent에 공개되는 ticket tool 이름은 `ticket_read`, `ticket_write`, `ticket_update` 세 개뿐이어야 한다.
- 제품 코드·지침·테스트 fixture에 특정 실운영 ticket ID나 sample ticket을 결합하지 않는다.
- 실제 OpenAI API를 호출하지 않는 전체 테스트가 유지되어야 한다.
- token, client secret, OpenAI API key가 모델 입력, tool result, 로그, HTTP 오류에 나타나지 않는 회귀 테스트가 필요하다.
- 기존 사용자 전환, session, 대화 이력, 고정 model, 화면과 API 동작을 회귀 테스트한다.
