# U2 Ticket Write — 기술 스택 결정

## Sources

- `construction/u2-ticket-write/functional-design/functional-spec.md` — create workflow, ledger, gateway and presentation boundaries
- `construction/u2-ticket-write/functional-design/rules.md` — deterministic serialization, confirmation, attempts and trust rules
- `inception/requirements-analysis/requirements.md` — fixed stack constraints, NFR1~NFR9, coverage and network isolation
- `inception/contract-design/contract-summary.md` — shared V1 ports, `ticket_create_attempts`, retry and result contracts
- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md` — installed runtime and quality-tool baseline
- `requirements.in`, `requirements.txt` — current project dependency pins, including `coverage==7.17.0`
- `construction/u2-ticket-write/nfr-requirements/nfr-requirements-questions.md` — confirmed no-new-infrastructure and contract-compatible direction

## Decision Summary

| Decision | Selection | Rationale | NFR linkage |
|---|---|---|---|
| Runtime | Existing Python 3.13 | Preserves project conventions and avoids a second runtime or service | NFR5.1 |
| HTTP/API boundary | Existing FastAPI 0.162.0, Pydantic 2.14.1, Starlette 1.10.0 | Reuses current server-session dependency injection, response models, and same-origin browser contract | NFR1.1, NFR2.1, NFR5.1 |
| Agent integration | Existing `openai-agents` 0.24.0 `Agent`, `Runner`, and `function_tool` | Adds `ticket_write` to the current loop without a new Agent or custom loop | NFR5.1, NFR9.1 |
| ITSM transport | Existing httpx 0.28.1 `AsyncClient` and `MockTransport` | Supports one-attempt gateway calls, timeout enforcement, exact-byte request tests, and live-network isolation | NFR3.4, NFR6.2, NFR7.1 |
| Validation | Existing Pydantic/dataclass boundary plus explicit canonical serializer | Enforces closed schemas while keeping byte serialization versioned and independent of incidental model serialization | NFR1.3, NFR3.4 |
| Persistence target | Existing Server Session SQLite database and approved `ticket_tools_create_v1.ticket_create_attempts` | Provides ledger-first bytes, evidence binding, retry states, send claim deadlines, one-shot refresh generation evidence, claim fencing and minimum retention without an unapproved table or new infrastructure | NFR3.1, NFR3.2, NFR3.6, NFR3.8, NFR3.9, NFR3.10 |
| Concurrency target | Existing per-conversation Runner lock plus SQLite expected-state/claim-ID compare-and-set transitions | Serializes one process while durable claim identity·deadline and outcome fencing preserve safety across restart and competing callers | NFR2.2, NFR3.3, NFR3.4, NFR3.6 |
| Testing | Existing pytest 9.1.1, FakeModel, `httpx.MockTransport`, FastAPI TestClient, fake clock/randomness/barriers | Deterministic contract, concurrency, lifecycle, restart, security, and regression evidence without external calls | NFR5.1, NFR6.1, NFR6.2 |
| Browser presentation | Existing build-free JavaScript, HTML and CSS | Preserves current keyboard, screen-reader, landmark and live-region behaviour without a new UI | NFR9.1 |

## Contract-Aligned Ledger and Claim Decision

The reviewed Functional Design and C-01/C-04 now share one authoritative flow:

- Prepare/revise creates the C-04 `TicketCreateAttemptV1` row in `prepared` state before publishing the U1 pending review. It stores one server-only idempotency key and exact canonical bytes.
- Review replacement first terminalizes the previous evidence-free prepared row with expected-state CAS and invalidates the previous U1 pending binding. Only then may it create and publish the replacement.
- A `prepared` row is not execution authority. The public U1 `consume_once` result binds `confirmed_mutation_id` and `confirmed_at` idempotently to the unique actor·payload attempt.
- Each POST requires a new SQLite CAS that writes unique `claim_id`, `claim_deadline_at`, `in_flight`, and the incremented global attempt count before network I/O.
- A typed no-apply 401 uses `retryable_no_apply`; an uncertain result must be reconciled before `retryable_after_reconcile`. `ambiguous` never goes directly to another POST.
- Transport outcome writes compare `in_flight` plus the send claim ID. Reconciliation acquires one owner by Functional Design's expected-state/existing-claim-ID CAS and fences the reconciliation outcome with that same stored claim ID; no separate recovery identity or field is introduced. Late stale responses cannot overwrite the current state.
- Proactive expiry and `retryable_no_apply` share the Functional Design fields for one durable one-shot refresh reservation. The winner records base credential generation, used-at and `reserved` before invoking refresh. Concurrent same-process observers return the current state without a recovery write; only actual restart recovery compares the same-actor session generation, treating a higher generation as committed and the same/lower generation as failed without a second refresh.
- If a POST returns another authoritative no-apply 401 after the one-shot reservation is already used, Functional Design's expected send-claim fence and refresh guard produce its terminal authentication failure. Whether the repository records an internal intermediate `retryable_no_apply` state is an implementation detail; it cannot create another refresh or send authority, and no new repository transition is added here.
- Evidence binding extends `retained_until` to at least `confirmed_at + 24h`. An orphan prepared row retains no credential, is never model-visible, and has no execution authority.

This decision requires no additional table, no change to `ticket_tools_state_v1`, and no cross-owner transaction-participant method outside C-01.

## Canonical Serialization and Cryptography

| Concern | Decision | Acceptance condition |
|---|---|---|
| Body encoding | Version 1 compact UTF-8 JSON with declared field order and omitted absent optionals | Stored bytes equal every outbound body byte-for-byte |
| Body integrity | SHA-256 over exact stored bytes, recomputed before every call | Mismatch produces zero network calls |
| Payload binding | Separate normalized logical-payload SHA-256 bound to mutation and U1 pending state | confirmation rejects every hash mismatch |
| Idempotency key | Operating-system CSPRNG with at least 128 bits of entropy, generated once per mutation | one key per ledger identity; value never logged or model-visible |
| Time | Injected UTC clock; explicit now is captured once during prepare/revise | confirmation/retry never recaptures or changes `occurred_at` |

No new cryptographic library is selected. Python standard-library primitives and operating-system randomness are sufficient for hashing and key generation; secret storage remains the existing server-only process/session boundary.

## Reliability and Concurrency Decisions

| Case | State decision | Observable bound |
|---|---|---|
| Ledger write fails before U1 pending publication | no pending review | POST 0 |
| U1 pending publication fails after ledger commit | orphan `prepared`, non-authorizing | POST 0 |
| Revise races previous confirm | prior-row terminalization and evidence binding use conflicting expected-state CAS | exactly one path wins; stale POST 0 |
| Cancel/expiry/lifecycle before consume | U1 state invalid; matching prepared row cannot claim execution | POST 0 |
| Two exact confirms race | U1 consume-once and claim CAS admit at most one execution owner | one counted gateway invocation at a time |
| Successful consume | bind mutation ID/time and extend retention to `max(existing, confirmed_at + 24h)` before claim | confirmation-anchored durability |
| Crash before evidence bind | same attempt/key/bytes, new review and explicit confirmation required | unbound POST 0 |
| Crash after evidence bind before claim | bound evidence and prepared row are recoverable | no uncounted POST |
| Crash after CAS before deadline | active claim cannot be taken over | additional POST 0 |
| Claim deadline passes | expected-state/existing-claim-ID CAS admits one reconciliation owner and preserves the same claim identity fence | reconciliation before any new send claim |
| Pre-send expiry or token expiry with authoritative no-apply | durable one-shot refresh reservation with base generation, refresh once, committed generation evidence, then new same-budget send claim | refresh ≤1, total POST ≤2 |
| Refresh reservation owner is still live in the same process | competing caller observes `reserved` and returns current state without mutation | premature failure/recovery 0 |
| Process restarts with a reserved refresh | compare same-actor session generation once; higher means committed, same/lower means terminal failed | second refresh 0 |
| No-apply 401 after refresh already used | expected `in_flight` + current claim-ID fence leads to FD-U2-03 terminal authentication failure | additional refresh 0, additional POST 0 |
| 429 | immediate typed result | wait 0, automatic retry 0 |
| Timeout/transport/5xx uncertainty | durable ambiguous, then optional `retryable_after_reconcile` | success claims 0 without created/replayed ticket ID |
| Old claimant returns after newer claim | expected claim-ID mismatch | stale state writes 0 |

The existing application is single-process. No distributed lock or new coordination service is introduced. The durable SQLite CAS remains the cross-restart authority; the in-process conversation lock preserves ordering within the current deployment model.

## Verification Tooling Decisions

- Keep pytest as the test runner and existing fixture/parametrize/direct-assert conventions.
- Use FakeModel for Agent tool-loop scenarios and `httpx.MockTransport` for every ITSM request.
- Add a test network deny boundary so undeclared OpenAI/ITSM connections fail immediately.
- Inject fake UTC clock, deterministic CSPRNG output, catalog fixtures, gateway outcomes, lifecycle events, process-restart snapshots and controllable concurrency barriers.
- Use the already pinned `coverage==7.17.0` from `requirements.in`/`requirements.txt`; do not introduce Ruff, Black, mypy, or a new mandatory formatter/linter/type-checker.
- Re-run the documented 37-test baseline before implementation, layer tests after each implementation layer, and the full suite plus changed-code coverage at completion.

### Reproducible changed-code coverage contract

- Baseline commit: the merge base of the Unit branch `HEAD` and `main`, resolved once as `aidlc_cov_base=$(git merge-base HEAD main)` in the Unit worktree.
- Application scope: Python files under `app/**/*.py`. Exclude `tests/**`, `aidlc/**`, `.codex/**`, virtual environments, vendor content and generated files. Deleted lines are not part of the denominator.
- Measurement: `coverage.py` branch mode with `--source=app`; the JSON report's executable statement lines are `executed_lines ∪ missing_lines`.
- Changed-line set: added or modified destination line numbers in `git diff --unified=0 --no-ext-diff "$aidlc_cov_base" -- app`, including uncommitted Unit worktree changes. For a new file, all executable statement lines are eligible.
- Numerator: changed executable line numbers present in `executed_lines`. Denominator: changed line numbers present in `executed_lines ∪ missing_lines`. The threshold is `numerator / denominator >= 0.80`.
- A repository-owned `scripts/changed_line_coverage.py` must parse the diff and `coverage.json`, print base commit, included files, covered/total changed executable lines and percentage, and exit non-zero below 80%. An empty denominator is accepted only with an explicit audited statement that the Unit changed no `app/**/*.py`; that exception cannot complete U2 Code Generation, which is expected to change application code.

Run from the Unit worktree root:

```bash
aidlc_cov_base=$(git merge-base HEAD main)
coverage erase
coverage run --branch --source=app -m pytest
coverage json -o coverage.json
python scripts/changed_line_coverage.py --base "$aidlc_cov_base" --coverage-json coverage.json --include 'app/**/*.py' --fail-under 80
```

The script itself receives unit tests for modified lines, new files, deleted-only hunks, renames, non-executable lines, uncovered branches and the threshold boundary. Build and Test records the exact base commit and command output.

## Rejected Alternatives

| Alternative | Reason rejected |
|---|---|
| Add `prepared_create_payloads` | C-04 approves only `ticket_create_attempts`; another table changes the accepted storage contract and migration/test surface |
| Add a U1 transaction-participant API during U2 implementation | C-01 exposes independent pending operations and U1 owns that adapter; inventing the port bypasses contract ownership |
| Reconstruct canonical bytes on confirm | confirm forbids draft input and reconstruction can change defaults, time, encoding, or byte order |
| Keep bytes in conversation/model context | violates trust minimization and cannot be authoritative across turns or restart |
| New service, queue, distributed lock, cache, or database | outside scope and unnecessary for the single-process deployment and approved SQLite durability boundary |
| Hidden transport retry in gateway | breaks the one-call/one-attempt contract and makes the total cap unprovable |

## Implementation Preconditions

- NFR Design must quantify send-claim deadline derivation and specify how `begin_stale_claim_reconciliation` retains the existing `claim_id` as the single-owner and outcome fence without adding a recovery identity.
- NFR Design must specify the Functional Design refresh-reservation fields, same-process `reserved` observer behaviour, actual-restart generation recovery, and the CAS that marks the one-shot reservation used before refresh invocation; it must not add a refresh deadline field.
- NFR Design must specify how the existing expected send-claim fence and one-shot refresh guard realize FD-U2-03's terminal authentication failure after an already-used refresh, without inventing a repository operation or renewed execution authority.
- Contract tests must prove fail-closed review replacement, idempotent evidence binding, distinct retry states, shared total POST budget, existing-claim send/reconciliation outcome fencing, same-process live-refresh noninterference, restart recovery, and refresh invocation ≤1.
- If the existing U1 public repository cannot provide the documented `ConsumedMutationEvidenceV1`, implementation must stop and reopen Contract Design rather than add an undocumented method.
- Code Generation may proceed only against the reviewed ledger-first state machine and must not reintroduce a second table, cross-owner transaction API, ambiguous direct retry, or unfenced late outcome write.
