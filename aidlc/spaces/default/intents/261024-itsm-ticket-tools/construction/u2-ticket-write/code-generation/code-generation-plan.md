## Summary

- Builds: 기존 U1 안전 경계 위에 ledger-first `ticket_write` 등록 흐름, 최대 2회 멱등 POST, claim-fenced 복구와 one-shot credential refresh를 추가한다.
- Touches: U2 전용 `app/ticketing/create_*.py`, 기존 gateway/capability/runtime 조립, additive SQLite migration, U2 pytest와 changed-line coverage helper를 변경한다.
- Tests: 논리 구성요소별 5~8개 수준의 단위·계약 테스트와 핵심 FakeModel/MockTransport 통합·동시성·보안 테스트 약 60~85개를 추가하고 changed application lines 80% 이상을 검증한다.

## Scope and Guardrails

- U2는 `ticket_write`의 prepare, revise, confirm, cancel, create POST, 결과 조정, refresh reservation, create presentation만 구현한다. U3 update semantics, 새 UI, U4 README·성과 측정·최종 세 도구 판정은 포함하지 않는다.
- U1의 `ticket_tools_state_v1`, `ticket_tools_history_v1`, common `RegistryV1` 구현과 pending mutation schema를 변경하지 않는다. U2는 공개 `put`/`get`/`confirm`/`consume_once`/`invalidate` 연산과 plugin registration만 사용한다.
- U2가 소유하는 유일한 새 저장소는 기존 Server Session SQLite의 `ticket_tools_create_v1.ticket_create_attempts`다. Required C-04 fields와 additive refresh fields만 추가하며, 기존 `sessions`에는 refresh 후 credential generation을 restart 뒤에도 복원하기 위한 additive 정수 필드만 추가한다.
- Review 공개보다 `prepared` ledger commit이 먼저다. U1 consume evidence의 동일 actor·payload attempt 결합, retention 연장과 U2 send claim CAS가 끝나기 전에는 POST를 수행하지 않는다.
- 한 create attempt는 평생 동일한 serialization version, canonical bytes, request hash와 CSPRNG idempotency key를 사용한다. Initial send, refresh recall, reconciliation retry를 합친 POST 횟수는 최대 2회다.
- Active send claim은 저장된 `claim_deadline_at` 전에는 탈취하지 않는다. Reconciliation은 새 recovery identity를 만들지 않고 기존 send `claim_id`를 보존하며, transport와 recovery outcome은 그 exact claim ID로 fence한다.
- No-apply가 권위 있게 보장된 token-expired 401만 `retryable_no_apply`가 된다. Refresh reservation을 network 전에 durable하게 사용 처리한 한 caller만 refresh port를 한 번 호출한다.
- Created 또는 `Idempotent-Replayed` 응답의 authoritative ticket ID 없이는 `completed`나 사용자-visible success를 만들지 않는다. 429는 sleep·retry 0회이고 ambiguous에서 직접 POST하지 않는다.
- Credential, Authorization, client secret, OpenAI API key, idempotency key, canonical bytes, raw header/body/problem detail/exception은 model, tool result, API, browser, log, test failure output에 노출하지 않는다.
- 새 CI provider, workflow, container, cloud resource, queue, cache, distributed lock 또는 feature flag를 만들지 않는다. 현재 single-process deployment와 기존 production approval을 유지한다.

## Planned Source Set

아래 목록이 U2가 만들거나 변경하도록 승인 요청하는 명시적 source/test 범위다. 구현 중 다른 path가 필요하면 코드를 쓰기 전에 계획을 갱신하고 현재 Guard Policy에 따른 재승인을 받는다.

| Path | Action | Responsibility |
|---|---|---|
| `app/ticketing/create_models.py` | create | Strict create draft/action/result, canonical request, review, ledger and claim/refresh DTOs |
| `app/ticketing/create_repository.py` | create | `ticket_tools_create_v1` repository, evidence binding, send/recovery/refresh CAS, retention cleanup |
| `app/ticketing/create_operations.py` | create | Catalog normalization, ledger-first prepare/revise, confirmation, send, reconcile and refresh policy |
| `app/ticketing/create_tools.py` | create | OpenAI Agents SDK `ticket_write` factory and U2 plugin contribution |
| `app/ticketing/create_presentation.py` | create | Text-first create review/success/error/ambiguous mapper |
| `app/config.py` | modify | Dedicated environment-backed refresh signing key ring, current `kid`, verification-only previous keys and bounded key-lifetime validation; no secret default |
| `app/db.py` | modify | Additive U2 table bootstrap/reset without changing U1 schemas |
| `app/session.py` | modify | Persist and atomically advance the delegated credential generation with the existing server-side session credential commit |
| `app/itsm_auth.py` | modify | Existing one-attempt ticket request support for exact bytes and allowlisted headers |
| `app/ticketing/gateway.py` | modify | One-attempt catalog and create methods with typed safe outcome evidence |
| `app/ticketing/capability.py` | modify | Versioned reservation-aware refresh port while preserving U1 read refresh behavior |
| `app/ticketing/tools.py` | modify | Add create-operation/result slots to the existing server-only runtime context |
| `app/agent/assistant.py` | modify | Register the U2 plugin through the existing registry; no registry implementation edit |
| `app/agent/service.py` | modify | Compose U2 repository/operations, current-turn evidence, presentation and cleanup |
| `scripts/changed_line_coverage.py` | create | Merge-base diff plus coverage JSON changed-line threshold checker |
| `tests/conftest.py` | modify | Deterministic catalog/create MockTransport fixtures, fake clocks/randomness and barriers |
| `tests/test_ticket_create_models.py` | create | U2 schema, catalog selector, canonicalization and public-secret boundary tests |
| `tests/test_ticket_create_repository.py` | create | Migration, ledger-first, CAS, claim fencing, retention and refresh reservation tests |
| `tests/test_ticket_create_operations.py` | create | Prepare/confirm/send/reconcile/refresh state-machine tests |
| `tests/test_ticket_write_tool.py` | create | Function-tool schema, registry contribution and safe serialization tests |
| `tests/test_ticket_write_integration.py` | create | FakeModel/MockTransport create flow, restart/lifecycle and presentation tests |
| `tests/test_ticket_create_security.py` | create | Secret canary, malicious external text, network deny and safe-error tests |
| `tests/test_changed_line_coverage.py` | create | Coverage helper diff/rename/deletion/threshold behavior tests |
| `tests/test_ticket_gateway.py` | modify | Catalog/create exact-byte, delegated bearer, timeout and response evidence contract tests |
| `tests/test_ticket_repositories.py` | modify | Replace the legacy four-column create-attempt fixture with the official additive U2 schema while preserving the existing U1 repository-test intent |
| `tests/test_ticket_registry.py` | modify | Additive `ticket_write` plugin and mapper resolution tests |
| `tests/test_ticket_lifecycle.py` | modify | U2 pending invalidation with ledger preservation and restart cleanup tests |
| `tests/test_agent.py` | modify | Existing Agent plus `ticket_read`/`ticket_write` assembly and fixed settings regression |
| `tests/test_session.py` | modify | Switch/logout/expiry revocation without premature U2 ledger deletion |

Existing generic presentation blocks and browser text rendering already support U2 kinds and actions, so no `static/` or endpoint schema change is planned. Tests must prove this reuse; a discovered incompatibility reopens the plan rather than silently adding UI work.

## Implementation Plan

- [x] **Step 1 — Verify the brownfield runner and U1 contract baseline.** Run the exact runner-readiness command from `unit-test-instructions.md`; inspect `PendingMutationRepository.consume_once`, `RegistryV1`, `ItsmGateway`, `TicketRequestCapability`, conversation lock and network-deny fixtures. Stop and reopen Contract Design if successful consume evidence cannot provide `mutation_id` and `confirmed_at`, or if the gateway/capability cannot be extended additively. **Trace:** US2.1; US4.1 / AC4.1.2–AC4.1.5; US5.1 / AC5.1.2, AC5.1.4; C-01.
- [x] **Step 2 — Implement strict U2 models and deterministic canonical serialization.** Add action-specific `TicketWriteToolInputV1`, closed draft/catalog/time models, normalized create payload, version-1 fixed-order compact UTF-8 bytes, SHA-256 bindings, safe review/result envelopes and internal ledger/claim DTOs. Capture explicit `now` once, materialize `classification=standard`, omit absent optionals and keep server-only values non-serializable to public output. Then write and run 5–8+ model tests per applicable model component, including unknown fields, length/enum/timezone limits, ID-or-name exclusivity, byte/hash stability and secret-field absence. **Trace:** US2.1 / AC2.1.1, AC2.1.2, AC2.1.6; BR2.1–BR2.5; NFR1.1–NFR1.3.
- [x] **Step 3 — Add the U2 SQLite migration and durable create-attempt repository.** Add only `ticket_tools_create_v1.ticket_create_attempts` with required C-04 fields and additive refresh reservation/generation fields; do not introduce `claim_kind`, `claim_started_at` or a second recovery claim identity. Preserve U1 namespaces and add only a credential-generation integer to the existing session credential record. Implement `create_prepared`, actor/payload lookup, prior prepared terminalization, idempotent evidence binding plus monotonic retention, send claim, send outcome, same-send-claim reconciliation outcome, one-shot refresh reservation, unconfirmed termination and retention-aware cleanup as explicit affected-row CAS operations. Then write and run repository tests for migration compatibility, unique key/evidence constraints, actor-scope uniqueness, concurrent winners, late stale writes, restart snapshots and exact 24-hour boundaries. Update only the legacy helper/fixture in `tests/test_ticket_repositories.py` that recreates `ticket_create_attempts` with four columns so it uses the official additive U2 schema, without weakening or changing the U1 repository assertions. **Trace:** US2.1 / AC2.1.3–AC2.1.5; BR3.1–BR4.9; NFR2.3, NFR3.1–NFR3.10; C-04.
- [x] **Step 4 — Extend catalog and one-attempt create transport boundaries.** Extend the existing client/gateway additively for service/model catalog reads and `POST /api/v2/tickets`. A create call must pass current delegated capability, exact stored bytes, original idempotency key and a bounded timeout, perform one HTTP attempt, and return only typed created/replayed evidence or a safe categorized failure. It owns no retry, sleep, refresh or reconciliation. Then add and run gateway tests for active/ambiguous/retired catalog data, component-service relation inputs, exact body/header capture, 201/replayed/malformed success, 401/403/422/429/5xx/timeout/response-loss mapping, Retry-After validation and raw-detail/secret exclusion. **Trace:** US2.1 / AC2.1.2, AC2.1.5, AC2.1.6; BR4.5, BR4.7, BR4.10, BR5.1–BR5.3; NFR2.1, NFR7.1–NFR7.2; C-01, C-07.
- [x] **Step 5 — Implement ledger-first prepare/revise and catalog policy.** Resolve each selector to exactly one active match, validate service/component ownership, normalize time/defaults and create one attempt ID, CSPRNG key, bytes and hashes. Commit `prepared` before U1 pending `put`. For revise, CAS-terminalize the previous evidence-free attempt, invalidate the previous pending review, then create/publish the replacement; if confirm/evidence/claim won first, fail closed without a new review. Test each committed failure boundary, orphan prepared rows, ambiguous selectors, concurrent revise/confirm and zero POST before confirmation. **Trace:** US2.1 / AC2.1.1–AC2.1.4; BR3.1–BR3.3; NFR3.2–NFR3.3.
- [x] **Step 6 — Implement exact current-turn confirmation and evidence binding.** Accept authority only from `CurrentTurnEvidenceV1` whose normalized raw message is exactly `확인` or `confirm`. Use U1 public `get`/`confirm`/`consume_once`, locate one actor/payload prepared attempt, bind returned evidence idempotently and extend `retained_until` before claiming. Cancel, changed text, mismatch, expiry and lifecycle invalidation must terminate only revocable authorization and send zero POSTs. A consume-before-bind crash must retain the same attempt/key/bytes, publish a new review and require a new explicit confirmation. Write and run confirmation/lifecycle tests after implementation. **Trace:** US2.1 / AC2.1.3–AC2.1.5; US4.1 / AC4.1.4–AC4.1.5; BR3.3–BR3.6; NFR2.2–NFR2.3.
- [x] **Step 7 — Implement send claims and authoritative outcome fencing.** Before every POST, CAS bound `prepared`, `retryable_no_apply` or `retryable_after_reconcile` with `attempt_count < 2` into `in_flight`, increment count and write one unique send claim identity plus absolute deadline. Compute the deadline and outbound timeout exactly as designed; only the winner calls the gateway. Fence transport and reconciliation outcomes by `status=in_flight` and the exact send `claim_id`; reconciliation preserves that identity and creates no second claim namespace. Store completed only for authoritative ticket-ID evidence; map definitive errors safely and ambiguous outcomes durably. Then run deterministic concurrent confirmer, active deadline, late sender, body/hash/key mismatch, total-budget and second-ambiguous tests. **Trace:** US2.1 / AC2.1.5–AC2.1.6; BR4.1–BR4.8; NFR3.4–NFR3.7, NFR7.1–NFR7.2.
- [x] **Step 8 — Implement reconciliation, the dedicated refresh key ring and durable one-shot credential refresh.** A recovery CAS winner may reconcile an ambiguous or expired send claim but may not POST directly. With no documented result lookup, record lookup-unavailable and move to `retryable_after_reconcile` only when budget remains; a later send needs a new claim with the same bytes/key. Load a dedicated environment-backed key ring with an explicit current signing `kid`, verification-only previous keys, no production default, bounded verification lifetime at least as long as create-attempt retention, and startup validation that fails closed on malformed/unknown configuration. Sign opaque reservations as `r1.<kid>.<payload>.<mac>` with domain-separated actor bindings, credential generation and creator boot ID; expose separate signer/verifier adapters so raw key bytes never enter operations or public runtime context. For authoritative no-apply token expiry, durably reserve refresh before invoking the exact C-01 port once; atomically commit the new token, expiry and incremented credential generation to the server session before returning the same-binding capability. Test rotation overlap/retirement, restart verification, unknown/tampered keys, reservation-before-call crashes, commit-before-response loss, concurrent recovery owners, refresh invocation/exchange ≤1 and third POST 0. **Trace:** US2.1 / AC2.1.5; US4.1 / AC4.1.3–AC4.1.4; BR4.3, BR4.8; NFR3.6, NFR3.9–NFR3.10.
- [x] **Step 9 — Add the U2 function tool, plugin and text-first presentation.** Implement `ticket_write` as the sole U2 model-visible tool factory, consume only server-held runtime/capability/current-turn evidence, and serialize only `TicketMutationToolResultV1`. Contribute the plugin and create mapper keys through existing `RegistryV1` without modifying the registry implementation. Map input correction, complete review, success, auth, rate-limit, ambiguous and unavailable states to plain text plus server-allowlisted actions; external labels remain untrusted text. Then write and run tool/registry/presentation tests covering exact schema/action rules, duplicate registration, secret absence, all mapper kinds and accessible text fallback. **Trace:** US2.1 / AC2.1.3, AC2.1.6; US5.1 / AC5.1.4; BR5.4–BR5.6; NFR9.1; C-03A, C-06.
- [x] **Step 10 — Compose U2 into the existing Agent/runtime and lifecycle.** Instantiate the U2 repository/operations in `AgentService`, inject the configured signer and verifier through separate server-only ports, extend the existing runtime, register `ticket_write` beside `ticket_read`, reuse the same Runner and conversation lock, and persist create presentation through the existing correlation repository. The session credential commit atomically persists token, expiry and credential generation; restart reconstructs a capability at that stored generation. User switch, logout, clear and expiry invalidate U1 pending state and unexecuted authorization but preserve non-expired U2 ledger rows and historical actor bindings. Startup cleanup respects retention. Then run FakeModel/MockTransport integration and lifecycle tests, including key rotation across restart, commit-before-response loss, current-turn confirmation, old-user isolation and existing chat/history fallback; do not add browser files. **Trace:** US2.1 / AC2.1.3–AC2.1.6; US4.1 / AC4.1.2–AC4.1.6; US5.1 / AC5.1.2, AC5.1.4; NFR3.9–NFR3.10, NFR5.1, NFR9.1.
- [x] **Step 11 — Prove deterministic security and network isolation.** Add distinct canaries for delegated token, client secret, OpenAI key, Authorization, idempotency key, canonical bytes, raw body/header/problem detail and exception. Capture model input, tool schema/result, API response, presentation, logs, stdout/stderr and isolated expected-failure diagnostics; require zero matches. Reuse the process-level DNS/TCP default-deny fixture and deliberately probe an unregistered AsyncClient/raw socket. Test malicious catalog/problem text cannot alter user, confirmation, tool choice, claim or retry policy. **Trace:** US4.1 / AC4.1.2, AC4.1.6; US5.1 / AC5.1.2; NFR1.1–NFR1.3, NFR6.2.
- [x] **Step 12 — Add changed-line coverage support and verify the Unit.** Implement and test `scripts/changed_line_coverage.py` for modified/new/renamed/deleted/non-executable lines, coverage JSON parsing, empty denominator and exact 80% threshold. Run every U2 layer command, the exact U2-scoped command and U2 changed-line coverage command from `unit-test-instructions.md`, including the updated `tests/test_ticket_repositories.py` compatibility fixture. Then run the repository-wide regression and the recorded construction verification command as a separate final gate; never lower thresholds, add skip/xfail, or enable live services to pass. **Trace:** US5.1 / AC5.1.2–AC5.1.4; NFR5.1, NFR6.1–NFR6.2; PIPE-U2-07–PIPE-U2-14.
- [x] **Step 13 — Rehearse compatibility and leave implementation evidence ready.** Verify the immediately prior application version can open the U2-migrated copied DB while ignoring the additive table/fields, and that code rollback never deletes/restores away non-expired ledger rows. Confirm the exact planned source set, migration inventory, test counts, network/secret counters, coverage base/files/percentage and any tests written but not executed are available for `code-summary.md`, `source-manifest.json` and `traceability.json`. NFR8.1 remains `Deferred` to U4 measurement evidence. **Trace:** NFR3.1, NFR3.8, NFR5.1, NFR8.1; C-04; infrastructure rollback contract.

## Test File Plan

| Test file | Component coverage | Standard-strategy volume |
|---|---|---|
| `tests/test_ticket_create_models.py` | LC-U2-01/03 DTO, selectors, time, canonical bytes, safe result | 8+ focused cases plus parameter matrices |
| `tests/test_ticket_create_repository.py` | LC-U2-04 migration, evidence, send/recovery/refresh CAS and retention | 8+ focused cases plus concurrency/state matrices |
| `tests/test_ticket_repositories.py` | Legacy U1 repository regression fixture compatibility with the official additive U2 create-attempt schema | Existing assertions preserved; fixture-only compatibility update |
| `tests/test_ticket_gateway.py` | LC-U2-03/06 catalog and one-attempt create transport | 5–8+ added create/catalog cases |
| `tests/test_ticket_create_operations.py` | LC-U2-02/05/06/07/08 full state policy | 8+ focused cases plus failure-injection matrices |
| `tests/test_ticket_write_tool.py` | LC-U2-01 tool schema, runtime authority and plugin | 5–8+ cases |
| `tests/test_ticket_registry.py` | additive plugin/mapper registration | 5+ U2 extension cases shared with existing tests |
| `tests/test_ticket_write_integration.py` | FakeModel/MockTransport vertical create flow and restart | 5–8+ end-to-end cases |
| `tests/test_ticket_create_security.py` | LC-U2-09/10 text, canary and network boundaries | 5–8+ cases plus canary matrix |
| `tests/test_ticket_lifecycle.py`, `tests/test_session.py`, `tests/test_agent.py` | current user, lifecycle isolation, fixed Agent/runtime and text fallback | 5–8+ aggregate U2 regression cases |
| `tests/test_changed_line_coverage.py` | diff/coverage helper correctness | 5–8+ cases |

Parameterized matrices may create more pytest cases than these estimates. They may not omit a named contract boundary to meet a numeric target.

## Completion Criteria

- Ledger-first ordering, U1 public-port-only confirmation, same-attempt crash recovery and actor/payload binding are proven with direct row and POST counters.
- Concurrent send/recovery/refresh flows have at most one durable owner; active claims are not stolen; stale outcome writes are zero.
- Every create POST uses the original stored bytes/key and current delegated capability, and total POST ≤2. Refresh port invocation/exchange ≤1 and 429 sleep/retry = 0.
- Production refresh uses only the dedicated configured key ring; current/previous `kid` behavior, bounded retirement, restart verification and raw-key isolation are proven. Missing or invalid key configuration fails closed before refresh activation.
- Token refresh commits token, expiry and a monotonically increasing credential generation atomically to the server session; restart and commit-before-response-loss never cause a second exchange.
- Authoritative created/replayed ticket ID is required for success; malformed or lost results remain safe non-success/ambiguous.
- Confirmed retention is at least `confirmed_at + 24h`; orphan retention is at least `created_at + 24h`; lifecycle and rollback do not delete those rows early.
- Actual external OpenAI/ITSM calls and secret-canary matches are zero. External text remains non-instructional data.
- All U2-scoped tests and the repository-wide regression pass; changed U2 application executable lines meet the 80% floor without exclusions or threshold changes.
- No U1 table/registry implementation, U3 behavior, static UI, new infrastructure or undocumented result-lookup operation is introduced.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "test-after",
  "source": "team",
  "ordering": "각 테스트 가능한 계층을 구현한 직후 그 계층의 pytest 테스트를 작성·실행하고, 마지막에 실제 OpenAI 호출이 없는 전체 회귀 테스트를 실행한다.",
  "scope": "feature",
  "test_strategy": "standard",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: test-after\n- **Ordering**: 각 테스트 가능한 계층을 구현한 직후 그 계층의 pytest 테스트를 작성·실행하고, 마지막에 실제 OpenAI 호출이 없는 전체 회귀 테스트를 실행한다.\n- **Methodology evidence**: 저장소에는 pytest 통합·회귀 테스트, FakeModel, `httpx.MockTransport` 패턴이 있지만 테스트 선작성 이력은 입증되지 않았으며, 팀은 현재 구조와 조직 기본값에 맞춰 `test-after`를 선택했다.\n- 세 function tool의 schema·호출, ITSM v2 계약, 사용자 위임과 가시성, 토큰 갱신, 비밀정보 비노출, 등록 멱등성, 수정 `If-Match`, 오류 정제, 기존 사용자 전환·세션·대화 이력·고정 모델 회귀를 자동화 테스트로 다룬다.\n- 실제 OpenAI API와 실제 ITSM은 호출하지 않고 FakeModel과 MockTransport를 사용한다. 문서화된 기존 37개 테스트 기준선은 코드 변경 전후에 재실행한다.\n- feature 범위에는 조직 기준인 80% line coverage floor를 적용한다. 현재 저장소에는 coverage 측정 도구나 임계값 설정이 없으므로, 이 기능의 테스트·검증 설계에서 측정 방법을 구체화해야 한다."
    },
    {
      "layer": "project",
      "text": "- R-17은 runtime infrastructure 추가가 아니라 기존 promotion gate에 deterministic concurrency evidence를 추가하는 변경으로 해석했다. barrier event, direct row count, response/publication counter가 blocking evidence다. (learned 2026-10-25) \n\n- 테스트는 시간 기반 flaky race 대신 controllable Runner history-write barrier와 fake clock을 사용한다. 실제 경쟁 순서를 결정적으로 고정하면서 production lock 경계를 그대로 통과시킨다. (learned 2026-10-25) \n\n- NFR3.2와 credential refresh 보강은 새 runtime resource가 아니라 기존 승격 경로의 blocking test contract로 반영했다. confirmation CAS, U2 ledger isolation, crash-before-bind, pre-call/401 shared refresh budget을 각각 관찰 가능한 counter와 snapshot으로 검증한다. (learned 2026-10-25) \n\n- brownfield의 기존 60초 token refresh margin과 server UTC clock을 pre-call usability predicate로 명시하고, gateway-only accessor의 preflight를 첫 public gateway call 내부이지만 첫 socket I/O 이전의 단계로 고정했다. (learned 2026-10-25) \n\n- whole-application 80% threshold를 새로 만들지 않고 changed-source JSON을 U1의 유일한 coverage 판정으로 삼았다. network 차단은 특정 CI provider 방화벽 대신 pytest process의 DNS/TCP default-deny fixture와 deliberate bypass probe로 증명한다. (learned 2026-10-25)"
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Meet an 80% line-coverage floor.",
      "Run the selected tests in CI before merge."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "test-after",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Data model / database behavior - implement.",
      "Data model / database behavior - write and run its tests after implementation.",
      "Repository / data access - implement.",
      "Repository / data access - write and run its tests after implementation.",
      "Business logic - implement.",
      "Business logic - write and run its tests after implementation.",
      "API / endpoint - implement.",
      "API / endpoint - write and run its tests after implementation.",
      "Frontend behavior - implement.",
      "Frontend behavior - write and run its tests after implementation.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:064ee5cc387154391a720806c9fb88310bb87df6291570937ed25a9136f4d036",
  "contract_sha256": "sha256:7c1a2133be59b30537538045547c2115814b810c08e1659e4f43987ab18922ae"
}
```
