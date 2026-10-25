# U3 Ticket Update — 기술 스택 결정

## Sources

- `construction/u3-ticket-update/functional-design/functional-spec.md` — update workflow, optimistic lock, durable execution 초안과 crash recovery
- `construction/u3-ticket-update/functional-design/rules.md` — confirmation, patch/version binding, recovery와 trust rules
- `inception/requirements-analysis/requirements.md` — fixed stack constraints, NFR1~NFR9, coverage and network isolation
- `inception/contract-design/contract-summary.md` — shared V1 ports, C-02 update extension, C-05 verification contract
- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md` — installed runtime and quality-tool baseline
- `construction/u3-ticket-update/nfr-requirements/nfr-requirements-questions.md` — confirmed no-new-infrastructure, durable publication and recovery direction

## Decision Summary

| Decision | Selection | Rationale | NFR linkage |
|---|---|---|---|
| Runtime | Existing Python 3.13 | Preserves project conventions and avoids a second runtime or service | NFR5.1 |
| HTTP/API boundary | Existing FastAPI 0.162.0, Pydantic 2.14.1, Starlette 1.10.0 | Reuses current server-session dependency injection, closed schemas and same-origin browser contract | NFR1.1, NFR2.1, NFR5.1 |
| Agent integration | Existing `openai-agents` 0.24.0 `Agent`, `Runner`, and `function_tool` | Adds only `ticket_update` to the current loop without a new Agent or custom loop | NFR5.1, NFR9.1 |
| ITSM transport | Existing httpx 0.28.1 `AsyncClient` and `MockTransport` | Supports one-attempt PATCH, timeout enforcement, exact `If-Match` tests and live-network isolation | NFR3.1, NFR3.4, NFR6.2, NFR7.1 |
| Validation | Existing Pydantic/dataclass boundary plus explicit canonical patch serialization | Enforces additional-properties false and omit/null semantics while supporting deterministic hash verification | NFR1.3, NFR3.2, NFR3.3 |
| Confirmation authority | U1 `PendingMutationRepositoryV1` atomic confirm+`consume_once` evidence plus exact matching U3 active execution | Keeps revocable confirmation in U1 while U3 owns only durable execution material; neither record alone authorizes PATCH | NFR2.2, NFR2.3, NFR3.3 |
| Durable execution persistence | U3-owned `ticket_tools_update_v1.pending_update_executions` in the existing server-session SQLite database | C-02/C-05 now define owner, exact fields, migration order, lifecycle cleanup and U4 verification without a new database or service | NFR3.3, NFR3.8, NFR3.9, NFR3.10 |
| Revise arbitration | U1 `replace_update_pending(expected_old, replacement)` transaction plus U3 staged-first/active-CAS publication | Preserves the old review on validation or replacement failure and gives concurrent confirm/revise a deterministic single winner | NFR3.7, NFR3.8 |
| Update credential refresh | U3 durable `UpdateCredentialRefreshReservationV1` plus U1 `UpdateCredentialRefreshPortV1` | Allows the single authoritative no-apply 401 continuation while preventing a second refresh across crash or response loss | NFR3.4, NFR3.6, NFR7.1 |
| Testing | Existing pytest 9.1.1, FakeModel, `httpx.MockTransport`, FastAPI TestClient, fake clock/barriers/restart snapshots | Deterministic contract, concurrency, lifecycle, security and regression evidence without external calls | NFR5.1, NFR6.1, NFR6.2 |
| Browser presentation | Existing build-free JavaScript, HTML and CSS | Preserves current keyboard, screen-reader, landmark and live-region behaviour without a new UI | NFR9.1 |

## Optimistic-Lock and Recovery Decisions

- U1 alone parses the detail response ETag and emits `IfMatchVersion`; U3 never derives or rewrites it from a number.
- Prepare/revise rejects missing, weak, non-decimal or body-version-mismatched ETags before review publication.
- Confirm requires current-turn evidence, every actor/target/patch/version binding, U1 consume-once evidence and exact canonical execution data.
- PATCH uses one `update_ticket_once` call by default. U3 `TicketOperationPolicyV1` owns one confirmation-execution counter; only an authoritative no-apply `token_expired` 401 may consume a one-shot refresh and a second `update_ticket_once` call with identical patch/version. The total is at most two, and no retry library, decorator, httpx transport retry or reconciliation loop may add another call.
- 412/428 and ambiguous transport outcomes switch to `read_ticket_once`; only complete expected changes plus an advanced version permit success.
- A typed 401 recall is allowed only when the authoritative ITSM contract guarantees no application; it consumes the existing one-shot credential refresh budget and does not establish a general PATCH retry policy.
- U3는 active execution에 `UpdateCredentialRefreshReservationV1`을 먼저 reserve하고 U1 `UpdateCredentialRefreshPortV1`을 한 번만 호출한다. Session credential commit 뒤 응답 유실은 credential generation 비교로 복구하며 port를 재호출하지 않는다.
- 429 returns immediately with a validated `Retry-After`; it does not sleep.

## Approved Persistence and Publication Boundary

- U3 owns `PendingUpdateExecutionV1` in the existing server-session SQLite database under namespace `ticket_tools_update_v1`, table `pending_update_executions`; U3 owns its migration and never writes U1 or U2 namespaces.
- Migration order is U1 `ticket_tools_state_v1` first, then U3 `ticket_tools_update_v1`, then U3 plugin activation. Missing or failed migration prevents plugin/PATCH activation.
- The row preserves immutable mutation and actor binding, ticket/base version, serialization version 1, compact fixed-key-order canonical patch bytes, SHA-256, server-only validated `IfMatchVersion`, `staged|active|retired` status and lifecycle timestamps. Credential, Authorization, raw headers and raw problem details are forbidden.
- U1 owns `replace_update_pending(expected_old_mutation_id_or_null, replacement)`. One U1 transaction verifies the exact expected-old actor/operation/pending binding, invalidates exactly that row and inserts the replacement; rejection changes neither row and never writes U3 storage.
- Publication order is U3 staged row, U1 exact-old replacement, then one U3 transaction that CAS-retires the exact old active execution when present and promotes the exact new staged row. Actor scope active partial unique index와 exact binding이 active row를 최대 하나로 제한하며 crash recovery도 같은 transaction 조건을 사용한다.
- U1 terminal or missing pending makes the U3 row immediately non-authorizing. U3 cleanup is idempotent on access, startup and lifecycle events, with terminal deletion only after the existing session-state cleanup window.
- Review-response loss uses an internal exact actor/session/conversation/ticket active-row locator, then revalidates every U1 binding. It restores the same pending reference only; version drift returns conflict and requires revise/cancel without PATCH.
- C-05/U4 verification covers round-trip, migration order, replacement rollback, exact-old invalidation, concurrent confirm/revise, staged orphan cleanup, activation crash recovery, terminal cleanup, response-loss isolation, tamper rejection and server-only-field leakage.

## Canonicalization and Cryptography

| Concern | Decision | Acceptance condition |
|---|---|---|
| Patch encoding | Versioned compact UTF-8 JSON over validated allowed fields with a fixed key order; omitted fields absent and explicit null retained | Re-serialization is byte-identical for the same logical patch |
| Patch integrity | SHA-256 over exact canonical bytes, recomputed before any PATCH | Mismatch produces zero network calls |
| Pending binding | Separate normalized patch hash bound with operation, actor, ticket and base version | every mismatch rejects confirmation |
| Pending reference | Operating-system CSPRNG opaque identifier with at least 128 bits of entropy | value is not authority and is safe to expose as a correlation reference |
| Time | Injected UTC clock for 15-minute expiry and recovery tests | restart and boundary tests are deterministic |

No new cryptographic dependency is selected. Python standard-library hashing and operating-system randomness are sufficient; credentials and `IfMatchVersion` remain server-only.

## Reliability and Concurrency Decisions

| Case | Required state decision | Observable bound |
|---|---|---|
| Invalid/forbidden/no-op patch | no executable review | PATCH 0 |
| Invalid ETag/version pair | no executable review | PATCH 0 |
| Cancel/expiry/lifecycle before consume | pending invalid | PATCH 0 |
| Two exact confirms race | U1 consume-once admits at most one evidence owner | PATCH owner ≤1 |
| First PATCH returns authoritative no-apply `token_expired` 401 | one refresh and one identical continuation under the same execution counter | PATCH total ≤2, refresh ≤1 |
| PATCH returns 412/428 | conflict then latest-detail read | automatic PATCH resend 0 |
| PATCH timeout/transport ambiguity | ambiguous then latest-detail read | automatic PATCH resend 0 |
| Latest detail proves all expected changes and version advance | success may be emitted | authoritative evidence required |
| Latest detail proves partial/different/no change | old authority invalid; new review required if diff remains | success 0 |
| Latest detail cannot be read | terminal/current ambiguous guidance | success 0, additional PATCH 0 |
| Revise publication or process restart | staged-first, exact-old U1 replacement, active CAS and exact-binding recovery | old review preserved on rejection; mismatch PATCH 0 |
| Review response lost after active promotion | exact actor/session/conversation/ticket locator plus U1 rebinding | same pending only; version drift PATCH 0 |

## Verification Tooling Decisions

- Keep pytest as the runner and existing fixture/parametrize/direct-assert conventions.
- Use FakeModel for Agent tool-loop scenarios and `httpx.MockTransport` for every ITSM request.
- Inject fake UTC clock, deterministic randomness, gateway outcomes, lifecycle events, process-restart snapshots and controllable confirm/revise barriers.
- Capture exact PATCH bytes, `If-Match`, Authorization source category and call counts without exposing credential values.
- Use the already pinned `coverage==7.17.0` and repository-owned `scripts/changed_line_coverage.py`; do not add Ruff, Black, mypy or another mandatory quality tool.
- Re-run the documented 37-test baseline before implementation, layer tests after each implementation layer, and the full suite plus changed-code coverage at completion.

### Reproducible changed-code coverage contract

- Resolve the Unit baseline once as the merge base of Unit `HEAD` and `main`.
- Measure executable Python statement lines under `app/**/*.py`; exclude tests, lifecycle artifacts, virtual environments, vendor and generated content.
- Intersect added/modified destination lines from a zero-context git diff with `coverage.py` JSON `executed_lines ∪ missing_lines`.
- Require covered changed executable lines divided by total changed executable lines to be at least 80%.
- Record the exact base commit, included files, covered/total line counts and percentage; an empty denominator is valid only when no application code changed and cannot complete expected U3 implementation.

Run from the Unit worktree root:

```bash
aidlc_cov_base=$(git merge-base HEAD main)
coverage erase
coverage run --branch --source=app -m pytest
coverage json -o coverage.json
python scripts/changed_line_coverage.py --base "$aidlc_cov_base" --coverage-json coverage.json --include 'app/**/*.py' --fail-under 80
```

`requirements.in` and `requirements.txt` pin `coverage==7.17.0`. `tests/test_changed_line_coverage.py` must pass with the rest of the suite and covers changed hunks, new/deleted files, non-executable lines, path normalization and the 80% boundary.

## Rejected Alternatives

| Alternative | Reason rejected |
|---|---|
| Let U1 write `ticket_tools_update_v1.pending_update_executions` | violates single-owner storage boundaries and couples the U1 transaction to U3 persistence |
| Replace exact-old `replace_update_pending` with selector invalidation | can invalidate the wrong or newly inserted row and cannot preserve stale-review safety |
| Invalidate old pending then call `put` | a `put` failure destroys the still-valid old review and violates revise failure semantics |
| Call `put` then selector-based `invalidate` | existing selector can invalidate the newly created row as well and does not provide atomic publication |
| Reconstruct patch or `If-Match` from review/model/history on confirm | loses authoritative omission/null and ETag provenance and permits tampering |
| Keep execution data only in process memory | fails across process restart and cannot support the claimed durable confirmation semantics |
| New service, queue, distributed lock, cache or database | outside scope and unnecessary once the existing SQLite ownership contract is explicitly resolved |
| Hidden PATCH retry | violates FR6.4/C-05 and can duplicate or overwrite an uncertain update |

## Implementation Preconditions

- Verify the consumed C-02/C-05 fingerprint still contains U1 `replace_update_pending`, U3 `PendingUpdateExecutionV1`, migration order, lifecycle cleanup and U4 verification obligations before implementation starts.
- Apply U3 migration only after U1 `ticket_tools_state_v1` is ready and before registering the U3 plugin; any migration or schema mismatch fails activation closed.
- Contract tests must prove exact patch/`IfMatchVersion` round-trip, atomic replacement rollback, exact-old invalidation, active CAS, response-loss locator isolation, concurrent confirm/revise arbitration, lifecycle cleanup and restart recovery.
- Code Generation must stop on contract drift or missing ownership evidence; it may not approximate atomicity with multiple U1 calls, selector invalidation or process memory.
