# U1 Ticket Read Skeleton — Security Design

## Sources

- `construction/u1-ticket-read-skeleton/nfr-requirements/security-requirements.md`
- `construction/u1-ticket-read-skeleton/nfr-requirements/tech-stack-decisions.md`
- `construction/u1-ticket-read-skeleton/functional-design/functional-spec.md`
- `construction/u1-ticket-read-skeleton/functional-design/rules.md`
- `inception/contract-design/contract-summary.md`
- `inception/domain-design/components.md`
- `construction/u1-ticket-read-skeleton/nfr-design/nfr-design-questions.md`

## Scope and Security Posture

U1은 기존 FastAPI 애플리케이션 안에 포함되는 library 경계다. 새 인증 체계, 별도 서비스, cache, queue, circuit breaker, WAF, KMS 또는 secrets manager를 추가하지 않는다. 대신 기존 서버 session과 사용자 위임 credential을 권한의 유일한 원천으로 유지하고, ITSM API v2를 외부 권한·가시성의 최종 판정자로 둔다.

이 설계가 보호하는 자산은 현재 사용자 신원, 위임 credential, 안전하게 투영한 티켓 데이터, server-bound continuation, 향후 U2·U3가 사용할 confirmation state, assistant message와 presentation metadata의 정확한 상관관계다. `Ticket`, `Service`, `Component`, `Model` 자체는 Assistant가 소유하거나 복제하지 않는다.

## Security Design Decisions

| ID | 결정 | 강제 경계 | 실패 시 동작 |
|---|---|---|---|
| SEC-U1-01 | 서버 session에서만 `TicketRequestCapability`를 만들고 model/tool input에는 신원·role·credential field를 두지 않는다. | `ApplicationLifecycle` → `IdentitySession` | capability를 만들 수 없으면 Runner와 ITSM 호출 없이 `authentication_required`로 종료한다. |
| SEC-U1-02 | capability는 요청 범위, 비직렬화, 비로그, 비모델 가시 객체이며 credential 값은 `ItsmGateway` outbound adapter만 사용할 수 있다. | capability provider와 gateway adapter | 직렬화·repr·schema 변환 시 credential field를 만들지 않고 안전 실패한다. |
| SEC-U1-03 | `TicketOperations`가 read operation의 deadline, 최대 두 HTTP 시도, credential refresh 한 번과 250ms retry 한 번을 단독 소유한다. read용 내부 `ReadCredentialRefreshPortV1`은 pre-call unusable credential과 typed 401을 같은 one-shot budget으로 처리한다. U2 create용 `CredentialRefreshPortV1`은 별도 계약이며 U2가 durable하게 소비한 authenticated reservation만 받는다. | application policy boundary → 목적별 narrow identity refresh ports | budget·reservation 검증 또는 deadline이 실패하면 추가 refresh/HTTP 호출 없이 safe failure를 반환한다. |
| SEC-U1-04 | `ItsmGateway` 공개 호출 한 번은 HTTP 시도 정확히 한 번이며 raw body, header, exception을 typed transport outcome으로 축소한다. | ITSM trust boundary | malformed·unknown 응답은 부분 성공 없이 `upstream_unavailable`로 닫는다. |
| SEC-U1-05 | 외부 데이터는 allowlist V1 projection으로만 들어오고 모든 ITSM 문자열은 `itsm_untrusted`로 유지한다. | response adapter, tool result, presentation mapper | 알 수 없는 field·enum·shape는 무시하거나 전체 결과를 안전 실패시키며 추측하지 않는다. |
| SEC-U1-06 | cursor reference는 운영체제 CSPRNG의 최소 128-bit entropy를 사용하고 exact actor·conversation·canonical query binding으로 한 번만 해석한다. | `TicketCursorRepositoryV1` | mismatch, replay, tamper, expiry는 outbound 호출 없이 새 검색을 요구한다. |
| SEC-U1-07 | pending mutation은 15분 expiry와 exact actor·payload·target·version binding을 적용한다. create는 같은 scope의 이전 pending/confirmed create를 원자 교체할 수 있지만, update prepare/revise는 미만료 `confirmed` update가 있으면 새 row publication을 거부한다. `confirm`은 `pending → confirmed`, 별도 `consume_once`는 binding을 다시 검사해 `confirmed → consumed`를 각각 원자적 CAS로 수행한다. consume은 정확히 `{mutation_id, confirmed_at}`만 가진 일회성 `ConsumedMutationEvidenceV1`을 반환하며 transport 권한을 부여하지 않는다. | `PendingMutationRepositoryV1`의 operation별 publication constraint와 분리된 confirmation/consumption ports | confirmed update는 exact consume 재개·expiry·lifecycle invalidation 전까지 경쟁 pending을 만들 수 없다. binding mismatch·repeat consume은 evidence와 mutation transport 없이 실패하고, U1 cleanup은 U2 `ticket_tools_create_v1` ledger를 변경하지 않는다. |
| SEC-U1-08 | presentation metadata는 persisted assistant message의 conversation·sequence·text hash를 같은 lock 아래 검증한 뒤 commit/readback이 성공할 때만 노출한다. | `PresentationHistoryRepositoryV1` | correlation 또는 persistence 실패 시 기존 assistant text만 반환한다. |
| SEC-U1-09 | model/API/log/storage/test output은 allowlist serializer와 중앙 redaction 규칙을 통과하며 비밀 canary 검증을 수행한다. | 모든 관찰 경계 | redaction이 불확실하면 원문 대신 고정 safe message와 opaque request ID만 남긴다. |
| SEC-U1-10 | 기존 chat endpoint, cookie/session, CSRF·same-origin 및 browser 보안 동작을 변경하지 않고 선택적 presentation만 하위 호환으로 추가한다. | 기존 FastAPI/browser boundary | metadata가 없거나 알 수 없으면 기존 reply/history 렌더링으로 fallback한다. |
| SEC-U1-11 | ordinary `ticket_read` detail과 U3의 server-internal `read_for_update`를 목적별 typed profile로 분리한다. ordinary detail은 유효한 public projection만으로 성공할 수 있지만 update evidence를 만들지 않는다. `read_for_update`는 strong quoted-decimal ETag와 public version의 정확한 일치가 필수다. | `TicketOperations.read_for_update` → `Result[ReadForUpdateResultV1, SafeErrorV1]` | ETag가 missing·weak·non-decimal·mismatched이면 정확히 `SafeErrorV1(upstream_unavailable)`로 실패하고 `ReadForUpdateResultV1`, review, PATCH를 만들지 않는다. |
| SEC-U1-12 | 논리 `ServerSession` 만료 view는 기존 물리 session schema의 대체 정의가 아니다. 현재 repository의 모든 인증·사용자·권한·위임 credential column과 의미를 snapshot contract로 고정하고 `session_expires_at`만 additive하게 migration한다. | existing Server Session SQLite migration과 session restore adapter | 기존 column 누락·rename·type/optionality 변화 또는 backfill 실패 시 migration을 중단하고 보호 요청을 fail closed한다. |
| SEC-U1-13 | 보호 chat, user switch, logout, conversation clear, session expiry는 모두 동일한 per-conversation application lock provider를 사용한다. 각 lifecycle event는 lock 직후 expected user/session/conversation을 재검증하고, presentation-before-history cleanup, revocable-state cleanup, terminal lifecycle commit까지 lock을 유지한다. 보호 chat은 Runner 전·직후 persisted session을 재검증하며 stale/expired Runner 결과를 correlation·fallback·publication 전에 폐기한다. | `ApplicationLifecycle`이 소유한 shared conversation lock → Runner/history/presentation과 네 lifecycle event 전체 | actor mismatch는 새 scope를 건드리지 않고 old-scope 결과를 폐기한다. cleanup commit 뒤 old-scope SDK message/presentation 재생성은 0건이며, 경쟁 요청은 terminal state를 idempotent하게 처리한다. |
| SEC-U1-14 | U2 create refresh는 U2가 `ticket_tools_create_v1`에서 one-invocation claim을 durable하게 소비한 `CredentialRefreshReservationV1`만 허용한다. U1은 server secret 기반 verifier로 opaque envelope의 authenticity와 create-attempt·user·session·conversation binding을 검증한 뒤 exchange 최대 1회와 기존 `ServerSession.itsm_token` 원자 교체를 수행한다. | U2 durable claim → authenticated reservation verifier → IdentitySession atomic rotation | tamper·binding mismatch·replay·deadline 실패는 exchange 0건이다. pre-commit crash는 reservation을 소비된 채로 끝내고 post-commit crash는 저장된 credential을 복원하며 둘 다 second exchange를 금지한다. |

## Trust Zones and Data Flow

| Zone | 신뢰 수준 | 허용 데이터 | 금지 데이터 또는 권한 |
|---|---|---|---|
| Browser and user text | 비신뢰 | 자연어 요청, allowlisted tool argument 후보 | user ID·role·permission·credential을 주장해 권한을 얻는 행위 |
| Existing FastAPI session boundary | 신뢰 원천 | opaque session ID로 복원한 current user, lifecycle event | model text로 session binding 변경 |
| Runner and function-tool boundary | 제한 신뢰 | strict V1 schema, request-scoped capability reference, safe result | credential 값, raw cursor, raw upstream response, 권한 판정 |
| TicketOperations | 정책 신뢰 | canonical query, attempt/deadline budget, typed repositories | raw HTTP access, 독립 gateway retry, 외부 문자열 기반 control flow |
| ItsmGateway adapter | 외부 경계 | delegated Authorization, allowlisted path/query/body, configured timeout | credential의 상위 반환, raw error/header 전파, 내부 retry |
| ITSM API v2 | 외부 비신뢰 데이터·권한 원천 | 계약에 맞는 response와 권한 판정 | 응답 텍스트가 application instruction이 되는 것 |
| Protected ServerSession SQLite | 신뢰 원천 persistence | 기존 인증·사용자·권한 field, 유일하게 허용된 `ServerSession.itsm_token`, additive `session_expires_at` | IdentitySession 이외의 credential 복원·교체, raw exchange response, 기존 field 재해석 |
| Other SQLite namespaces | 서버 내부 최소 persistence | revocable bindings, canonical safe JSON, message correlation, U2/U3 operation state | credential, Authorization, raw problem detail, raw tool trace |
| Browser presentation | 최종 비신뢰 목적지 | validated kind/block, server labels, escaped text values | `innerHTML` 기반 외부 문자열 실행, payload가 ARIA/DOM 의미 결정 |

### Request Flow

1. `ApplicationLifecycle`이 opaque session ID에서 conversation scope만 복원하고 동일한 per-conversation lock provider를 통해 lock을 얻는다. 이 시점까지 capability를 만들거나 SDK history를 읽고 쓰지 않는다.
2. lock을 얻은 직후 persisted session과 `session_expires_at`을 다시 읽는다. missing, malformed 또는 `now >= session_expires_at`이면 capability, Runner, ITSM 없이 SEC-U1-13 cleanup을 수행한다.
3. 유효한 session에서만 현재 user/session/conversation과 기존 위임 credential field에 고정된 capability를 만들고, Runner context에 server-derived current-turn evidence를 제공한다. credential 값은 직렬화하지 않는다. LC-U1-01은 opaque lock-held context를 하위 component에 전달하며 하위 component는 lifecycle coordinator를 역호출하지 않는다.
4. `ticket_read` input은 strict V1 validation과 mode exclusivity를 통과한 뒤 canonical query 또는 opaque ticket ID로 변환된다.
5. `TicketOperations`가 단일 read budget을 만들고 capability의 server-only credential usability를 검사한다. expired/imminently-expiring이면 같은 one-shot budget의 `ReadCredentialRefreshPortV1`을 먼저 호출하며 실패 시 ticket HTTP call 0건으로 닫는다. usable 또는 refreshed capability만 `ItsmGateway`의 one-attempt operation에 전달한다. 첫 call의 typed 401은 동일 budget이 남을 때만 한 번 갱신할 수 있다.
6. Runner가 완료되면 같은 lock을 유지한 채 persisted session과 expiry를 즉시 다시 읽는다. 이 검사는 correlation, reply mapping, presentation commit, text fallback과 HTTP 응답 결정에 선행한다.
7. 두 번째 검사에서 missing/expired이면 모든 Runner 결과를 폐기하고 presentation companion → SDK message/session history → pending/cursor → server session을 같은 lock 안에서 정리한 뒤 `authentication_required`만 결정한다.
8. 두 번째 검사도 유효할 때만 safe projection과 persisted assistant message correlation을 사용해 optional presentation을 commit/readback하고 기존 reply 또는 reply+presentation 응답을 결정한다.

## Authentication and Authorization Architecture

### Identity source

- current user, session ID, conversation ID는 서버 session에서만 복원한다.
- 동일 이름의 model input, tool argument, ITSM title·description은 authority가 없다.
- session 만료, inactive user, refresh 실패에서는 capability를 발급하지 않는다.
- user switch는 새 identity를 준비만 한 뒤 이전 revocable state와 history를 정리하고 마지막에 새 session을 commit한다.

### Delegated credential confinement

- ticket list/detail 호출의 token kind는 항상 delegated user다. service token은 directory/catalog 이외의 ticket endpoint에 사용할 수 없다.
- credential persistence는 기존 보호된 `ServerSession.itsm_token` 하나만 허용한다. IdentitySession만 이를 복원하거나 같은 row에서 원자 교체하며, capability는 gateway-only accessor를 제공한다. model schema, function-tool result, 다른 SQLite namespace, Pydantic dump와 logging context에는 credential field를 만들지 않는다.
- read flow는 capability의 server-only credential-usability metadata를 첫 ticket call 전에 검사한다. expired 또는 imminently-expiring이면 `TicketOperations`가 one-shot budget을 소비해 내부 `ReadCredentialRefreshPortV1`을 먼저 호출한다. 실패하면 ticket HTTP call 0건으로 닫고, 성공 handle만 첫 attempt에 사용한다. 첫 attempt의 typed 401도 같은 budget이 남을 때만 한 번 갱신한다.
- U2 create flow의 public `CredentialRefreshPortV1.refresh_delegated_capability_once(capability, reservation, remaining_deadline)`는 `CredentialRefreshReservationV1`을 필수로 받는다. U1 verifier는 server-authenticated opaque envelope의 authenticity와 capability/create-attempt actor binding을 검증하며 U2 table을 읽거나 쓰지 않는다. IdentitySession은 검증 성공 후 exchange를 최대 한 번 수행하고 `ServerSession.itsm_token`을 원자 교체한 다음 동일 actor-bound capability만 반환한다.
- U2의 durable claim이 restart replay를 선차단한다. mismatch·tamper·replay·pre-commit crash는 second exchange를 허용하지 않고, post-commit crash 뒤에는 저장된 credential을 복원해 재교환하지 않는다. raw credential과 token-exchange response는 어느 port에서도 반환하지 않는다.
- Authorization header는 outbound request 생성 직전 추가하고 typed outcome 생성 전에 폐기한다.

### Authorization decisions

- Assistant는 role이나 local permission으로 티켓 visibility를 확대하지 않는다.
- ITSM의 현재 delegated-user 결과만 사용한다. list 누락과 detail 404는 숨은 티켓 존재를 추론하지 않는다.
- detail 404는 absent와 invisible 모두 동일한 `failed/not_found` message key와 다음 행동을 사용한다.
- ordinary `ticket_read` detail은 visible public projection이 유효하면 ETag가 없거나 유효하지 않아도 read 결과 자체는 성공할 수 있지만 update precondition evidence를 만들지 않는다.
- U3에 공개되는 `read_for_update` profile은 C-01의 `detail_read_for_update_requires_ETag` invariant를 적용한다. strong quoted-decimal ETag와 public numeric version이 정확히 같을 때만 server-side evidence를 반환하며, missing·weak·non-decimal·mismatched ETag에서는 전체 read-for-update를 `upstream_unavailable`로 실패시켜 PATCH를 금지한다.
- 두 profile은 같은 public projection validator를 사용하되 성공 조건을 섞지 않는다. contract test는 ordinary-detail success-without-evidence와 read-for-update safe failure를 별도 fixture로 고정한다.

## Data Protection and Encryption

### In transit

- C-07의 ITSM endpoint는 HTTPS만 사용하고 httpx의 인증서 검증을 비활성화하지 않는다.
- redirect가 credential을 다른 origin으로 전달하지 않도록 ticket request는 계약에 고정된 origin/path만 사용한다.
- returned header allowlist는 ETag, X-Request-ID, Retry-After, Idempotent-Replayed, Location 중 해당 operation에 필요한 값으로 제한한다. U1 read는 ETag, X-Request-ID, Retry-After만 해석한다.

### At rest

- 기존 Server Session SQLite가 기존 credential storage를 계속 소유한다. U1의 새 namespace에는 credential을 복사하지 않는다.
- migration 전 기존 session table column 이름·type·nullability와 대표 row 복원 결과를 contract fixture로 고정한다. migration은 `session_expires_at`만 추가하며 기존 column을 drop·rename·recreate·reinterpret하지 않는다.
- 새 session은 동일 transaction에서 기존 field와 `created_at`, `session_expires_at = created_at + 8시간`을 저장한다. legacy row는 parse 가능한 기존 `created_at + 8시간`으로 backfill하고, missing·malformed `created_at`은 이미 만료된 값으로 backfill한다.
- `ticket_tools_state_v1`에는 pending binding과 cursor binding만 저장한다. upstream cursor는 server-only이며 model/API/log에 노출하지 않는다.
- `ticket_tools_history_v1`에는 canonical validated presentation JSON과 message correlation만 저장한다. raw tool trace나 upstream body는 저장하지 않는다.
- 새 at-rest encryption infrastructure를 도입하지 않는다. 데이터베이스 파일 권한·backup protection은 기존 배포 통제를 상속하며, U1은 민감 원문 최소화와 lifecycle deletion으로 노출 범위를 줄인다.

### Data minimization and retention

| Record | 최소 저장 내용 | 삭제 또는 무효화 경계 |
|---|---|---|
| Cursor binding | opaque ref, actor binding, canonical query material/hash, upstream cursor, timestamps | resolve-once, expiry, invalid cursor, session expiry, switch, logout, conversation clear |
| Pending mutation | operation, actor binding, payload hash, target/version, state, expiry | one-time consume, cancel, 15분, replacement, binding/lifecycle change; U1 row만 정리하고 U2 durable create ledger는 보존 |
| Presentation companion | message correlation, V1 canonical presentation JSON, creation time | matching history lifetime, switch, logout, conversation clear; history load와 application startup에서 orphan을 판정해 idempotent delete |

## Input Validation and Untrusted Data Handling

- Pydantic V1 boundary models는 `additional_properties: false` 의미로 unknown field를 거부한다.
- `ticket_read`는 first-page list, continuation, detail 세 mode를 상호 배타적으로 검증한다.
- limit은 생략 시 20, 허용 범위 1–100이며 범위 밖 입력은 outbound 호출 전에 거부한다.
- canonical query는 고정 field 순서, UTC timestamp, materialized default, UTF-8 JSON과 SHA-256 hash로 만든다.
- continuation은 저장한 exact canonical JSON을 재구성하며 호출자가 filter, sort, limit 또는 raw cursor를 바꿀 수 없다.
- 외부 enum과 text는 업무 data다. 외부 text는 tool selection, identity, confirmation, registry key, message kind, block type, ARIA/live semantics를 선택할 수 없다.
- browser는 외부 text를 `textContent`와 동등한 text-node 경로로 삽입한다. server allowlist만 label, action, presentation kind와 block type을 결정한다.

## Secret and Error Containment

`SafeErrorV1`은 정확히 `version`, allowlisted `code`, server-owned `message_key`, `retryable`, optional request ID, validated retry seconds와 allowlisted field errors만 허용한다. raw detail, exception, header, Authorization, token, secret, API key는 금지한다.

| 관찰 경계 | 허용 | 차단 방법 | 검증 |
|---|---|---|---|
| Model input/tool schema | safe business fields와 opaque non-authority refs | capability와 credential field 자체를 schema에서 제외 | schema snapshot과 secret canary |
| Tool result/API response | safe projection, SafeErrorV1, optional presentation | exact V1 serializer와 unknown-field rejection | malicious body/header fixture |
| Application log | operation kind, safe code, opaque request ID, attempt count | raw exception/body/header 미기록, redaction filter | captured logs canary scan |
| Persistence | 최소 binding/correlation/canonical safe JSON | repository model allowlist | SQLite row inspection |
| Test failure output | safe assertion context만 | secret-bearing object repr 금지, isolated intentional failure scan | stdout·stderr·traceback·assertion diff canary 0건 |

## Continuation and Confirmation Security

### Continuation

- reference 생성기는 OS CSPRNG를 사용하며 최소 128-bit entropy를 제공한다.
- reference는 비밀이나 권한 증명이 아니다. user, session, conversation, serialization version, canonical query hash를 모두 맞춰야 한다.
- `issue`는 canonical material의 hash를 다시 계산하고 mismatch를 거부한다.
- `resolve_once`는 저장 row의 hash를 다시 계산하고 exact query를 재구성한 뒤 원자적으로 소비한다.
- 100,000개 collision sample, sequential/timestamp-only rejection, random guess와 cross-actor matrix로 구현 seam을 검증한다.

### Pending confirmation

- U1 repository는 create/update variant를 strict discriminator로 보존하지만 mutation transport를 호출하지 않는다.
- create publication은 같은 actor scope의 이전 pending/confirmed create를 한 transaction에서 `invalidated`로 바꾸고 새 pending을 넣을 수 있다.
- update prepare/revise는 같은 actor scope에 미만료 `confirmed` update가 있으면 transaction 안에서 새 publication을 거부한다. 허용 경로는 exact binding의 `consume_once` 재개, expiry 또는 lifecycle invalidation뿐이며 그 전까지 새 pending row와 PATCH 호출은 0건이다.
- update pending 교체는 exact expected-old pending row만 invalidate하고 새 pending을 같은 transaction에 넣는다. broad selector replacement와 confirmed-row replacement는 금지한다.
- current raw user turn에서 server가 만든 `CurrentTurnEvidenceV1`만 confirm/cancel authority를 가진다.
- `confirm(binding, current_turn_evidence)`는 exact user/session/conversation/operation/payload/target/version binding과 미만료 상태를 transaction 안에서 확인하고 유효한 `pending` row 하나만 `confirmed`로 CAS한다. 반환값에는 credential, idempotency key, canonical bytes 또는 HTTP 실행 권한이 없다.
- `consume_once(binding)`는 별도 transaction에서 같은 binding과 `confirmed` 상태를 다시 확인하고 row 하나만 `consumed`로 CAS한다. 성공 시 정확히 `ConsumedMutationEvidenceV1 { mutation_id, confirmed_at }`만 한 번 반환하며, 재시도·동시 호출·만료·불일치에는 evidence를 반환하지 않는다.
- U2와 U3는 이 evidence를 각 Unit의 operation state에 별도로 결합하고 자체 실행 전제조건을 충족해야 한다. U2는 durable ledger evidence binding과 별도 CAS claim이 있어야 POST할 수 있고, U3는 target·patch·version·`If-Match` 조건이 있어야 PATCH할 수 있다.
- U1 consume 뒤 U2 evidence binding 전에 process가 중단되면 consumed row에서 evidence를 재발급하지 않는다. U2의 동일 attempt, idempotency key와 canonical request bytes를 그대로 보존하고 새 pending review를 발행해 새로운 명시적 confirmation을 요구한다. bind되지 않은 evidence로 POST하지 않는다.

## Presentation and Browser Security

- 기존 `reply`, `role`, `text`는 필수 fallback으로 남는다. `presentation`은 선택적이다.
- mapper는 typed tool result만 소비하며 raw tool trace나 gateway outcome에 접근하지 않는다.
- 동일한 conversation lock을 Runner 시작 전 persisted-expiry 검사부터 Runner, SDK history 접근, post-Runner persisted-expiry 검사, persisted assistant item correlation, presentation commit/readback과 최종 응답 결정까지 유지한다. session-expiry cleanup도 반드시 이 lock을 사용하며 lock 밖에서 SDK history를 삭제하지 않는다.
- post-Runner expiry 검사는 correlation, mapper, presentation commit, text fallback보다 앞선다. 만료 branch에서는 생성된 reply를 포함한 Runner 결과를 폐기하므로 기존 text fallback 규칙을 적용하지 않고 `authentication_required`만 반환한다.
- history load는 conversation, sequence, text hash를 모두 맞춘 row만 붙인다. matching SDK assistant item이 없는 orphan row는 같은 repository operation에서 응답 대상에서 제외하고 idempotent delete를 시도한다.
- application startup cleanup은 모든 companion row를 matching SDK history key와 대조해 orphan을 idempotent하게 삭제한다. cleanup transaction 실패는 startup이나 history text를 실패시키지 않고 text-only fallback을 유지하며 다음 startup/history load에서 다시 시도한다.
- restored history는 `announce=false`이며 현재 응답만 기존 live announcement 규칙을 사용한다.
- 새 inline HTML 또는 script를 생성하지 않으며 기존 CSP, cookie, CSRF/same-origin 정책을 약화하지 않는다. 새 HTTP endpoint도 만들지 않는다.

## Reliability and Safe Degradation Controls

| 실패 | 격리 경계 | 자동 동작 | 사용자에게 보이는 결과 |
|---|---|---|---|
| Session/capability 실패 | ApplicationLifecycle | Runner·ITSM 호출 0회 | 재로그인 안내 |
| Timeout/transport/500/502/503/504 | TicketOperations | 첫 실패에만 250ms 뒤 한 번 재시도, 전체 deadline 안 | 소진 시 retry-later safe error |
| 401 expired credential | TicketOperations + IdentitySession | refresh budget이 남으면 한 번 갱신 후 남은 attempt/deadline 사용 | 실패 시 재로그인 안내 |
| U2 create refresh reservation 오류 | U2 durable ledger + U1 reservation verifier | tamper·binding mismatch·replay를 exchange 전에 거부; 내부 retry 0회 | create attempt를 fail closed하고 second exchange 금지 |
| 429 | TicketOperations | sleep 0회, retry 0회 | 검증된 Retry-After가 있으면 안전 안내 |
| Malformed success | ItsmGateway adapter | partial projection 금지 | upstream unavailable |
| Cursor store/resolve 실패 | CursorRepository | 권한 또는 cursor 추측 금지 | 새 검색 안내 |
| Pending confirm/consume 실패 | PendingRepository | CAS rollback, evidence 0건, mutation 실행 금지 | 안전 실패 또는 새 review 요구 |
| Presentation store/readback 실패 | PresentationHistoryRepository | 기존 text 보존 | text-only 응답 |
| Cleanup 일부 실패 | ApplicationLifecycle | idempotent 재실행, 새 context 활성화 금지 | lifecycle safe error |
| Runner 도중 session 만료 | ApplicationLifecycle + shared conversation lock | Runner 직후 persisted expiry 재검사, 결과 폐기, lock 안 terminal cleanup | 성공 reply/presentation 없이 `authentication_required` |
| 경쟁 expiry 요청 | ApplicationLifecycle + shared conversation lock | Runner/선행 cleanup 종료까지 대기하고 이미 비어 있는 terminal state를 idempotent success로 처리 | history/metadata 재생성 없이 동일 authentication failure |
| user switch/logout/conversation clear와 Runner 경쟁 | ApplicationLifecycle + shared conversation lock | event가 lock 뒤 expected actor를 재검증하고 presentation→history→revocable state→terminal commit 순서를 완료 | old-scope 결과 폐기, commit 후 message/metadata 재생성 0건 |
| confirmed update 뒤 prepare/revise | ConfirmationRepository | transaction 안 publication 거부, exact consume/expiry/lifecycle만 허용 | 새 pending과 PATCH 0건; 기존 confirmed authority 유지 |
| Session schema migration 불일치 | existing session repository | transaction rollback, application 보호 경계 fail closed | 기존 field를 잃거나 새 lifetime을 부여하지 않고 운영자 조치 필요 |

Read operation의 사용자 관찰 자동 정책 경과시간은 credential refresh를 포함해 `2 × ITSM_TIMEOUT_SECONDS + 0.25초` 이하다. 모든 outbound attempt는 남은 monotonic deadline으로 timeout을 줄인다. U1은 shared failure memory가 다른 사용자의 호출을 차단할 수 있는 circuit breaker를 추가하지 않고, authoritative 티켓 data cache도 추가하지 않는다.

## Threat-to-Control Matrix

| 위협 | 예방 통제 | 탐지·검증 | 잔여 영향 범위 |
|---|---|---|---|
| Model 또는 ITSM text의 신원 위조 | SEC-U1-01, SEC-U1-05 | forged identity와 injection fixture | 단일 요청 safe failure |
| Credential 유출 | SEC-U1-02, SEC-U1-04, SEC-U1-09 | 모든 관찰 경계 secret canary 0건 | 해당 요청 중단; 값 미기록 |
| Refresh reservation 위조·restart replay | SEC-U1-14 | actor/create-attempt mismatch, tamper, restart, pre/post-commit crash fixture | 해당 create attempt fail closed; exchange 최대 1회 |
| Hidden ticket enumeration | ITSM authority, uniform 404 | absent/invisible semantic equivalence | 현재 사용자의 detail 요청 하나 |
| Cursor 탈취·변조·재사용 | SEC-U1-06 | guess/cross-actor/tamper/replay matrix | 해당 continuation 하나 무효화 |
| Confirmation replay | SEC-U1-07 | expiry/replacement/lifecycle/binding matrix | 해당 operation의 pending row 하나 |
| Consume 후 U2 bind 전 crash | SEC-U1-07 + downstream ownership boundary | fault injection으로 동일 ledger attempt/key/bytes 보존, 새 review·재확인, unbound POST 0건 확인 | 해당 create attempt는 보존되고 재확인까지 실행 중지 |
| Retry amplification | SEC-U1-03, SEC-U1-04 | operation request counter ≤2 | 해당 read operation만 실패 |
| History metadata misbinding | SEC-U1-08 | concurrent completion, hash mismatch, restart fixture | presentation만 제거; text 유지 |
| Expiry cleanup과 Runner history write 경쟁 | SEC-U1-13 | deterministic barrier로 Runner write 중 expiry 요청을 시작해 lock 대기, post-Runner 검사 선행, terminal zero rows와 publication 0건을 확인 | 한 conversation의 in-flight 결과 폐기와 재로그인 |
| switch/logout/clear와 Runner history write 경쟁 | SEC-U1-13 | event별 deterministic barrier, post-lock actor 재검증, terminal commit 후 old-scope row/publication 0건 | old scope 한 conversation만 폐기; 새 scope 보존 |
| confirmed update authority 덮어쓰기 | SEC-U1-07 | confirm 직후 crash와 동시 prepare/revise fixture | expiry·lifecycle·exact consume 전 경쟁 pending/PATCH 0건 |
| Stored/reflected markup | SEC-U1-05, SEC-U1-10 | markup payload DOM snapshot | 해당 text는 inert data |
| Test diagnostics leakage | SEC-U1-09 | isolated failing-test output scan | CI job 실패; 비밀 출력 0건 목표 |
| Session expiry bypass 또는 schema 축소 | SEC-U1-12, pre-capability expiry check | legacy snapshot, exact-boundary, restart, refresh, switch regression | 만료 session과 해당 revocable state만 정리; downstream 호출 0건 |

## Verification Design

| Control group | Test doubles and evidence | Pass condition |
|---|---|---|
| Identity and credential | fake server sessions, token-kind marker, MockTransport | delegated ticket calls 100%, service-token ticket calls 0건 |
| Secret containment | distinct canary per credential class and boundary | schema/result/API/row/log/failure-output 발견 0건 |
| Safe errors | malicious body, header and exception fixtures | exact SafeErrorV1 validation, raw detail 0건 |
| Injection safety | instruction-shaped ticket text and markup | identity, confirmation, registry, outbound request 변화 0건 |
| Cursor security | deterministic entropy seam plus real OS source contract | ≥128-bit CSPRNG, 100,000 collision 0건, binding bypass 0건 |
| Attempt/deadline policy | fake monotonic clock and sleeper | HTTP attempts ≤2, elapsed ≤ formula, 429 sleep/retry 0회 |
| Read credential refresh seam | fake `ReadCredentialRefreshPortV1`, pre-call unusable capability와 typed 401, capability-handle probes | pre-call failure의 ticket call 0건, 두 trigger가 같은 one-shot budget을 공유, refresh≤1, 성공 handle만 남은 attempt에 사용, credential 직렬화 0건 |
| U2 create refresh reservation | fake U2 durable one-invocation claim, authenticated-envelope verifier, exchange/commit crash probes | mismatch·tamper·restart replay의 exchange 0건, accepted reservation의 exchange≤1, 성공 전 `ServerSession.itsm_token` atomic commit, crash 뒤 second exchange 0건 |
| Presentation correlation and retention | concurrent Runner completions, lock-acquisition probe, missing SDK message, startup/history-load cleanup and SQLite failure injection | 두 Runner가 실행 전에 같은 conversation lock을 획득해 SDK persistence까지 직렬화됨, mismatched metadata 노출 0건, orphan row 삭제, cleanup 실패 시 text fallback 100%와 다음 실행 재시도 |
| Session migration and expiry | legacy row snapshots, fake UTC clock, restart and token-refresh fixtures | 기존 field/value·복원 의미 100% 보존, exact/after expiry downstream 호출 0건, restart/refresh deadline 연장 0건 |
| Runner/lifecycle serialization | user switch·logout·conversation clear·session expiry 각각의 controllable Runner-write barrier, fake UTC clock, direct row-count inspection | 네 event 모두 같은 lock에서 대기하고 post-lock expected actor를 재검증하며 presentation-before-history cleanup과 terminal commit 뒤 old-scope SDK message/presentation 재생성 0건; expiry success publication 0건 |
| Read for update | valid/missing/weak/non-decimal/mismatched ETag matrix | valid case만 `ReadForUpdateResultV1`; 나머지는 `SafeErrorV1(upstream_unavailable)`이며 review/PATCH 0건 |
| Confirmation consumption and ledger isolation | concurrent repository CAS, repeat/expiry/binding matrix, confirm 직후 crash와 concurrent update prepare/revise, U2 fake durable ledger, crash-before-bind injection | `confirm`과 `consume_once`가 별도 전이이고 성공 consume 최대 1회, 미만료 confirmed update에서 새 pending/PATCH 0건, evidence field가 정확히 두 개, lifecycle cleanup 전후 U2 ledger key/bytes 불변, unbound POST/PATCH 0건 |
| Regression and coverage | FakeModel, MockTransport, coverage 7.17.0 | external calls 0건, baseline 통과, changed app code line coverage ≥80% |

## NFR Allocation

| NFR | Primary design controls |
|---|---|
| NFR1.1–NFR1.4 | SEC-U1-02, SEC-U1-04, SEC-U1-05, SEC-U1-09 |
| NFR2.1–NFR2.5 | SEC-U1-01, SEC-U1-12, delegated credential confinement, persisted pre-capability expiry, uniform authorization outcomes |
| NFR2.6 | SEC-U1-13 shared conversation lock, 네 lifecycle event의 post-lock actor 재검증·presentation-before-history cleanup·terminal commit, pre/post-Runner expiry fence와 stale-result discard |
| NFR2.7 | SEC-U1-14 U2 durable one-invocation reservation, authenticated envelope verification, exact actor/create-attempt binding, atomic ServerSession credential rotation and crash/replay closure |
| NFR3.1 | SEC-U1-11 purpose-specific ordinary-detail/read-for-update profiles, exact typed result union, validated strong ETag/version server-only evidence |
| NFR3.2 | SEC-U1-07 separate confirmation/consumption CAS ports, one-time minimal non-authoritative evidence, downstream operation binding, U2 durable-ledger preservation and crash-before-bind recovery |
| NFR4.1–NFR4.2 | strict pagination validation, SEC-U1-06 |
| NFR5.1–NFR5.2 | existing-process embedding, SEC-U1-10 compatibility boundary, SEC-U1-12 additive migration contract |
| NFR6.1 | deterministic test harness and changed-code coverage gate |
| NFR7.1–NFR7.4 | SEC-U1-03, SEC-U1-04 and monotonic shared deadline |
| NFR9.1–NFR9.2 | SEC-U1-08, text-first presentation and accessible fallback |

## Residual Risks and Deferred Ownership

- 기존 SQLite 파일 자체의 at-rest encryption, backup, host access control은 현재 배포의 운영 통제에 의존한다. U1은 새 비밀을 저장하지 않고 최소 데이터만 보존한다.
- 단일-process conversation lock은 현재 배포 경계에서만 상관 원자성을 보장한다. 다중 process 배포가 실제로 도입되면 shared lock 또는 transaction design이 별도 결정으로 필요하다.
- U2는 U1과 분리된 `ticket_tools_create_v1` namespace에서 create idempotency ledger와 최대 한 번 생성 보장을 완결한다. U1 lifecycle cleanup은 이 ledger를 변경하지 않는다.
- U3는 PATCH `If-Match`, conflict와 ambiguous-result 처리를 완결한다.
- U4는 정확히 세 tool 조립, 전체 suite·coverage, README와 최종 lifecycle 회귀를 검증한다.

## Outcome

U1은 서버 session과 ITSM 권한 원천을 그대로 유지하면서 capability confinement, exact typed projection, server-bound state, one-owner recovery policy와 text-first fallback으로 위험을 격리한다. 실패는 권한 확대나 성공 추측으로 이어지지 않고 해당 요청·continuation·presentation 범위에서 안전하게 닫힌다.
