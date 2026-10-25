# U1 Ticket Read Skeleton — Unit Test Instructions

## Preconditions

- Run from the repository root: `/Users/jihyukma/Documents/c/itsm_dlc`.
- Use the project virtual environment and pinned dependencies.
- Tests must use FakeModel and `httpx.MockTransport`; no live OpenAI or ITSM credential is required or allowed.
- An autouse process-level network blocker must deny unregistered DNS/TCP entry points; MockTransport and in-process ASGI transport remain socket-free.
- Fixture ticket IDs must be generated for the test case. Do not copy a sample or operating ticket ID into product code, prompts or fixtures.

## Baseline Command

Run before production changes:

```bash
.venv/bin/python -m pytest -q
```

Expected pre-change reference: the documented existing 37 tests pass. If the observed count or result differs, stop implementation and record the discrepancy rather than rewriting the baseline.

## Layer Commands

Run each command immediately after implementing that layer and writing its test-after tests.

### Models and SQLite repositories

```bash
.venv/bin/python -m pytest -q tests/test_ticket_models.py tests/test_ticket_repositories.py
```

This layer must prove that `confirm` and `consume_once` are separate CAS transitions, successful consumption returns exactly `{mutation_id, confirmed_at}` once, repeat/mismatch/expiry returns no evidence, U1 cleanup leaves every U2 `ticket_tools_create_v1` row/key/canonical byte unchanged, and a consume-before-bind crash preserves the same attempt while requiring a new review and explicit confirmation with unbound POST/PATCH calls at 0.

### Capability, gateway and operations

```bash
.venv/bin/python -m pytest -q tests/test_ticket_gateway.py tests/test_ticket_operations.py
```

This layer must include the R-08 strict `read_for_update` matrix and the R-10 continuation-reference quality test:

- Only a strong quoted-decimal ETag exactly equal to the public ticket version returns `ReadForUpdateResultV1`.
- Missing, weak, non-decimal or mismatched ETags return `SafeErrorV1(upstream_unavailable)`; update review and PATCH call counts remain 0.
- Ordinary detail-read behavior remains unchanged and no ETag is serialized to the model or client.
- The production reference source is an OS CSPRNG with at least 128 bits of entropy behind an injectable boundary. A single test issues 100,000 references with zero collisions and no raw-cursor, sequential or timestamp-only output; weak injected sources are rejected.
- `TicketOperations` evaluates `credential_expires_at <= server UTC now + 60초` before calling the gateway and owns the shared one-shot refresh budget. Test 60초 ±1µs, preflight success, preflight failure with ticket HTTP count 0, preflight success followed by 401 with second refresh count 0, and a non-imminent first 401 with one refresh and one final attempt.
- U2 create refresh must separate rejection ownership exactly: a durable second invocation and restart replay stop before the U1 port with U1 call count 0; each first-call tamper·expiry·actor/create-attempt mismatch reaches the U1 verifier exactly once with token exchange count 0; every rejection keeps session credential mutation count 0.

### Tool registry and presentation

```bash
.venv/bin/python -m pytest -q tests/test_ticket_registry.py tests/test_ticket_presentation.py
```

### Runner integration and lifecycle

```bash
.venv/bin/python -m pytest -q tests/test_ticket_read_integration.py tests/test_ticket_lifecycle.py
```

This layer must include the R-09 absolute-expiry, correlation matrix and R-17 cross-execution serialization regression:

- The migration adds only `session_expires_at` to the existing physical session store and proves existing authentication, user, permission and delegated-credential fields retain their names, types, nullability and behavior.
- New expiry is exactly `created_at + 8h` and is not extended by activity, delegated-token refresh or restart.
- Legacy parseable creation times backfill to `created_at + 8h`; missing or malformed creation time fails closed as expired.
- Test `now < expiry`, `now == expiry` and `now > expiry`, including restart. Expired-state cleanup runs before capability creation and deletes pending/cursor state and the session before Runner/ITSM; cleanup failure also yields Runner/ITSM call counts of 0.
- Existing-session restoration, token refresh and user switching remain green.
- The migration shape is `session_expires_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z'`. Run the immediately prior release's session create, restore, login and logout/write fixture on the migrated database, then restart the new release and prove epoch-default rows fail closed as expired while U2 durable ledger rows remain unchanged.
- Protected chat and session-expiry cleanup resolve the same per-conversation lock. It is acquired before the authoritative persisted-expiry check and Runner, then held through Runner/SDK history access, the immediate post-Runner persisted-expiry check, correlation/presentation/response decision or terminal cleanup.
- A controllable Runner history-write barrier starts a competing expiry request while the first request is in Runner. The second request must remain waiting on the shared lock until the first reaches post-Runner expiry handling.
- Advance the fake UTC clock across `session_expires_at` during Runner. Before correlation, reply mapping, text fallback, presentation commit or response publication, the first request must detect expiry, discard the generated Runner result and clear presentation companion, SDK message/session history, pending mutation, cursor binding and server-session state under the lock.
- After committed cleanup, direct repository counts for SDK messages, SDK sessions, presentation companions, pending mutations, cursor bindings and server sessions are all 0. Success response count, presentation publication count and post-cleanup metadata/history regeneration count are all 0; only `authentication_required` is returned.
- Release the barrier and let the competing expiry request continue. It must treat the already-empty state idempotently and leave every zero-count and no-publication assertion unchanged.

## Exact U1-Scoped Verification Command

This is the unit-only runnable command. All named files are owned by U1 and may not silently fall back to the whole repository suite.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_models.py tests/test_ticket_repositories.py tests/test_ticket_gateway.py tests/test_ticket_operations.py tests/test_ticket_registry.py tests/test_ticket_presentation.py tests/test_ticket_read_integration.py tests/test_ticket_lifecycle.py tests/test_network_isolation.py
```

Pass conditions:

- Every selected test passes.
- No unexpected network request is allowed; all ITSM traffic is captured by MockTransport and all model behavior uses FakeModel. Deliberate fresh-AsyncClient and raw-socket bypass probes must fail with `UnexpectedNetworkError` before DNS/socket I/O and record the blocked-attempt count.
- Delegated-token ticket requests are observed, service-token ticket requests are 0, and secret-canary matches across model/tool/log/HTTP output are 0.
- Read attempts never exceed two; retry sleep is exactly one 250ms delay only for allowed transient failures; 429 sleep/retry counts are 0.
- The concurrency fixture proves the conversation lock is acquired before Runner and presentation metadata cannot bind to the wrong assistant item.
- The R-17 barrier fixture proves the expiry request waits on that same lock, the post-Runner persisted-expiry check precedes all correlation/mapping/fallback/publication, the Runner result is discarded, all six persisted state groups are empty after cleanup, and success reply/presentation publication or later metadata regeneration counts remain 0.
- Separate confirmation/consumption CAS, exact one-time evidence, U2 ledger preservation and consume-before-bind recovery pass with unbound mutation transport counts at 0.
- The 60-second preflight and reactive 401 fixtures share one refresh budget; preflight failure sends 0 ticket HTTP requests and no path refreshes twice.
- The U2 create-refresh fixture proves same-process second invocation and restart replay have U1 port calls 0, first-call tamper·expiry·actor/create-attempt mismatch has U1 verifier calls 1 and exchanges 0, and all rejection paths have session credential mutations 0.
- The strict `read_for_update` matrix passes and every rejected ETag produces update-review/PATCH call counts of 0.
- Absolute session expiry passes exact-boundary, restart, legacy-backfill, cleanup-failure, token-refresh and user-switch cases without changing the pre-existing physical session contract.
- The 100,000-reference issue test completes with zero collisions, zero raw cursor disclosures and zero sequential/timestamp-only references; weak entropy sources fail closed.

## Full Regression and Coverage

After the U1-scoped command succeeds, run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m coverage run --source=app -m pytest -q
.venv/bin/python -m coverage json --include='app/ticketing/*,app/db.py,app/session.py,app/itsm_auth.py,app/agent/*,app/main.py,app/schemas.py' --fail-under=80 -o coverage.json
```

The complete suite must pass and existing behavior must remain green. The JSON command is the sole U1 80% decision and its include list must match every changed Python application path in the final `source-manifest.json`; update the explicit list before the approved build completes if that manifest adds another application path. A report that measures none of the claimed paths fails. Do not lower the threshold, omit a claimed application file or enable live services to obtain a pass.

## Failure Recording

Record the exact failing command, test node, safe failure category and repair in `code-summary.md`. Redact credentials and upstream raw problem text; never paste Authorization values or secret canaries into the artifact.
