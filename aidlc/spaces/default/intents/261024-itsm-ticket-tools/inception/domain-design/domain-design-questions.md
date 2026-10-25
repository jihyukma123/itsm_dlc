# Domain Design 질문

## Sources

- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `aidlc/spaces/default/codekb/itsm_dlc/architecture.md`
- `aidlc/spaces/default/codekb/itsm_dlc/component-inventory.md`
- `inception/practices-discovery/team-practices.md`
- `inception/refined-mockups/mockups.md`
- `inception/refined-mockups/interaction-spec.md`
- `construction/u2-ticket-write/functional-design/functional-design-questions.md`

## Q1. [아키텍처] 논리적 컴포넌트 경계

새 서비스나 배포 단위를 만들지 않으면서 티켓 기능의 책임을 기존 코드에 어떻게 배치할까요?

- A. 기존 `IdentitySession`, `AgentConversation`, `ItsmGateway`, `ConversationPresentation` 경계를 유지·확장하고, 확인·멱등성·충돌·오류 복구를 소유하는 내부 `TicketOperations` 논리 컴포넌트 하나를 추가한다. 이는 같은 FastAPI 프로세스 안의 코드 경계이며 새 서비스가 아니다. (Recommended)
- B. 티켓 로직을 기존 `AgentService`와 `ItsmAuthClient`에 직접 분산하고 별도 논리 컴포넌트를 만들지 않는다.
- C. 조회·등록·수정을 각각 별도 논리 컴포넌트로 나눈다.
- X. Other (please specify)

[Answer]: A. 기존 `IdentitySession`, `AgentConversation`, `ItsmGateway`, `ConversationPresentation` 경계를 유지·확장하고, 확인·멱등성·충돌·오류 복구를 소유하는 내부 `TicketOperations` 논리 컴포넌트 하나를 추가한다. 이는 같은 FastAPI 프로세스 안의 코드 경계이며 새 서비스가 아니다. (Recommended)

## Q2. [아키텍처] ITSM HTTP 경계 구성

인증과 티켓 호출이 같은 설정·HTTP 생명주기를 사용하되 업무 로직과 외부 계약 변환은 분리되어야 합니다. 내부 어댑터를 어떻게 구성할까요?

- A. 하나의 `ItsmGateway` 논리 컴포넌트가 기존 인증·디렉터리 경계와 새 카탈로그·티켓 HTTP 어댑터를 소유하고, 내부 클래스나 모듈로 책임을 나눈다. `TicketOperations`는 이 공개 경계만 호출한다. (Recommended)
- B. 기존 `ItsmAuthClient` 한 클래스에 인증·카탈로그·티켓 메서드를 모두 직접 추가한다.
- C. 인증, 카탈로그, 조회, 등록, 수정마다 독립 논리 컴포넌트를 만든다.
- X. Other (please specify)

[Answer]: A. 하나의 `ItsmGateway` 논리 컴포넌트가 기존 인증·디렉터리 경계와 새 카탈로그·티켓 HTTP 어댑터를 소유하고, 내부 클래스나 모듈로 책임을 나눈다. `TicketOperations`는 이 공개 경계만 호출한다. (Recommended)

## Q3. [보안·데이터] Assistant가 소유할 엔터티 범위

ITSM이 티켓의 원천인 상황에서 Assistant가 자체적으로 소유·보존할 데이터 범위를 어디까지로 제한할까요?

- A. Assistant는 네 업무·대화 엔터티 `ServerSession`, `Conversation`, `PendingTicketMutation`, `TicketCreateAttempt`와 두 기술 persistence 엔터티 `TicketCursorBinding`, `TicketMessagePresentation`만 소유한다. 티켓·카탈로그는 ITSM이 소유하는 외부 데이터로 취급해 필요한 순간의 안전한 projection만 사용한다. (Recommended)
- B. 조회한 티켓과 카탈로그 전체를 로컬 SQLite에 복제해 Assistant 엔터티로 소유한다.
- C. 등록·수정 보류 상태까지 SDK 대화 이력과 모델 문맥에만 보존한다.
- X. Other (please specify)

[Answer]: A. Assistant는 네 업무·대화 엔터티 `ServerSession`, `Conversation`, `PendingTicketMutation`, `TicketCreateAttempt`와 두 기술 persistence 엔터티 `TicketCursorBinding`, `TicketMessagePresentation`만 소유한다. 티켓·카탈로그는 ITSM이 소유하는 외부 데이터로 취급해 필요한 순간의 안전한 projection만 사용한다. (Recommended)

## Q4. [보안·데이터] 확인·멱등 상태의 보존 방식

프로세스 재시작과 불명확한 등록 결과에서도 중복 생성과 다른 사용자 재사용을 막으려면 보류 상태의 저장 위치와 결합 키를 정해야 합니다.

- A. `TicketOperations`가 서버 측 SQLite에 상태를 저장하고 사용자·서버 세션·대화·작업 종류·정규화된 본문 hash와, 수정의 경우 티켓 ID·version까지 결합한다. 사용자 전환·세션 종료·대화 초기화 시 관련 상태를 무효화한다. (Recommended)
- B. 프로세스 메모리에만 저장하고 재시작 시 폐기한다.
- C. 모델이 대화 이력에서 이전 확인을 추론하도록 한다.
- X. Other (please specify)

[Answer]: A. `TicketOperations`가 서버 측 SQLite에 상태를 저장하고 사용자·서버 세션·대화·작업 종류·정규화된 본문 hash와, 수정의 경우 티켓 ID·version까지 결합한다. 사용자 전환·세션 종료·대화 초기화 시 관련 상태를 무효화한다. (Recommended)

## Q5. [프런트엔드] 대화 표시 계약의 소유권

승인된 `TicketPresentationV1`은 기존 `reply` 계약을 유지하면서 성공·오류·확인 상태를 결정적으로 표시해야 합니다. 이 계약을 누가 소유할까요?

- A. 서버의 `ConversationPresentation` 경계가 안전한 도구 결과를 허용 목록의 `TicketPresentationV1`으로 매핑하고, 브라우저는 그 구조를 escape해 렌더링만 한다. 모델과 ITSM 원문은 DOM 역할·제목·live 우선순위를 선택하지 못한다. (Recommended)
- B. `TicketOperations`가 업무 처리와 UI 표시 계약을 함께 소유한다.
- C. 브라우저가 모델의 자유 형식 `reply` 문구를 분석해 상태와 접근성 의미를 추론한다.
- X. Other (please specify)

[Answer]: A. 서버의 `ConversationPresentation` 경계가 안전한 도구 결과를 허용 목록의 `TicketPresentationV1`으로 매핑하고, 브라우저는 그 구조를 escape해 렌더링만 한다. 모델과 ITSM 원문은 DOM 역할·제목·live 우선순위를 선택하지 못한다. (Recommended)

## Q6. [데이터 수명주기] TicketCreateAttempt 생성 시점

확인 turn 사이에서도 byte-identical body를 보존하면서 U1 공개 confirmation port만 사용하려면 등록 원장의 생성 시점을 상위 설계에 확정해야 합니다.

- A. `prepare`·`revise`에서 기존 `ticket_create_attempts`에 exact bytes·hash·key를 `prepared`로 먼저 저장하고, 그 뒤 U1 pending review를 공개한다. U1 consumption evidence와 U2 CAS claim이 있어야 POST할 수 있다. (Recommended)
- B. 확인 후에만 ledger를 만들고, 확인 전 bytes 보존을 위한 별도 schema 또는 shared contract를 추가한다.
- X. Other (please specify)

[Answer]: A. `prepare`·`revise`에서 기존 `ticket_create_attempts`에 exact bytes·hash·key를 `prepared`로 먼저 저장하고, 그 뒤 U1 pending review를 공개한다. U1 consumption evidence와 U2 CAS claim이 있어야 POST할 수 있다. (Recommended)

## Q7. [오류 복구] 일반 불명확 결과의 두 번째 등록 시도

첫 POST의 timeout·전송 단절처럼 결과가 불명확할 때, FR6.3과 AC2.1.5의 결과 확인 후 최대 2회 시도를 어떻게 보존할까요?

- A. 먼저 ITSM 결과를 조회하고, 티켓이 없으며 전역 attempt count가 2 미만일 때만 `retryable_after_reconcile`로 전환해 같은 key·same bytes를 다시 CAS claim한다. `retryable_no_apply`를 포함한 모든 retryable 상태는 이 하나의 최대 2회 POST 예산을 공유하며, 두 번째 불명확 결과는 terminal `ambiguous`로 둔다. (Recommended)
- B. 첫 불명확 결과부터 모든 추가 POST를 금지하고 수동 조정만 허용한다.
- C. 결과 확인 없이 새 idempotency key로 다시 등록한다.
- X. Other (please specify)

[Answer]: A. 먼저 ITSM 결과를 조회하고, 티켓이 없으며 전역 attempt count가 2 미만일 때만 `retryable_after_reconcile`로 전환해 같은 key·same bytes를 다시 CAS claim한다. `retryable_no_apply`를 포함한 모든 retryable 상태는 이 하나의 최대 2회 POST 예산을 공유하며, 두 번째 불명확 결과는 terminal `ambiguous`로 둔다. (Recommended)

## Q8. [오류 복구] consume_once 직후 crash 정책

U1 `consume_once` 성공 뒤 U2 ledger에 확인 증거를 결합하기 전에 프로세스가 중단되면 어떻게 복구할까요?

- A. U2는 반환된 mutation ID·확인 시각을 ledger에 즉시 idempotent하게 결합한다. 결합 전 crash에서는 기존 exact bytes·key를 유지한 채 새 pending review와 재확인을 요구하고, 결합된 증거가 있을 때만 실행을 재개한다. U1 schema나 cross-owner transaction은 추가하지 않는다. (Recommended)
- B. 결합되지 않은 소비도 확인된 것으로 추정해 바로 POST한다.
- C. U1과 U2를 묶는 새 cross-owner transaction port를 추가한다.
- X. Other (please specify)

[Answer]: A. U2는 반환된 mutation ID·확인 시각을 ledger에 즉시 idempotent하게 결합한다. 결합 전 crash에서는 기존 exact bytes·key를 유지한 채 새 pending review와 재확인을 요구하고, 결합된 증거가 있을 때만 실행을 재개한다. U1 schema나 cross-owner transaction은 추가하지 않는다. (Recommended)

## Consolidated Summary Confirmation

- 기존 네 컴포넌트 경계를 확장하고, 확인·멱등성·충돌·오류 복구를 소유하는 내부 `TicketOperations` 논리 컴포넌트를 추가한다. 새 서비스나 배포 단위는 만들지 않는다.
- 하나의 `ItsmGateway`가 인증·디렉터리·카탈로그·티켓 HTTP 경계를 소유하며 내부 클래스·모듈로 책임을 나눈다.
- Assistant는 네 업무·대화 엔터티와 두 기술 persistence 엔터티만 소유하고 티켓·카탈로그는 ITSM 원천 데이터로 유지한다.
- 보류 변경과 등록 시도는 서버 측 SQLite에 사용자·세션·대화·본문 hash 및 필요한 티켓 ID·version과 결합해 저장한다. 수명주기 변경은 revocable `PendingTicketMutation`을 무효화하지만 durable `TicketCreateAttempt`는 보존한다.
- `ticket_write`의 `prepare`·`revise`는 기존 `ticket_create_attempts`에 exact canonical bytes·hash·한 idempotency key를 `prepared`로 먼저 저장한 뒤 U1 pending review를 공개한다. 별도 pre-confirm table이나 cross-owner transaction port는 만들지 않는다.
- U1 공개 `consume_once`가 같은 mutation의 confirmation을 입증한 뒤 U2 CAS claim 승자만 POST한다. Ledger는 confirmation 시점부터 최소 24시간으로 보존을 연장한다.
- `consume_once` 증거는 mutation ID·확인 시각으로 ledger에 idempotent하게 결합한다. 결합 전 crash에서는 기존 bytes·key를 유지한 새 pending review와 재확인을 요구하고, 결합된 증거가 있을 때만 실행을 재개한다.
- Durable claim은 claim identity와 deadline을 가진다. stale `in_flight`는 먼저 결과를 확인하고, 티켓이 없으며 전역 attempt count가 2 미만일 때만 `retryable_after_reconcile`로 전환해 same-key·same-bytes 두 번째 CAS 시도를 허용한다. 두 번째 불명확 결과는 terminal `ambiguous`로 둔다.
- 변경 미적용이 보장된 token-expired 401은 `retryable_no_apply`로 기록하지만 별도 재시도 예산을 만들지 않는다. `retryable_after_reconcile`과 `retryable_no_apply`를 포함한 모든 POST CAS claim은 동일한 전역 attempt count가 2 미만일 때만 허용한다.
- `ConversationPresentation`이 허용 목록 기반 `TicketPresentationV1` 매핑을 소유하며 브라우저는 escape 후 렌더링만 한다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
