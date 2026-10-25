# U2 Ticket Write — 비즈니스 규칙

## Sources

- `inception/units-generation/unit-of-work.md` — U2 책임·소유권·검증 경계
- `inception/units-generation/unit-of-work-story-map.md` — U2 acceptance criteria
- `inception/user-stories/stories.md` — US2.1 및 공유 US4.1·US5.1 동작
- `inception/requirements-analysis/requirements.md` — FR3, FR5, FR6.3 및 관련 NFR
- `inception/domain-design/components.md` — `TicketOperations`, `ItsmGateway`, session, registry, presentation 경계
- `inception/contract-design/contract-summary.md` — C-01, C-03A, C-04, C-06, C-07 V1 계약
- `construction/u2-ticket-write/functional-design/functional-design-questions.md` — 확인된 ledger-first/public-port-only 방향

## Authoritative Rule Set

아래 YAML block이 business-rule source of truth다. 모든 규칙은 live network 없이 결정적으로 검증할 수 있다.

```yaml
schema_version: 1
unit: u2-ticket-write
rules:
  - id: BR2.1
    statement: Create draft는 문서화된 ticket-create field와 constraint만 허용한다.
    category: validation
    applies_to: [TicketWriteDraftV1, prepare, revise]
    trigger: Create draft가 제출된다.
    logic: IF supplied key가 모두 allowlist에 있고 required string, length, enum이 유효하다 THEN 진행하고 ELSE outbound access 전에 거부한다.
    violation_behaviour: Safe field error와 수정 가능한 draft를 반환하고 POST를 0회 수행한다.
    source: [FR3.1, FR3.2, NFR1]

  - id: BR2.2
    statement: Service, component, model selector는 정확히 하나의 active catalog match로 해석되고 component는 service에 속해야 한다.
    category: validation
    applies_to: [catalog_resolution, NormalizedTicketCreateV1]
    trigger: Catalog selector를 normalize한다.
    logic: IF 각 selector가 유일한 active normalized match이고 component-service 관계가 유효하다 THEN server-resolved identity를 사용하고 ELSE 추측 없이 거부한다.
    violation_behaviour: 해당 field의 invalid_input을 반환하고 POST를 0회 수행한다.
    source: [FR3.2, FR3.3, NFR1]

  - id: BR2.3
    statement: occurred_at은 timezone-qualified timestamp 또는 한 번만 UTC로 고정한 explicit now여야 한다.
    category: validation
    applies_to: [TicketWriteDraftV1, NormalizedTicketCreateV1]
    trigger: prepare 또는 revise에서 occurred_at을 normalize한다.
    logic: IF offset 또는 Z timestamp가 유효하다 THEN UTC RFC3339로 canonicalize하고 ELSE IF explicit now이면 server time을 한 번 capture하며 ELSE 거부한다.
    violation_behaviour: Client timezone을 추측하거나 confirm/replay에서 now를 다시 capture하지 않는다.
    source: [FR3.2, NFR2]

  - id: BR2.4
    statement: Normalization과 serialization은 하나의 deterministic body, canonical byte sequence, SHA-256 hash를 만든다.
    category: constraint
    applies_to: [NormalizedTicketCreateV1, CanonicalRequestBytesV1]
    trigger: 유효한 draft를 prepare 또는 revise한다.
    logic: standard classification default를 materialize하고 absent optional을 생략한 뒤 version 1 field order와 compact UTF-8 JSON으로 한 번 encode하고 hash한다.
    violation_behaviour: Deterministic bytes 또는 hash를 만들 수 없으면 confirmation 전에 중단한다.
    source: [FR3.2, FR6.3, NFR2]

  - id: BR2.5
    statement: Invalid input은 raw upstream detail 없이 안전한 사용자 입력을 수정용으로 보존한다.
    category: policy
    applies_to: [validation_result, presentation]
    trigger: Draft 또는 catalog validation이 실패한다.
    logic: Server-owned field message와 수정에 필요한 safe draft field만 반환한다.
    violation_behaviour: 안전하게 echo할 수 없는 값은 generic invalid-input presentation으로 대체한다.
    source: [FR3.2, FR6.1, FR6.2, NFR1]

  - id: BR3.1
    statement: Prepare와 revise는 U1 pending review 공개 전에 U2 durable ledger에 authoritative reviewed bytes와 한 idempotency key를 prepared로 저장하며 POST를 수행하지 않는다.
    category: policy
    applies_to: [prepare, revise, TicketCreateAttemptV1, SafeMutationReviewV1]
    trigger: Draft validation과 normalization이 끝난다.
    logic: 독립 create_attempt_id로 exact canonical bytes, hashes, actor bindings, one key, attempt_count 0, prepared status를 ticket_create_attempts에 commit한 뒤 같은 actor scope와 payload hash의 U1 pending row를 put하고 complete review를 반환한다.
    violation_behaviour: Ledger commit 또는 U1 pending publish가 실패하면 executable confirmation을 공개하지 않고 POST를 0회 수행한다.
    source: [FR3.3, FR3.4, FR3.5, FR6.3, NFR1]

  - id: BR3.2
    statement: 같은 actor scope의 새 create review는 이전 ledger 실행 권한 제거와 이전 pending 무효화를 모두 완료한 뒤에만 공개된다.
    category: constraint
    applies_to: [PendingCreateMutationV1, TicketCreateAttemptV1]
    trigger: 새 valid create review를 저장한다.
    logic: 이전 row가 evidence 없는 prepared인지 expected-state CAS로 확인해 terminal_failure로 닫고, U1 공개 repository로 이전 pending을 invalidate한 뒤에만 새 ledger를 prepared로 commit하고 새 pending을 put한다. Confirm이 먼저 evidence를 결합했거나 claim을 얻었다면 교체를 중단한다.
    violation_behaviour: 이전 실행 권한 제거나 invalidation이 확정되지 않으면 새 ledger·pending을 만들지 않는다. 새 pending 공개가 실패하면 새 row는 evidence 없는 orphan prepared로 남아 실행할 수 없고 fresh prepare를 안내한다.
    source: [FR3.3, FR3.4, NFR2]

  - id: BR3.3
    statement: Pending create confirmation은 최대 15분이며 exact user, session, conversation, operation, payload hash에만 유효하다.
    category: authorization
    applies_to: [PendingCreateMutationV1, lifecycle]
    trigger: Confirmation 또는 관련 lifecycle event를 처리한다.
    logic: IF current server time이 expiry 전이고 U1 pending과 U2 ledger binding이 모두 일치한다 THEN confirmation을 검토할 수 있다.
    violation_behaviour: Pending을 consume 또는 invalidate하고 미확인 ledger를 실행 불가능하게 닫으며 fresh review를 요구한다.
    source: [FR3.4, FR5.1, FR5.4, NFR1]

  - id: BR3.4
    statement: 현재 raw user turn이 허용된 normalization 뒤 확인 또는 confirm과 정확히 같을 때만 create execution을 승인한다.
    category: authorization
    applies_to: [confirmation_classifier, Runner]
    trigger: Create review가 pending인 동안 새 turn이 도착한다.
    logic: IF current turn이 exact allowed token이고 BR3.3이 통과한다 THEN U1 public confirmation flow로 진행하며 quoted, embedded, historical, model-generated, external text는 승인으로 인정하지 않는다.
    violation_behaviour: POST를 0회 수행하고 explicit intent에 따라 revise, cancel 또는 ordinary conversation으로 처리한다.
    source: [FR3.4, FR5.1, NFR1]

  - id: BR3.5
    statement: U2는 U1 공개 confirm과 consume_once 결과를 같은 prepared attempt에 idempotent하게 결합하며 cross-owner transaction을 만들지 않는다.
    category: constraint
    applies_to: [PendingCreateMutationV1, TicketCreateAttemptV1]
    trigger: Exact confirmation이 binding과 freshness check를 통과한다.
    logic: U1 public port로 same-binding pending을 confirm하고 consume_once한다. Actor binding과 payload hash로 유일한 prepared attempt를 찾고 returned mutation_id와 confirmed_at을 compare-and-set으로 한 번만 결합하며 retained_until을 confirmed_at_plus_24_hours 이상으로 늘린 뒤 claim을 시도한다.
    violation_behaviour: Consumption을 입증하지 못하거나 evidence 결합 전에 중단되면 같은 attempt·key·bytes로 새 review와 새 explicit confirmation을 요구하며 claim과 POST를 거부한다.
    source: [FR3.4, FR6.3, NFR2]

  - id: BR3.6
    statement: Cancel, mutation-bearing text, expiry, lifecycle invalidation은 ticket POST를 수행하지 않는다.
    category: authorization
    applies_to: [cancel, revise, lifecycle]
    trigger: 취소, field 변경 또는 binding lifecycle event가 발생한다.
    logic: U1 pending을 공개 invalidate 연산으로 닫고 대응 prepared ledger를 terminal_failure로 표시하며 safe next step을 반환한다.
    violation_behaviour: 실행을 fail closed하고 새 complete review를 요구한다.
    source: [FR3.4, FR5.4, NFR1]

  - id: BR4.1
    statement: Durable create ledger는 confirmation 공개와 첫 POST보다 먼저 존재한다.
    category: constraint
    applies_to: [TicketCreateAttemptV1, prepare, revise, create_execution]
    trigger: Review를 만들거나 valid confirmation 뒤 execution을 시작한다.
    logic: Review 공개 전 exact bytes와 key가 prepared로 commit되어야 하며, execution 전 same row의 U1 consumed evidence와 retained_until extension이 존재해야 한다.
    violation_behaviour: 필요한 durable evidence 중 하나라도 없으면 POST를 0회 수행한다.
    source: [FR3.5, FR6.3, NFR2]

  - id: BR4.2
    statement: 한 create attempt는 평생 하나의 unpredictable idempotency key와 byte-identical body만 사용한다.
    category: constraint
    applies_to: [TicketCreateAttemptV1, gateway_create]
    trigger: Initial, refreshed, restarted 또는 reconciliation POST를 검토한다.
    logic: Stored byte hash를 재계산해 일치할 때만 original key와 exact stored bytes를 보낸다.
    violation_behaviour: 불일치 시 전송 없이 terminal_failure로 닫는다.
    source: [FR6.3, NFR1, NFR2]

  - id: BR4.3
    statement: Confirmed create의 ticket POST는 refresh recall, restart, reconciliation을 합쳐 최대 두 번이다.
    category: constraint
    applies_to: [TicketCreateAttemptV1, create_execution]
    trigger: 추가 POST를 검토한다.
    logic: IF attempt_count가 2 미만이고 follow-up policy가 허용한다 THEN claim을 시도하며 ELSE 더 보내지 않는다.
    violation_behaviour: Ambiguous 또는 terminal outcome을 보존하고 성공을 주장하지 않는다.
    source: [FR5.3, FR6.2, FR6.3, NFR7]

  - id: BR4.4
    statement: 모든 POST는 U2 ledger CAS claim 승자가 confirmation evidence, claim identity·deadline, attempt_count와 in_flight를 먼저 durable commit한 뒤에만 수행한다.
    category: constraint
    applies_to: [TicketCreateAttemptV1, concurrency, process_restart]
    trigger: TicketOperations가 gateway call을 승인하려 한다.
    logic: Bound confirmation evidence가 있는 prepared, retryable_after_reconcile 또는 retryable_no_apply와 count below 2를 expected state로 사용해 compare-and-set으로 count를 증가시키고 unique claim_id, claim_deadline_at, in_flight를 commit한다. claim_deadline_at 이전에는 active claim을 탈취하지 않으며 모든 결과 write는 expected in_flight와 expected claim_id를 함께 비교한다.
    violation_behaviour: Claim 실패·패자는 gateway를 호출하지 않고 current durable state를 반환한다. Deadline이 지난 in_flight는 expected claim_id CAS의 단일 recovery owner가 결과를 조정하기 전까지 새 POST를 금지하고, 늦은 stale claimant 결과는 현재 상태를 바꾸지 않는다.
    source: [FR6.3, NFR2]

  - id: BR4.5
    statement: HTTP 429는 automatic sleep과 automatic retry를 모두 금지한다.
    category: policy
    applies_to: [create_execution, gateway_outcome]
    trigger: Ticket POST가 429를 반환한다.
    logic: rate_limited를 즉시 반환하고 유효한 non-negative Retry-After seconds만 선택적으로 포함한다.
    violation_behaviour: 해당 confirmation에서 추가 gateway call을 수행하지 않는다.
    source: [FR6.2, NFR7]

  - id: BR4.6
    statement: Idempotency key를 다른 request bytes와 함께 재사용할 수 없다.
    category: authorization
    applies_to: [TicketCreateAttemptV1, gateway_create]
    trigger: Stored state를 load하거나 follow-up send를 준비한다.
    logic: IF key, serialization version, bytes, hash binding이 모두 같다 THEN 진행하고 ELSE 중단한다.
    violation_behaviour: Conflicting body를 보내지 않고 terminal_failure로 닫는다.
    source: [FR6.3, NFR1, NFR2]

  - id: BR4.7
    statement: Create success는 ticket ID와 authoritative created 또는 Idempotent-Replayed evidence를 요구한다.
    category: policy
    applies_to: [CreateCompletionEvidenceV1, SafeMutationResultV1, TicketMutationToolResultV1, TicketCreateAttemptV1]
    trigger: Create response를 mapping한다.
    logic: IF valid created 또는 replayed response에 ticket ID가 있다 THEN completed로 저장하고 shared result shape를 반환하며 ELSE success가 아니다.
    violation_behaviour: Malformed success-like response는 ticket ID를 만들지 않고 upstream_unavailable 또는 ambiguous로 mapping한다.
    source: [FR3.5, FR6.2, FR6.3, NFR1]

  - id: BR4.8
    statement: 401 미적용 보장과 불명확 결과는 서로 다른 durable retry state로 기록되며 모든 재호출은 shared attempt cap을 사용한다.
    category: policy
    applies_to: [timeout, transport_failure, server_failure, process_restart]
    trigger: Token-expired 401 또는 sent request의 authoritative terminal response 부재를 처리한다.
    logic: IF 첫 POST 전 capability가 만료됐거나 만료 임박했거나 권위 계약이 401 미적용을 보장하면 U2 one-shot refresh reservation을 먼저 durable consume한 승자만 U1 CredentialRefreshPortV1을 정확히 한 번 호출하고 session credential generation 증가를 commit evidence로 기록한다. ELSE ambiguous를 기록하고 stale claim 또는 불명확 결과를 먼저 조정하며, 생성되지 않음이 확인되거나 조회 실패·불명확이고 count가 남을 때만 retryable_after_reconcile로 전이한다. 어느 retryable state든 same key·bytes의 새 CAS claim이 필요하다.
    violation_behaviour: Active claim을 탈취하거나 ambiguous에서 직접 POST하거나 새 key를 만들지 않는다. Refresh reservation을 reset·replace·replay하지 않고, refresh 실패 또는 commit 전후 crash에서 두 번째 refresh를 시도하지 않는다. Attempt count가 2이면 terminal ambiguous로 유지하고 success를 추측하지 않는다.
    source: [FR6.2, FR6.3, NFR1, NFR7]

  - id: BR4.9
    statement: Create ledger는 confirmation server time부터 최소 24시간 동안 lifecycle과 restart를 넘어 보존된다.
    category: constraint
    applies_to: [TicketCreateAttemptV1, cleanup]
    trigger: Confirmation, cleanup 또는 lifecycle isolation을 처리한다.
    logic: Confirmation 때 retained_until을 max(existing, confirmation_time_plus_24_hours)로 늘리고 그 전에는 row를 삭제하지 않는다. 미확인 orphan도 initial retained_until 전에는 보존할 수 있으나 실행 권한은 없다.
    violation_behaviour: 삭제를 건너뛰고 safe operational diagnostic만 남긴다.
    source: [FR5.4, FR6.3, NFR2]

  - id: BR4.10
    statement: Gateway create invocation 한 번은 HTTP attempt 정확히 한 번만 수행한다.
    category: constraint
    applies_to: [ItsmGatewayV1.create_ticket]
    trigger: Gateway method를 호출한다.
    logic: Supplied immutable bytes로 한 번 serialize-send-parse하고 typed allowlisted outcome 하나를 반환한다.
    violation_behaviour: Hidden retry, sleep, refresh 또는 reconciliation을 contract violation으로 처리한다.
    source: [FR6.2, FR6.3, NFR2]

  - id: BR4.11
    statement: Credential refresh는 U2 durable reservation 소비 뒤 U1 port 호출 한 번과 기존 server session credential의 atomic commit으로만 수행된다.
    category: constraint
    applies_to: [CredentialRefreshReservationV1, CredentialRefreshCommitEvidenceV1, CredentialRefreshPortV1, prepared, retryable_no_apply]
    trigger: 첫 POST 전 current capability가 만료됐거나 만료 임박했거나 counted POST가 authoritative token-expired no-apply 결과를 반환한다.
    logic: IF attempt count가 2 미만이고 refresh state가 unused이면 U2가 reservation ID, used-at, base credential generation과 reserved state를 atomic commit한 뒤 remaining deadline과 current capability를 U1 port에 전달한다. U1 port는 token exchange를 최대 한 번 수행하고 성공 credential을 기존 server session에 atomic replace한다. U2는 더 큰 returned generation을 committed evidence로 기록하며, restart의 reserved row는 same-actor current session generation이 base보다 클 때만 committed로 복원한다. Send claim은 refresh state가 unused인 valid capability 또는 committed evidence와 generation이 일치하는 capability만 허용한다.
    violation_behaviour: Reservation CAS 패자와 이미 사용된 reservation은 refresh 0회다. Refresh 실패나 current generation이 base와 같거나 낮은 pre-commit crash는 failed와 terminal_failure로 닫는다. Commit 후 응답 전 crash는 더 큰 session generation으로 committed를 복원하되 refresh를 다시 호출하지 않는다. Reserved 또는 failed state에서는 POST하지 않는다.
    source: [FR5.2, FR6.2, FR6.3, NFR1, NFR2]

  - id: BR5.1
    statement: Current server-session delegated credential만 ticket POST를 승인한다.
    category: authorization
    applies_to: [TicketOperations, ItsmGatewayV1]
    trigger: Ticket POST를 준비한다.
    logic: Outbound boundary에서 current server session capability를 얻고 model, browser, persisted payload, external text의 identity claim을 무시한다.
    violation_behaviour: POST 전에 중단하고 authentication_required 또는 permission_denied를 반환한다.
    source: [FR5.1, FR5.2, NFR1]

  - id: BR5.2
    statement: Create 결과와 관찰 가능 출력은 safe allowlisted data만 노출하며 replay에 필요한 key와 bytes는 접근 통제된 server-only ledger에만 보존한다.
    category: authorization
    applies_to: [tool_result, presentation, logging, persistence]
    trigger: Data가 trust boundary를 넘거나 기록된다.
    logic: Credential과 authorization 값은 모든 durable create state에서 금지한다. Idempotency key와 canonical bytes는 U2 ledger의 server-only 접근 통제 필드에만 저장하고 model input, tool result, presentation, history, log, error, metric, test output에서는 제외한다. Raw header, exception, upstream body와 problem detail도 관찰 가능 경계를 넘기지 않는다.
    violation_behaviour: 필요한 ledger 보호를 보장하지 못하면 저장·전송을 중단한다. 관찰 가능 출력의 safe mapping이 불가능하면 redact하고 upstream_unavailable로 fallback한다.
    source: [FR6.1, FR6.2, NFR1]

  - id: BR5.3
    statement: 모든 ITSM-origin text는 escaped untrusted data이며 control flow를 바꾸지 않는다.
    category: authorization
    applies_to: [catalog_labels, error_mapping, presentation, model_context]
    trigger: External text를 읽고 저장하고 표시하거나 model에 다시 제공한다.
    logic: Text를 data로만 취급하고 confirmation, credential, tool, retry policy의 근거로 사용하지 않는다.
    violation_behaviour: Control state를 보존하고 안전하게 escape할 수 없는 text는 생략한다.
    source: [FR6.1, NFR1]

  - id: BR5.4
    statement: 모든 create state는 rich rendering 없이도 이해 가능한 text presentation을 가진다.
    category: policy
    applies_to: [ticket_input, ticket_review, ticket_success, ticket_auth_error, ticket_rate_limited, ticket_ambiguous, ticket_unavailable]
    trigger: Presentation layer가 create state를 render한다.
    logic: Field label, status, explicit choice 또는 next action을 plain text로 제공하고 color-only meaning을 금지한다.
    violation_behaviour: Text-only rendering으로 fallback한다.
    source: [FR7.1, FR7.2, NFR5]

  - id: BR5.5
    statement: U2는 U1 common registry를 수정하지 않고 RegistryV1으로 ticket_write와 create mapper를 등록한다.
    category: constraint
    applies_to: [TicketWritePluginV1, composition_root]
    trigger: Application composition이 U2를 load한다.
    logic: Contract version 1, tool name ticket_write, FunctionTool factory, create mapper key를 documented registry API로 기여한다.
    violation_behaviour: Duplicate, missing, unknown registration이면 startup validation을 fail한다.
    source: [FR7.3, NFR2]

  - id: BR5.6
    statement: U2 functional behavior는 injected clock, randomness, gateway outcome, blocked real network로 결정적으로 test할 수 있어야 한다.
    category: constraint
    applies_to: [unit_tests, integration_tests, contract_tests]
    trigger: Automated test가 실행된다.
    logic: Explicit now, CSPRNG output, catalog/gateway fake, process-restart state, lifecycle event를 inject하고 undeclared network access를 차단한다.
    violation_behaviour: Nondeterministic 또는 live-network-dependent behavior를 quality-gate failure로 처리한다.
    source: [NFR2, NFR8, NFR9]
```

## Rule Summary

| Area | Rules | Outcome |
|---|---|---|
| 입력과 normalization | BR2.1–BR2.5 | Complete, catalog-valid, timezone-safe, deterministic body만 review로 진행 |
| 사람 확인 | BR3.1–BR3.6 | Ledger-first review, actor binding, 15분 expiry, exact current-turn token, U1 public port only |
| 멱등성과 ambiguity | BR4.1–BR4.11 | Existing ledger가 confirmation과 network보다 앞서고, CAS winner만 최대 두 번의 counted POST와 최대 한 번의 durable-reserved refresh 수행 |
| Trust와 presentation | BR5.1–BR5.6 | Delegated authorization, allowlisted output, untrusted text, accessible rendering, additive registration, deterministic test |

## Rule Precedence

Authorization과 no-send 규칙은 retry·reconciliation 규칙보다 우선한다. U1 consumption evidence, CAS claim, attempt-count, immutable-byte 검사는 refresh 또는 recovery 기회보다 우선한다. BR4.7 evidence 없이는 어떤 규칙도 success claim을 허용하지 않는다.

## Assumptions & Open Questions

None.
