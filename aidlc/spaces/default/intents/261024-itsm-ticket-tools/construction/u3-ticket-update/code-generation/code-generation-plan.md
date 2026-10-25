## Summary

- Builds: 기존 U1 안전 경계 위에 durable `ticket_update` prepare/revise/confirm/cancel 흐름, 정확한 `If-Match`, 충돌·불명확 결과 조정과 one-shot update credential refresh를 추가한다.
- Touches: U3 전용 `app/ticketing/update_*.py`, U1의 승인된 update provider port, additive SQLite migration, 기존 Agent/runtime 조립과 U3 pytest를 변경한다.
- Tests: 논리 구성요소별 5~8개 수준의 단위·계약 테스트와 FakeModel/MockTransport 통합·동시성·보안 테스트 약 55~75개를 추가하고 changed application lines 80% 이상을 검증한다.

## Scope and Guardrails

- U3는 `ticket_update`의 prepare, revise, confirm, cancel, update PATCH, latest-detail reconciliation, update presentation과 U3 execution lifecycle만 구현한다. U2 create ledger, 새 endpoint·화면·서비스, U4 README·최종 release manifest·성과 실측은 포함하지 않는다.
- U1 `ticket_tools_state_v1`의 소유권은 U1에 남긴다. U3는 U1 table에 직접 SQL을 실행하지 않고 승인된 `replace_update_pending`과 atomic confirm+consume provider port만 사용한다. 현재 최소 provider DTO·메서드는 C-02의 필수 필드와 원자성을 additive하게 완성하되 U2의 기존 분리 `confirm`/`consume_once` 계약은 보존한다.
- U3가 소유하는 유일한 새 저장소는 기존 Server Session SQLite의 `ticket_tools_update_v1.pending_update_executions`다. U1 migration 뒤, U3 plugin 등록 전에 migration·schema/index fingerprint·startup recovery가 모두 성공해야 한다.
- 새 review는 U3 `staged` 저장 → U1 exact-old replacement → U3 exact-old retire/new active CAS 순서로 게시한다. 검증 또는 U1 replacement 실패는 이전 review를 보존하며, U1 commit 뒤 activation 전 crash는 exact binding으로만 복구한다.
- PATCH authority는 exact active U3 execution, exact U1 pending binding, 현재 raw turn의 명시적 확인, atomic confirm+consume evidence가 모두 있을 때만 성립한다. Record나 `pending_ref` 보유만으로 실행하지 않는다.
- Gateway 호출 하나는 HTTP attempt 하나다. PATCH는 기본 1회이며 authoritative no-apply `token_expired` 401에서 durable refresh reservation과 U1 update refresh port를 거친 동일 bytes/`If-Match` 마지막 1회만 허용한다. 412·428·timeout·transport·그 밖의 401·429에는 PATCH를 재전송하지 않는다.
- Credential, Authorization, client secret, OpenAI API key, canonical patch bytes, raw `If-Match`, raw header/problem/exception은 model, tool schema/result, API, browser, log, test failure output에 노출하지 않는다.
- 실제 OpenAI·ITSM 호출은 0건이다. FakeModel, `httpx.MockTransport`, fake UTC/monotonic clock, controllable barrier와 restart snapshot을 사용한다.
- 새 CI provider, workflow, container, cloud resource, queue, cache, database 또는 distributed lock을 만들지 않는다. 다중-process arbitration은 잔여 위험으로 유지한다.

## Brownfield Blast Radius

| Change surface | Direct consumers | Impact | Planned protection |
|---|---|---|---|
| `app/ticketing/models.py`, `repositories.py`의 U1 update provider contract | U1 repository tests, U2 create confirmation, U3 operations | High | 기존 create DTO·분리 CAS를 유지하고 U3 전용 atomic port와 완전한 replacement evidence를 additive하게 추가한다. |
| `app/db.py`와 새 U3 migration | session startup/reset, copied DB, prior application rollback | High | U1→U3 순서, transactional rollback, idempotent fingerprint와 additive-table backward-read test를 둔다. |
| `app/ticketing/gateway.py`, `capability.py` | read/create operations와 새 update operations | High | 기존 메서드 의미를 바꾸지 않고 update one-attempt method/port를 추가하며 shared regression을 재실행한다. |
| `app/agent/assistant.py`, `service.py`, `app/ticketing/tools.py` | Agent tool set, Runner context, history/presentation | High | 기존 Agent/Runner/model/reasoning/tracing과 conversation lock을 보존하고 누적 runtime에서만 세 번째 plugin을 등록한다. |
| session/lifecycle cleanup | switch, logout, clear, expiry, pending authority | High | 동일 conversation lock 안에서 U1 invalidation과 U3 retire/cleanup 순서를 검증하고 U2 durable ledger는 건드리지 않는다. |
| presentation registry | browser text fallback와 history restoration | Medium | 기존 block schema와 DOM 경계를 재사용하고 모든 update state의 plain-text label/next action을 snapshot으로 검증한다. |

## Planned Source Set

아래 목록이 U3가 만들거나 변경하도록 승인 요청하는 명시적 source/test 범위다. 구현 중 다른 path가 필요하면 코드를 쓰기 전에 계획을 갱신하고 현재 Guard Policy에 따른 절차를 따른다.

| Path | Action | Responsibility |
|---|---|---|
| `app/ticketing/update_models.py` | create | Closed update input/result, canonical patch, execution, refresh, review와 policy DTO |
| `app/ticketing/update_migration.py` | create | `ticket_tools_update_v1` schema/index/marker와 deterministic fingerprint verification |
| `app/ticketing/update_repository.py` | create | staged/active/retired persistence, replacement CAS, locator, refresh reservation와 cleanup |
| `app/ticketing/update_operations.py` | create | prepare/revise/confirm/cancel, read/PATCH budgets, refresh와 reconciliation orchestration |
| `app/ticketing/update_tools.py` | create | OpenAI Agents SDK `ticket_update` factory와 U3 plugin contribution |
| `app/ticketing/update_presentation.py` | create | Text-first update review/result/error/conflict/ambiguous mapper |
| `app/ticketing/models.py` | modify | C-02 `UpdatePendingReplacementV1` provider evidence를 승인된 complete closed shape로 확장 |
| `app/ticketing/repositories.py` | modify | U1-owned exact-old replacement evidence와 U3용 atomic confirm+consume provider port 추가 |
| `app/ticketing/gateway.py` | modify | Exact bytes/`If-Match`를 보내는 one-attempt update method와 allowlisted typed result 추가 |
| `app/ticketing/capability.py` | modify | Durable U3 reservation을 검증하는 U1 `UpdateCredentialRefreshPortV1`와 operation-domain separation 추가 |
| `app/itsm_auth.py` | modify | One-attempt delegated ticket provider가 서버 생성 `If-Match` 헤더를 allowlist하여 U3 PATCH를 전달 |
| `app/db.py` | modify | U1 migration 뒤 U3 migration 호출과 additive reset inventory 연결 |
| `app/session.py` | modify | Expiry terminal path에서 U3 lifecycle coordinator가 authority를 먼저 retire하도록 연결 |
| `app/ticketing/tools.py` | modify | Server-only runtime에 update operations/result slot 추가 |
| `app/agent/assistant.py` | modify | 누적 runtime registry에 U3 plugin 등록; U1 checkpoint seam은 유지 |
| `app/agent/service.py` | modify | U3 repository/operations/lifecycle/mapper 조립, startup recovery와 same-lock cleanup 연결 |
| `tests/conftest.py` | modify | Deterministic update MockTransport, fake clocks, restart DB와 barrier fixtures |
| `tests/test_ticket_update_models.py` | create | Patch schema, omit/null, canonical bytes/hash, result/secret boundary tests |
| `tests/test_ticket_update_migration.py` | create | Migration order, fingerprint, rollback, repeat startup와 prior-version compatibility tests |
| `tests/test_ticket_update_repository.py` | create | Round-trip, single-active CAS, locator, refresh reservation, cleanup와 tamper tests |
| `tests/test_ticket_update_u1_contract.py` | create | Complete replacement evidence, atomic confirm+consume, rollback와 U2 compatibility provider tests |
| `tests/test_ticket_update_operations.py` | create | Prepare/revise/confirm/PATCH/reconcile/refresh state-machine and attempt-bound tests |
| `tests/test_ticket_update_tool.py` | create | Function-tool schema, runtime authority, plugin과 safe serialization tests |
| `tests/test_ticket_update_integration.py` | create | FakeModel/MockTransport vertical update flow, response loss, restart와 Agent assembly tests |
| `tests/test_ticket_update_lifecycle.py` | create | switch/logout/clear/expiry, terminal cleanup, retention과 conversation-lock tests |
| `tests/test_ticket_update_security.py` | create | Secret/patch/header canary, malicious external text, network deny와 accessible-state tests |
| `tests/test_agent.py` | modify | 누적 Agent/Runner runtime의 정확한 세 tool 조립 회귀 검증 |
| `tests/test_ticket_registry.py` | modify | 누적 registry의 정확한 세 tool 이름·schema 조립 회귀 검증 |

`pytest.ini`, `requirements.in`, `requirements.txt`, `scripts/changed_line_coverage.py`는 이미 필요한 pytest/coverage 설정과 pinned 도구를 제공한다. U3는 이를 검증하고 재사용하며, 승인된 contract drift가 발견되지 않는 한 의존성이나 테스트 설정을 수정하지 않는다. 기존 build-free browser renderer도 현재 `TicketPresentationV1` block을 지원하므로 `static/` 변경은 계획하지 않는다.

## Implementation Plan

- [x] **Step 1 — Freeze the approved C-02/C-05 surface and module topology.** Verify that the approved contract still defines the complete `UpdatePendingReplacementV1`, `PendingUpdateExecutionV1`, `UpdateCredentialRefreshReservationV1`, `UpdateCredentialRefreshPortV1`, exact-old publication order and PATCH ceiling. Map current imports/consumers to the planned source set without changing application code. Stop on missing or contradictory contract ownership rather than approximating atomicity. **Trace:** US3.1; AC3.1.3–AC3.1.5; C-02, C-05, C-07; PIPE-U3-02.
- [x] **Step 2 — Establish the brownfield baseline and runner readiness.** Run the existing full pytest suite before application changes and the exact U3 prerequisite command from `unit-test-instructions.md`; record commit, pass/fail/skip counts and any pre-existing failures. Verify `pytest.ini`, pinned pytest/coverage, FakeModel/MockTransport seams and process-level network deny. **Trace:** US5.1 / AC5.1.2, AC5.1.4; NFR5.1, NFR6.2; PIPE-U3-01, PIPE-U3-05, PIPE-U3-07.
- [x] **Step 3 — Implement strict update models and canonical patch serialization, then test them.** Add action-specific `TicketUpdateToolInputV1`, closed eight-field `TicketPatchInV1`, omitted/null sentinel semantics, fixed-key-order compact UTF-8 serialization version 1, exact SHA-256, safe review/result envelopes, execution/refresh DTOs and request-scoped attempt policy. Extend U1 replacement evidence to the complete C-02 shape without changing create types. Then write and run 5–8+ cases per applicable model component for unknown/forbidden fields, all allowed types and limits, omit/null, empty/no-op input, byte/hash stability, closed schemas and server-only field absence. **Trace:** US3.1 / AC3.1.1, AC3.1.3, AC3.1.6; BR3.1–BR3.3, BR3.5, BR3.14; NFR1.1–NFR1.3, NFR3.2.
- [x] **Step 4 — Add the U3 migration and execution repository, then test them.** Create `ticket_tools_update_v1.pending_update_executions`, exact actor/session/conversation/ticket active locator index, actor-scope single-active partial unique index and migration marker/fingerprint. Implement stage/get/activate-replacement/retire/find-active/reserve-refresh/reconcile-refresh/cleanup with exact affected-row CAS and hash revalidation. Then write and run migration/repository tests for U1→U3→recovery→plugin order, repeated startup, forced rollback, staged/active/retired round-trip, exact-old retire+new promote transaction, actor isolation, locator cardinality, tamper/corruption rejection, retention and idempotent cleanup. **Trace:** AC3.1.3, AC3.1.6; BR3.18–BR3.20; NFR3.7–NFR3.10; PIPE-U3-03, PIPE-U3-04.
- [x] **Step 5 — Complete the U1-owned update provider ports, then test them.** Keep U2's public `confirm` and `consume_once` behavior unchanged, while adding a U3 consumer port that validates current-turn evidence and the full update binding and commits confirmed+consumed in one U1 transaction with no observable confirmed intermediate state. Return the complete immutable `UpdatePendingReplacementV1` only after exact-old replacement commits. Test prepare/revise row counts, insert rollback, stale/actor mismatch, concurrent confirm/revise, transaction crash points and U2 regression. U3 production code may call only these ports, never U1 table SQL. **Trace:** US3.1 / AC3.1.3; US4.1 / AC4.1.5; BR3.5–BR3.7, BR3.18; NFR2.2–NFR2.3, NFR3.3, NFR3.7; C-02.
- [x] **Step 6 — Extend one-attempt transport and update credential refresh ports, then test them.** Add a gateway update call that sends delegated bearer, exact canonical bytes and stored `IfMatchVersion` once, parses only allowlisted success evidence and exposes typed safe failures. Add the U1 update refresh port over a durable U3 reservation with operation-domain-separated actor binding, positive remaining deadline, one exchange/call and atomic session credential commit. Test exact wire body/header, permission outcomes, malformed success, typed/untyped 401, 412/428, 429, 5xx/timeout/transport, session-generation recovery and raw-detail/secret exclusion. **Trace:** AC3.1.2, AC3.1.4–AC3.1.5; AC4.1.2–AC4.1.4, AC4.1.6; BR3.4, BR3.8–BR3.10, BR3.14–BR3.15; NFR2.1, NFR3.1, NFR3.4–NFR3.6, NFR7.1.
- [x] **Step 7 — Implement prepare/revise durable publication, then test it.** Read the latest detail through U1 `read_for_update`, validate strong ETag/public version, compute only actual allowed diffs, stage the U3 execution, call U1 exact-old replacement and activate the exact U3 row in one repository transaction. Reconstruct a safe full review only after activation; preserve the old review on validation/replacement failure. Test all eight fields, no-op/invalid ETag, prepare/revise, stale old, injected writes, activation crash, response loss before return and concurrent publication. **Trace:** US3.1 / AC3.1.1–AC3.1.3, AC3.1.6; BR3.1–BR3.5, BR3.18, BR3.20; NFR3.1–NFR3.3, NFR3.7, NFR3.10.
- [x] **Step 8 — Implement confirm, PATCH, refresh and reconciliation, then test it.** Require exact raw-turn confirmation, tool target and all U1/U3 bindings; rehash stored bytes; atomically confirm+consume; then perform the first PATCH. Only authoritative no-apply `token_expired` may reserve refresh once, call the U1 port once and issue the identical second/final PATCH. For 412/428 or ambiguity, read latest detail without PATCH replay and emit success only for complete expected changes plus increased version; otherwise create a new review or remain ambiguous. Test deterministic concurrent confirm, consume crash, PATCH/refresh counters, two-401 and mixed outcomes, partial/different/no-read reconciliation and success-publication count. **Trace:** US3.1 / AC3.1.3–AC3.1.5; US4.1 / AC4.1.3–AC4.1.4, AC4.1.6; BR3.6–BR3.12; NFR3.3–NFR3.6, NFR7.1–NFR7.2.
- [x] **Step 9 — Implement lifecycle, startup and response-loss recovery, then test it.** Under the existing conversation lock, retire U3 authority on cancel, switch, logout, clear, expiry or terminal/missing U1 pending; retain then delete rows only under the existing session-state cleanup window. On startup/access, recover only exact U1-committed staged rows, retire orphans and reconcile committed credential generations without a second refresh. Recover review-response loss only through the exact actor/ticket active locator and full U1 rebinding; version drift returns conflict with zero PATCH. **Trace:** AC3.1.6; AC4.1.4–AC4.1.5; BR3.13, BR3.19–BR3.20; NFR2.2–NFR2.3, NFR3.6, NFR3.8–NFR3.10, NFR7.2.
- [x] **Step 10 — Add the U3 tool, plugin, presentation and cumulative runtime assembly, then test them.** Implement model-visible `ticket_update` with only action/ticket/patch/pending fields and server-held capability/current-turn evidence. Register U3 through `RegistryV1`, extend runtime/service composition and map review, explicit-confirmation, cancel, success, auth error, conflict, rate limit, ambiguous, invalidated and unavailable states to plain text plus safe actions. Preserve U1 checkpoint seams, existing Agent/Runner/model/reasoning/tracing, reply/history fallback and browser contracts. Run schema, plugin, mapper, FakeModel/MockTransport and exact-three-tool cumulative assembly tests. **Trace:** US3.1 / AC3.1.3–AC3.1.6; US5.1 / AC5.1.2, AC5.1.4; BR3.16–BR3.17; NFR5.1, NFR9.1; C-03A, C-05, C-06.
- [x] **Step 11 — Prove security, network isolation and accessibility.** Inject distinct credential, Authorization, canonical patch, `IfMatchVersion`, raw header/problem/exception and malicious external-text canaries. Capture model input, tool schema/result, HTTP/API response, presentation, logs and expected-failure diagnostics; require zero leaks and zero instruction effects. Reuse the process-level DNS/TCP default-deny fixture and deliberate bypass probe. Snapshot every NFR9.1 state with its plain-text label and next action through keyboard/screen-reader compatible existing rendering. **Trace:** AC4.1.2, AC4.1.6; AC5.1.2, AC5.1.4; BR3.14, BR3.17; NFR1.1–NFR1.3, NFR6.2, NFR9.1; PIPE-U3-07–PIPE-U3-10.
- [x] **Step 12 — Verify test configuration, Unit coverage and full regression.** Confirm `pytest.ini`, `coverage==7.17.0` pins and `scripts/changed_line_coverage.py` need no change. Run every layer command and the exact U3-scoped command from `unit-test-instructions.md`, then its single-run changed-line coverage chain at ≥80%. Separately run the repository-wide regression and recorded Construction verification command once; do not lower thresholds, add skip/xfail or enable live services to pass. Record that data-at-rest ACL/backup evidence remains a production release gate rather than fabricating repository evidence. **Trace:** US5.1 / AC5.1.2, AC5.1.4; NFR5.1, NFR6.1–NFR6.2; PIPE-U3-01, PIPE-U3-05–PIPE-U3-12.
- [x] **Step 13 — Rehearse compatibility and prepare implementation evidence.** Verify the immediately prior application can open a copied U3-migrated DB while ignoring the additive namespace, rollback never drops U3 rows, and missing/fingerprint-mismatched migration prevents plugin activation. Confirm the exact source manifest, migration/index inventory, commands/results, test counts, coverage base/files/percentage, network/secret/safety counters, deviations and unexecuted tests are ready for `code-summary.md`, `source-manifest.json` and `traceability.json`. Mark NFR8.1 as deferred to U4's real environment 3+3 measurement ledger, not as completed by synthetic tests. **Trace:** NFR3.8–NFR3.10, NFR5.1, NFR8.1; C-05; infrastructure rollback and U4 handoff.

## Test File Plan

| Test file | Component coverage | Standard-strategy volume |
|---|---|---|
| `tests/test_ticket_update_models.py` | Input/result DTO, omit/null, canonicalization, safe/server-only boundary | 5–8+ focused cases plus field matrices |
| `tests/test_ticket_update_migration.py` | Migration order/fingerprint/rollback/restart compatibility | 5–8+ cases |
| `tests/test_ticket_update_repository.py` | Execution CAS, locator, refresh, cleanup, corruption/restart | 8+ focused cases plus concurrency/state matrices |
| `tests/test_ticket_update_u1_contract.py` | Replacement evidence and atomic confirmation provider compatibility | 5–8+ cases plus race/crash matrix |
| `tests/test_ticket_update_operations.py` | Prepare/revise/confirm/read/PATCH/refresh/reconcile policies | 8+ focused cases plus outcome matrices |
| `tests/test_ticket_update_tool.py` | Tool schema, server context, plugin and safe serialization | 5–8+ cases |
| `tests/test_ticket_update_integration.py` | FakeModel/MockTransport vertical update, restart/response loss and Agent assembly | 5–8+ end-to-end cases |
| `tests/test_ticket_update_lifecycle.py` | clear/switch/logout/expiry and same-lock retirement | 5–8+ cases |
| `tests/test_ticket_update_security.py` | Secret/external-text canaries, network deny and accessible state text | 5–8+ cases plus canary/state matrix |

Parameterized matrices may create more pytest cases than these estimates. They may not omit a named contract boundary to meet a numeric target.

## Completion Criteria

- The complete C-02 provider/consumer fixture proves exact replacement evidence, atomic confirm+consume, old-review rollback preservation and no cross-owner table writes.
- U3 migration is transactional, idempotent and ordered after U1/before plugin registration; actor scope has at most one active execution and every corruption/mismatch yields PATCH 0.
- Every PATCH uses current delegated capability, byte-identical canonical patch and the stored validated `IfMatchVersion`. PATCH total is 1 normally and at most 2 only for the approved authoritative no-apply 401; refresh port invocation is at most 1.
- 412/428/timeout/transport/untyped 401/429 never trigger PATCH replay. Success requires expected applied changes and `new_version > base_version`.
- Review publication, confirm/revise competition, crash/restart and response loss have deterministic single winners and never invent authority. Other actor/ticket rows are never returned.
- All public update states carry plain text and a safe next action. External text remains untrusted data and no credential, canonical patch, raw `IfMatchVersion`, header, problem or exception canary crosses a public/log boundary.
- U3-scoped tests and repository-wide regression pass with real external network calls 0. Changed U3 application executable lines meet the 80% floor without exclusions or threshold changes.
- No new endpoint, UI, service, deployment infrastructure or U2 ledger dependency is introduced. NFR8.1 remains assigned to U4 real-environment measurement.

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
