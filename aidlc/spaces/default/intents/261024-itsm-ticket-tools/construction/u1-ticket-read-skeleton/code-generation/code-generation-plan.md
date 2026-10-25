## Summary

- **Builds:** 기존 FastAPI·OpenAI Agents SDK 대화 경로에 서버 세션 기반 `ticket_read` walking skeleton을 연결하고, U2/U3가 확장할 공통 capability, 안전 오류·DTO, pending-mutation/cursor/presentation 저장소, tool·presentation registry를 구현한다. 이번 수정에서는 Runner/history와 세션 만료 cleanup을 하나의 conversation lock 아래 직렬화하고 post-Runner 만료 결과 폐기와 terminal cleanup을 완결한다.
- **Touches:** 새 `app/ticketing/` 패키지와 기존 `app/db.py`, `app/session.py`, `app/itsm_auth.py`, `app/agent/*`, `app/main.py`, `app/schemas.py`, `static/app.js`, `static/style.css`, `requirements.in`, `requirements.txt`, `tests/*`를 최소 범위로 수정한다. 새 Agent·서비스·화면·배포 인프라는 만들지 않는다.
- **Tests:** 기존 37개 pytest 기준선을 먼저 확인하고, logical component별 5~8개 이상의 단위·경계 사례와 FakeModel/`httpx.MockTransport` 통합·보안·회귀 테스트를 추가한다. 분리된 `confirm`/`consume_once`, U2 ledger 보존, 60초 credential preflight·401 공유 budget, process-level network default-deny, rollback write compatibility와 Runner/expiry barrier를 검증한다. 실제 OpenAI·ITSM 호출은 0건이며 최종 전체 suite와 source manifest가 가리키는 변경 application code의 line coverage 80% floor를 검증한다.

## Scope and Guardrails

- U1이 소유하는 기능은 `ticket_read` 목록·검색·상세와 공통 확장 경계다. `ticket_write`, `ticket_update`, README 최종 완결은 각각 U2, U3, U4에 남긴다.
- U1 체크포인트의 Agent에는 `ticket_read`만 등록한다. registry는 후속 도구 factory를 받을 수 있지만 모델에 내부 helper를 노출하지 않으며, U4에서 최종 이름 집합이 정확히 세 개인지 검증한다.
- 티켓 ID, upstream cursor, 사용자 신원, delegated credential, ETag는 서버가 소유한다. credential·Authorization·원본 problem detail·원본 header는 모델 입력, tool schema/result, HTTP 오류, 로그, fixture 실패 출력에 넣지 않는다.
- `docs/itsm/integration-guide.md`와 `docs/itsm/openapi.json`의 `/api/v2/tickets` 계약만 사용하며 다른 저장소 코드는 import하거나 복사하지 않는다.
- 기존 model `gpt-5.4`, reasoning 설정, tracing 비활성, `Runner`, `SQLiteSession`, 세션 cookie, chat/history API의 기존 필드는 유지한다. optional presentation은 기존 text reply가 언제나 fallback이 되도록 additive하게 추가한다.
- 승인된 BR5.7·BR5.8, NFR2.6·NFR3.2·NFR7.4, SEC-U1-07·SEC-U1-13과 PIPE-U1-06·PIPE-U1-10~12를 구현 기준으로 사용한다. 동일 conversation lock을 **Runner 호출 전에** 획득하고 Runner·SDK history 접근·post-Runner persisted-expiry 재검사·presentation commit/readback·응답 결정 또는 expiry cleanup 종료까지 유지한다. 어떤 dependency나 route도 이 lock 밖에서 같은 conversation의 SDK history를 삭제하지 못한다.
- credential preflight의 정책 소유자는 `TicketOperations`다. `credential_expires_at <= server UTC now + 60초`이면 gateway를 호출하기 전에 narrow capability/refresh port를 통해 one-shot budget을 소비하고, gateway는 refresh를 판단하지 않은 채 정확히 한 HTTP attempt만 수행한다. preflight 성공 뒤 받은 401에는 두 번째 refresh를 허용하지 않는다.

## Planned Production Structure

| Path | Planned responsibility |
|---|---|
| `app/ticketing/models.py` | strict V1 request/result, safe projection/error, canonical query, presentation, pending-mutation DTO |
| `app/ticketing/capability.py` | non-serializable request-scoped `TicketRequestCapability`, actor binding, TicketOperations가 호출하는 60초 preflight/refresh port와 one-refresh budget |
| `app/ticketing/gateway.py` | application-lifetime httpx transport reuse, one-attempt ITSM v2 list/detail adapter, allowlisted response/error mapping |
| `app/ticketing/repositories.py` | `ticket_tools_state_v1` pending/cursor repositories and `ticket_tools_history_v1` presentation companion repository |
| `app/ticketing/operations.py` | read validation, canonical query/cursor binding, pre-call/401 공유 retry·refresh budget, safe list/detail projection |
| Existing session persistence | 기존 물리 세션의 인증·권한·위임 credential 열을 그대로 보존하는 additive `session_expires_at` migration, absolute-expiry 판정과 fail-closed cleanup |
| `app/ticketing/registry.py` | name-keyed tool factory and presentation-kind mapper extension contracts |
| `app/ticketing/tools.py` | OpenAI Agents SDK `ticket_read` function tool using only server-held context |
| `app/ticketing/presentation.py` | allowlisted TicketPresentationV1 mapping, exact text-hash correlation, text fallback |
| Existing app modules | DB migration/bootstrap, session lifecycle cleanup, Agent/Runner wiring, chat/history additive presentation, startup orphan cleanup |
| `static/app.js`, `static/style.css` | safe DOM text rendering for supported presentation kinds while preserving existing text/live/keyboard behavior |

Exact internal names may be consolidated where doing so reduces coupling, but the contract ownership and module boundaries above must remain recognizable and independently testable.

## Implementation Plan

- [ ] **1. Establish the brownfield baseline and runner readiness.** Run `.venv/bin/python -m pytest -q`, record the actual baseline against the documented 37 tests, confirm `pytest.ini` discovery and FakeModel/MockTransport seams, and verify that no test requires live OpenAI or ITSM access. Do not change production code until the baseline is understood. **Trace:** US5.1 / AC5.1.2, AC5.1.4; NFR5, NFR6.
- [ ] **2. Add the U1 package skeleton and strict V1 data contracts.** Create the `app/ticketing/` package, implement exact-field Pydantic models for read input, canonical queries, safe list/detail/error/tool results, pending mutation, cursor binding and presentation; reject unknown fields and keep server-only ETag/capability data out of public serialization. Then add and run 5~8+ model/schema tests covering list/detail modes, limit 1/20/100/101, enums, unknown fields, malicious text as data, and secret-field rejection. **Trace:** US1.1 / AC1.1.2~AC1.1.4; US1.2 / AC1.2.2, AC1.2.4; US4.1 / AC4.1.2, AC4.1.6.
- [ ] **3. Implement U1-owned SQLite namespaces and repositories.** Extend existing initialization/reset paths with additive `ticket_tools_state_v1` tables for `pending_ticket_mutations` and `ticket_cursor_bindings`, plus the history DB `ticket_tools_history_v1` presentation companion table. Implement `confirm` and `consume_once` as separate exact-binding CAS transitions; successful consumption returns exactly `ConsumedMutationEvidenceV1 { mutation_id, confirmed_at }` once and never transport authority. Preserve U2 `ticket_tools_create_v1` rows, idempotency keys and canonical bytes across every U1 lifecycle cleanup, including consume-before-bind crash recovery. Implement once-only cursor resolution, assistant correlation/readback and orphan cleanup without raw payloads, credentials, upstream bodies or confirmation text. Then add and run repository tests for concurrent/repeated CAS, exact evidence fields, operation isolation, tamper/mismatch/expiry, U2 ledger snapshots, crash-before-bind re-review/reconfirmation, restart recovery, clear ordering and idempotent cleanup. **Trace:** BR5.8; NFR3.2; US1.1 / AC1.1.2; US4.1 / AC4.1.5; US5.1 / AC5.1.4; C-01, C-03, C-03A, C-06.
- [ ] **4. Implement the request-scoped identity capability and one-attempt gateway.** Build a non-serializable capability from the HttpOnly server session and expose a narrow preflight/refresh port that `TicketOperations` invokes before the gateway. The preflight uses the injected server UTC clock and exact predicate `credential_expires_at <= utc_now + 60초`, shares one operation refresh budget with reactive 401 handling, returns no raw credential, and fails before ticket HTTP when refresh fails. Adapt the application-lifetime httpx client for typed list/detail calls with per-attempt `ITSM_TIMEOUT_SECONDS`; the gateway owns no refresh decision and performs exactly one HTTP attempt per invocation. Map only allowlisted fields and safe errors; preserve strong detail ETag only in server metadata for U3. Then add and run boundary tests at 60초 ±1µs, preflight success/failure, preflight-success-then-401 with no second refresh, non-imminent first-401 refresh, every list parameter, delegated bearer use, service-token calls 0, malformed bodies, status mapping, safe request IDs and secret canaries. **Trace:** BR1.3, BR3.5; NFR7.4; US1.1 / AC1.1.1, AC1.1.3; US1.2 / AC1.2.1~AC1.2.4; US4.1 / AC4.1.1~AC4.1.3, AC4.1.6.
- [ ] **5. Implement `TicketOperations.ticket_read`.** Normalize and canonicalize first-page queries, issue unpredictable server-bound continuation references instead of raw cursors, resolve references once against exact actor/conversation/query binding, distinguish empty from failed, and project only SafeTicketSummaryV1/SafeTicketDetailV1. Before the first gateway invocation, call the narrow credential preflight and own its one-shot budget; after an eligible first 401, refresh only if that same budget remains. Enforce at most two HTTP attempts, one 250ms retry only for timeout/transport/500/502/503/504, no sleep/retry on 429 and the whole-operation deadline `2 × ITSM_TIMEOUT_SECONDS + 0.25초`. Then add and run operation tests using injected UTC/monotonic clocks and sleeper for preflight/401 combinations, retry counts, timing budget, empty/list/detail outcomes, cursor rejection, cleanup, refresh failure and success-not-guessed behavior. **Trace:** BR1.3, BR3.1~BR3.5; NFR2, NFR4, NFR7.1~NFR7.4; US1.1 / AC1.1.1~AC1.1.5; US1.2 / AC1.2.1~AC1.2.5; US4.1 / AC4.1.3, AC4.1.6.
- [ ] **6. Add registry contracts and the `ticket_read` SDK function tool.** Implement name-keyed tool factories and presentation-kind mappers with duplicate/unsupported-name rejection. Register only `ticket_read` in the existing Agent, pass authority solely through `RunContextWrapper`/server context, keep input schema business-only, and preserve the current Agent, model, reasoning and tracing settings. Then add and run registry/tool tests for schema shape, no credential fields, exact U1 tool set, duplicate rejection, a synthetic later tool/mapper extension, safe serialized results and malicious external instructions remaining inert data. **Trace:** US1.1 / AC1.1.3; US1.2 / AC1.2.4; US4.1 / AC4.1.1, AC4.1.2; US5.1 / AC5.1.2.
- [ ] **7. Wire the protected chat lifecycle and presentation persistence.** Update `AgentService` and routes so the current server session creates the capability, acquires one application lock per conversation **before Runner**, runs the existing Runner, derives exact persisted assistant sequence/text hash, atomically writes and reads optional presentation metadata, and releases the lock only after commit/readback. Clear presentation metadata before history; invalidate only U1 pending/cursor state on clear, user switch, logout or expiry while preserving U2 `ticket_tools_create_v1` row/key/bytes; perform startup/history orphan cleanup. Then add and run concurrency/lifecycle tests that interleave chats, restart, clear, switch users and repeat cleanup, proving no metadata misbinding, no old authority crossing and no downstream durable-ledger mutation. **Trace:** BR5.5, BR5.8; NFR3.2; US4.1 / AC4.1.1~AC4.1.5; US5.1 / AC5.1.4; C-01, C-03, C-03A.
- [ ] **8. Extend API and browser rendering additively.** Add optional `presentation` to chat/history output without changing existing `reply`/`messages` meanings. Render only version/kind/block combinations registered by the server, create DOM text nodes rather than interpreting HTML/Markdown, and fall back to assistant text for missing, malformed, unsupported or mismatched metadata. Keep existing input, landmarks, keyboard submission and live announcements; give loading/success/empty/error/next-page states explicit text. Then add and run endpoint/presentation/static-contract tests for old rows, malformed metadata, unsupported versions, escaping payloads, fallback, accessibility text and unchanged legacy responses. **Trace:** US1.1 / AC1.1.3, AC1.1.4, AC1.1.6; US1.2 / AC1.2.2~AC1.2.5; US5.1 / AC5.1.4; NFR9.
- [ ] **9. Prove the walking skeleton end to end without external calls.** Extend FakeModel and MockTransport fixtures so one test exercises server session → existing Agent/Runner → `ticket_read` → delegated ITSM v2 list/detail → safe tool result → persisted assistant text/presentation → history reload. Install an autouse Python-process default-deny fixture for DNS/TCP entry points and add deliberate fresh-`httpx.AsyncClient` plus raw-socket bypass probes that fail with `UnexpectedNetworkError` before DNS/socket I/O. Add negative flows for 404, 429, pre-call/401 shared refresh, injected instructions and secret canaries. Run the exact U1 command from `unit-test-instructions.md`. **Trace:** BR6.1; US1.1 / AC1.1.1~AC1.1.6; US1.2 / AC1.2.1~AC1.2.5; US4.1 / AC4.1.1~AC4.1.3; US5.1 / AC5.1.2, AC5.1.4.
- [ ] **10. Add deterministic coverage support and run regressions.** Add a pinned `coverage` dependency through `requirements.in`/compiled `requirements.txt` without introducing a new formatter, linter or type checker. Run the whole pytest suite as a regression gate without inventing a whole-application threshold. Generate coverage from the full suite, then apply the sole U1 80% decision to the exact changed application paths in `source-manifest.json` via `coverage json --include=... --fail-under=80`; fail when no claimed source is measured and repair U1-owned gaps without weakening thresholds. Confirm existing session, user switch, history, UI/API and fixed Agent settings remain green. **Trace:** US5.1 / AC5.1.2~AC5.1.4; NFR5, NFR6.1.
- [ ] **11. Produce implementation evidence.** Record changed files, exact commands/results, test count, coverage, zero-live-network assertion, secret-canary outcome, remaining risks and U2/U3 extension points in `code-summary.md`; generate `traceability.json` covering the U1 stories, requirements and contracts. Do not claim README completion or final three-tool assembly in U1. **Trace:** US5.1 / AC5.1.2, AC5.1.4.
- [ ] **12. Repair R-08 with a strict server-only `read_for_update` port.** Add an exported typed port returning `ReadForUpdateResultV1` only when the detail response carries a strong quoted-decimal ETag whose numeric value exactly equals the public ticket version. Treat missing, weak, non-decimal or mismatched ETags as `SafeErrorV1(upstream_unavailable)` and ensure no update review or PATCH path can run after that failure; do not change ordinary `ticket_read` detail semantics and never serialize the ETag to the model/client. Then add and run focused gateway/operation tests for every accepted/rejected ETag form, public-version mismatch, server-only serialization, and downstream call counts of 0 on rejection. **Trace:** R-08; U3 precondition; US4.1 / AC4.1.2, AC4.1.6.
- [ ] **13. Repair R-09 with persisted absolute session expiry and backward-write-compatible cleanup.** Add `session_expires_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z'` to the existing physical session table by additive migration only: preserve every existing auth, user, permission and delegated-credential column name, type, nullability and meaning. New sessions receive exactly `created_at + 8h`; activity, token refresh and restart never extend it. Backfill legacy rows from parseable `created_at + 8h`; treat missing/malformed creation time as expired. Rehearse the immediately prior release's session create, restore, login and logout/write SQL paths against the migrated DB; after forward redeploy, rows written by the old version through the epoch default must fail closed as expired and require re-login. On protected requests, clean U1 revocable state and the session before Runner/ITSM without touching the U2 ledger. Then add and run exact-boundary, restart, migration/backfill, prior-release write, forward-redeploy, cleanup-failure, token-refresh and user-switch tests. **Trace:** R-09; NFR2.5; NFR5.2; C-03A.
- [ ] **14. Repair R-10 with a CSPRNG-backed continuation-reference boundary.** Make reference generation injectable for deterministic tests while production uses the OS CSPRNG with at least 128 bits of entropy. Issue 100,000 references in the required quality test and prove zero collisions, no raw upstream cursor disclosure and no sequential/timestamp-only shape; weak or deterministic injected sources that cannot meet the contract must be rejected fail-closed. Preserve exact actor/session/conversation/query binding and once-only resolution. Then run the focused repository/operation quality tests. **Trace:** R-10; NFR7; C-06.
- [ ] **15. Re-prove correlation, confirmation, refresh and isolation boundaries together.** Strengthen the concurrency fixture to prove the same conversation lock is acquired before Runner and held through persisted assistant-item correlation, companion commit/readback and response determination; the metadata/message mismatch count must be 0. Re-run separate confirmation/consumption CAS and U2 ledger isolation, the 60초 preflight/401 shared refresh budget, prior-release migration writes and network bypass probes. Run the exact U1-scoped command, full regression and changed-source coverage commands from `unit-test-instructions.md`; require all tests green, claimed application source line coverage at least 80%, real-network calls 0 and secret-canary matches 0. **Trace:** R-08, R-09, R-10; BR5.8; NFR3.2, NFR5, NFR6, NFR7.4.
- [ ] **16. Refresh implementation evidence for the repaired checkpoint.** Update `code-summary.md`, `traceability.json` and source manifest with the exact changed files, commands/results, R-08/R-09/R-10 evidence, 100,000-reference result, expiry/migration behavior, lock ordering, test count, coverage, zero-live-network assertion and remaining risks. **Trace:** R-08, R-09, R-10; US5.1 / AC5.1.2, AC5.1.4.
- [ ] **17. Repair R-17 by unifying protected-chat and expiry cleanup serialization.** Refactor the current session dependency, `AgentService`, route/lifecycle wiring and history cleanup so they resolve the same per-conversation lock provider. Acquire that lock before the authoritative persisted-session check and Runner; re-read persisted expiry immediately before Runner and immediately after Runner. The post-Runner check must occur before correlation, reply mapping, text-only fallback, presentation commit or any response decision. When the row is missing or expired, discard the Runner result and, while retaining the lock, clear presentation companions, SDK message/session history, pending mutations, cursor bindings and the server session, then return only `authentication_required`. A competing expiry request waits for the lock and treats an already-empty terminal state idempotently; it must not recreate history or metadata. Do not reimplement unrelated U1 behavior or change other Units. After implementation, write and run the R-17 lifecycle tests before proceeding. **Trace:** R-17; BR5.7; NFR2.6; SEC-U1-13; PIPE-U1-06; FR5.3, FR5.4.
- [ ] **18. Add the deterministic cross-execution barrier regression and refresh evidence.** Add a controllable FakeModel/Runner history-write barrier and fake UTC clock that starts a second expiry request while the first Runner is writing history. Assert the expiry request blocks on the shared lock; the first request performs the post-Runner persisted-expiry check before correlation/mapping/fallback/publication; the generated reply/result is discarded; cleanup commits zero SDK message rows, zero SDK session rows, zero presentation companion rows, zero pending rows, zero cursor rows and zero server-session rows; both the initial and waiting request produce no success response, presentation publication or later metadata regeneration. Run the U1-scoped lifecycle/integration command, then the exact full regression and coverage command, and update `code-summary.md`, `traceability.json` and the cumulative source manifest with R-17 results without weakening any prior assertion or coverage floor. **Trace:** R-17; BR5.7; NFR2.6; AC4.1.4, AC4.1.5; AC5.1.2, AC5.1.4.
- [x] **19. Revalidate the corrected U2 create-refresh rejection ownership.** Preserve production behavior and strengthen the existing gateway/capability tests so a same-process second invocation and a restart replay are rejected by the durable U2 claim before the U1 port (`U1 call 0`), while each first-call tamper·expiry·actor/create-attempt mismatch enters the U1 verifier exactly once, performs token exchange 0 times and leaves session credential generation unchanged. Re-run focused and full verification without weakening any prior assertion. **Trace:** NFR2.7; PIPE-U1-13; BR1.8.

## Test File Plan

| Test file | Component / boundary | Planned volume and focus |
|---|---|---|
| `tests/test_ticket_models.py` | strict DTO/schema | 5~8+ parameterized cases for exact fields, modes, enums, bounds, serialization and forbidden secret fields |
| `tests/test_ticket_repositories.py` | state/history repositories | 5~8+ cases per logical repository for binding, atomic invalidation, once-only resolution, persistence, clear and orphan cleanup |
| `tests/test_ticket_gateway.py` | HTTP adapter/capability | 5~8+ cases per list/detail/error boundary; query encoding, auth choice, timeout/status mapping and canaries |
| `tests/test_ticket_operations.py` | business orchestration | 5~8+ cases per list/detail/retry-cursor concern; virtual sleep/clock and exact attempt assertions |
| `tests/test_ticket_registry.py` | tool/mapper extension contracts | 5~8 cases for assembly, duplicate rejection, later extension and SDK schema secrecy |
| `tests/test_ticket_presentation.py` | correlation/API/UI fallback | 5~8+ cases for exact message binding, versions/kinds, escaping, accessibility text and fallback |
| `tests/test_ticket_read_integration.py` | FakeModel/MockTransport vertical slice | 5~8+ happy/failure/security flows including list, detail, refresh, 404, 429 and network denial |
| `tests/test_ticket_lifecycle.py` | concurrency and lifecycle | 5~8+ cases for pre-Runner locking, interleaving, restart, clear, switch/logout/expiry and idempotence, plus the R-17 Runner-history-write/expiry-request barrier regression with terminal row and publication counters |
| `tests/test_network_isolation.py` | process-level outbound default deny | deliberate fresh AsyncClient and raw-socket bypass probes that fail before DNS/socket I/O, plus blocker installation evidence |

The repair pass extends those owned files rather than creating a parallel implementation: `test_ticket_gateway.py` and `test_ticket_operations.py` cover strict `read_for_update`; `test_ticket_repositories.py` and `test_ticket_lifecycle.py` cover additive expiry migration and pre-capability cleanup; `test_ticket_operations.py` covers the 100,000-reference quality contract; and `test_ticket_lifecycle.py` proves both the full pre-Runner lock interval and R-17 cross-execution barrier with post-Runner result discard and terminal zero-row cleanup.

The parameter matrix may produce more pytest cases than the row counts; it may not reduce any contract boundary named above merely to stay within a numeric estimate.

## Completion Criteria

- The exact U1 scoped command passes with no live OpenAI/ITSM request.
- The complete existing-plus-new pytest suite passes and the exact changed application paths claimed by the U1 source manifest have line coverage of at least 80%; no second U1 whole-application threshold is introduced.
- All ticket HTTP requests observed in tests use only the current user's delegated token; service-token ticket requests, leaked secret canaries and raw upstream cursors are each 0.
- List/detail filters, cursor binding, retry caps, 429 behavior, safe projection and 404 non-disclosure match the approved contracts.
- The conversation lock begins before Runner; concurrent requests cannot mis-correlate presentation metadata.
- `confirm` and `consume_once` are separate CAS transitions; successful consumption returns exactly `{mutation_id, confirmed_at}` once, grants no transport authority, and U1 cleanup never changes U2 ledger row/key/bytes. A consume-before-bind crash requires a new review and confirmation with unbound POST/PATCH counts at 0.
- `TicketOperations` owns the 60-second credential preflight and shared one-shot refresh budget before invoking the one-attempt gateway. Preflight failure makes 0 ticket HTTP calls, and preflight success followed by 401 never performs a second refresh.
- U2 create-refresh rejection ownership is measured by case: durable second invocation/restart replay has U1 port calls 0; first-call tamper·expiry·actor/create-attempt mismatch has U1 verifier calls 1 and token exchanges 0; every rejection leaves session credential mutation at 0.
- Protected chat, Runner/SDK history, presentation commit and session-expiry cleanup use the same per-conversation lock. A deterministic barrier proves a competing expiry request waits, post-Runner expiry is checked before any response/presentation decision, the generated result is discarded, cleanup leaves SDK messages/session, presentation, pending, cursor and server-session rows at zero, and no success reply/metadata is published or recreated.
- The exported server-only `read_for_update` port accepts only a strong quoted-decimal ETag equal to the public version; every invalid form returns `upstream_unavailable` and causes 0 update-review/PATCH calls.
- Persisted session expiry is absolute at creation plus 8 hours across activity, token refresh and restart; expired or untrustworthy legacy sessions are cleaned before capability/Runner/ITSM work while the physical session schema remains otherwise unchanged.
- The prior release's session create/restore/login/logout writes succeed on the migrated DB through the epoch default, and a forward redeploy treats old-version epoch rows as expired without touching the U2 durable ledger.
- A process-level default-deny fixture blocks deliberate AsyncClient and raw-socket bypass probes before DNS/socket I/O; the release evidence records unregistered network attempts and no live OpenAI/ITSM access occurs.
- A 100,000-reference quality run has zero collisions and exposes neither raw cursors nor sequential/timestamp-only references; production entropy is at least 128 bits from the OS CSPRNG.
- Legacy text-only chat/history rows and unsupported presentation metadata degrade to existing text behavior.
- Existing user switch, session, history clear, fixed model/reasoning, tracing and UI/API behavior remain green.

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
      "text": "- R-17은 runtime infrastructure 추가가 아니라 기존 promotion gate에 deterministic concurrency evidence를 추가하는 변경으로 해석했다. barrier event, direct row count, response/publication counter가 blocking evidence다. (learned 2026-10-25) \n\n- 테스트는 시간 기반 flaky race 대신 controllable Runner history-write barrier와 fake clock을 사용한다. 실제 경쟁 순서를 결정적으로 고정하면서 production lock 경계를 그대로 통과시킨다. (learned 2026-10-25)"
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
  "input_sha256": "sha256:fcecf32258c5914e3e108c4075f798c69291307ca1bfa3bb7404c5a69f82ee8c",
  "contract_sha256": "sha256:1235ba2ccd7f6cbd2f1e8ab12b647bf8067dd7430a737582b4a5659cd9d7da43"
}
```
