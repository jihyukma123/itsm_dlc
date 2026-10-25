# U2 Ticket Write — Unit Test Instructions

## Preconditions

- 저장소 루트 `/Users/jihyukma/Documents/c/itsm_dlc`에서 실행한다.
- 프로젝트 `.venv`와 pinned dependencies를 사용한다. 새 test runner, formatter, linter 또는 type checker를 추가하지 않는다.
- 모든 model behavior는 FakeModel, 모든 ITSM traffic은 `httpx.MockTransport`, 모든 시간·randomness·경쟁 순서는 fake clock/CSPRNG/barrier를 사용한다.
- Process-level network default-deny fixture가 등록되지 않은 DNS와 동기·비동기 TCP를 차단해야 한다. 실제 OpenAI·ITSM credential은 필요하지 않으며 사용하면 실패다.
- 테스트 데이터의 ticket ID, actor ID, key와 request bytes는 각 case에서 생성한다. 실제 또는 샘플 운영 티켓 ID를 제품 코드·prompt·fixture에 하드코딩하지 않는다.

## Runner and Configuration Readiness

첫 production 변경 전에 기존 pytest discovery, fixture와 runner가 동작하는지 이 exact-file command로 확인한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_models.py tests/test_ticket_repositories.py tests/test_ticket_gateway.py tests/test_ticket_registry.py tests/test_network_isolation.py
```

이 command가 실패하거나 live network가 필요하면 구현을 시작하지 않는다. U2는 기존 `pytest.ini`, coverage dependency와 autouse network blocker를 재사용하므로 별도 test configuration 파일을 만들지 않는다.

## Layer Commands

`test-after` 순서에 따라 각 production layer 구현 직후 대응 test를 작성하고 아래 command를 실행한다.

### Models and canonical serialization

```bash
.venv/bin/python -m pytest -q tests/test_ticket_create_models.py
```

필수 검증: strict action/draft shape, unknown field 거부, 모든 길이·enum·timezone 경계, ID-or-name selector, explicit-now single capture, default materialization, optional omission, deterministic compact UTF-8 bytes/hash, public schema/result의 secret-like field 0건.

### SQLite migration and create-attempt repository

```bash
.venv/bin/python -m pytest -q tests/test_ticket_create_repository.py tests/test_ticket_repositories.py tests/test_ticket_lifecycle.py tests/test_session.py
```

필수 검증: U2 table만 추가, ledger-before-pending failure injection, actor-scope prepared uniqueness, evidence bind idempotence, retention monotonicity, send/recovery/refresh CAS winner ≤1, active claim non-takeover, stale outcome write 0, concurrent refresh reservation owner ≤1, exact 24-hour cleanup boundary, switch/logout/clear/expiry 뒤 ledger 보존. `tests/test_ticket_repositories.py`의 legacy helper/fixture는 공식 additive U2 schema를 사용하되 기존 U1 assertions의 의미를 변경하지 않는다.

### Catalog and one-attempt create gateway

```bash
.venv/bin/python -m pytest -q tests/test_ticket_gateway.py tests/test_ticket_create_models.py
```

필수 검증: active unique catalog match, service/component relation, delegated bearer 100%, exact stored bytes and original idempotency key, one gateway call = one HTTP attempt, per-attempt timeout, created/replayed ticket-ID evidence, malformed success, 401/403/422/429/5xx/timeout/response-loss safe mapping, raw detail/header/credential 노출 0. C-01 provider와 consumer는 같은 fixture로 contract-defined `CredentialRefreshReservationV1` required/optional fields와 `Result[TicketRequestCapability, SafeErrorV1]` 성공·safe failure를 검증한다.

### Create operation policy

```bash
.venv/bin/python -m pytest -q tests/test_ticket_create_operations.py tests/test_ticket_create_repository.py
```

필수 검증:

- Prepare/revise commit order, orphan prepared authority 0, stale review execution 0.
- Exact current raw turn 외 confirmation에서 POST 0; U1 consume evidence 없거나 bind 전 crash이면 동일 attempt/key/bytes 재검토와 새 확인 필요.
- Every POST 전에 count increment와 send claim commit; competing caller 중 POST owner ≤1.
- Send deadline은 claim 획득 시 한 번 capture한 UTC now에 `ITSM_TIMEOUT_SECONDS + 1초`를 더해 저장하며 deadline 전 takeover 0.
- Transport/reconciliation outcome은 exact claim ID로 fence되고 late stale write는 0.
- Ambiguous에서 direct POST 0; recovery claim 뒤 budget이 남을 때만 `retryable_after_reconcile`.
- Durable reservation 뒤 refresh invocation/exchange ≤1; commit 전/후 crash 모두 second refresh 0.
- Reservation CAS 직후 process-local active registry에 등록하고 durable outcome 기록 뒤 제거한다. Same-boot observer는 registry entry 존재 여부와 관계없이 write·recovery·refresh 0건이며, creator boot가 다른 restart만 stored generation 비교 CAS를 수행한다. Commit-before-registry, owner cancellation, same-boot missing-registry, different-boot restart를 각각 검증한다.
- Initial, refresh, reconciliation을 합친 POST ≤2; 모든 attempt의 key와 bytes가 동일; third POST 0.
- Authoritative ticket ID 없는 completed/success 0; 429 sleep/retry 0.

### Function tool, registry and presentation

```bash
.venv/bin/python -m pytest -q tests/test_ticket_write_tool.py tests/test_ticket_registry.py tests/test_ticket_presentation.py
```

필수 검증: exact `ticket_write` name, prepare/confirm/revise/cancel schema, model-visible secret field 0, existing registry implementation 불변, U2 mapper key resolution, complete review choices `확인`/`수정`/`취소`, accessible text for every state, external text가 control state를 바꾸는 사례 0.

### Agent/runtime integration and lifecycle

```bash
.venv/bin/python -m pytest -q tests/test_ticket_write_integration.py tests/test_ticket_lifecycle.py tests/test_agent.py tests/test_session.py
```

필수 검증: current server-session capability, same conversation lock and Runner, FakeModel tool loop, review→exact confirmation→POST→presentation/history, process-lifetime active refresh registry의 production 조립, restart recovery, old-user isolation, pending invalidation with ledger retention, fixed model/reasoning/tracing, existing chat/history/text fallback 회귀.

### Security, network isolation and coverage helper

```bash
.venv/bin/python -m pytest -q tests/test_ticket_create_security.py tests/test_network_isolation.py tests/test_changed_line_coverage.py
```

필수 검증: distinct secret canary가 model/tool/API/presentation/log/stdout/stderr/traceback/assert diff에 0건, unregistered AsyncClient와 raw socket은 DNS/TCP 전 차단, malicious external text는 data로만 남음, coverage helper가 added/modified/renamed/deleted/non-executable lines와 80% 경계를 정확히 판정함. Helper는 approved plan의 Planned Source Set과 Unit source manifest를 함께 읽어 U2 claim만 측정하고, approved changed path 누락과 out-of-plan claim은 실패시키며 다른 Unit/기존 source change는 별도 집계한다.

## Exact U2-Scoped Verification Command

Build and Test가 Unit별로 재실행할 exact-file command다. Repository 전체 suite로 대체하지 않는다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_create_models.py tests/test_ticket_create_repository.py tests/test_ticket_repositories.py tests/test_ticket_create_operations.py tests/test_ticket_write_tool.py tests/test_ticket_write_integration.py tests/test_ticket_create_security.py tests/test_changed_line_coverage.py tests/test_ticket_gateway.py tests/test_ticket_registry.py tests/test_ticket_presentation.py tests/test_ticket_lifecycle.py tests/test_agent.py tests/test_session.py tests/test_network_isolation.py
```

Pass conditions:

- 선택된 test가 모두 통과하고 새 skip/xfail이 없다.
- 실제 OpenAI·ITSM network call = 0; deliberate bypass probe만 차단 event를 남긴다.
- Delegated-token ticket POST 비율 = 100%, service-token ticket POST = 0.
- Pending-without-ledger committed state, unbound POST, active-claim takeover, stale outcome overwrite, second refresh, third POST, false success, premature ledger deletion이 각각 0건이다.
- Same attempt의 모든 POST body/key가 byte-identical하고 POST count는 최대 2다.
- Credential, Authorization, client secret, OpenAI key, idempotency key, canonical bytes와 raw upstream detail canary 노출이 0건이다.

## U2 Changed-Line Coverage

Exact U2-scoped tests로 coverage JSON을 만들고 merge-base 이후 U2가 변경한 `app/**/*.py` executable lines를 판정한다.

```bash
aidlc_cov_base=$(git merge-base HEAD main)
.venv/bin/python -m coverage erase
.venv/bin/python -m coverage run --branch --source=app -m pytest -q tests/test_ticket_create_models.py tests/test_ticket_create_repository.py tests/test_ticket_repositories.py tests/test_ticket_create_operations.py tests/test_ticket_write_tool.py tests/test_ticket_write_integration.py tests/test_ticket_create_security.py tests/test_ticket_gateway.py tests/test_ticket_registry.py tests/test_ticket_presentation.py tests/test_ticket_lifecycle.py tests/test_agent.py tests/test_session.py tests/test_network_isolation.py
.venv/bin/python -m coverage json -o coverage.json
.venv/bin/python scripts/changed_line_coverage.py --base "$aidlc_cov_base" --coverage-json coverage.json --source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/code-generation/source-manifest.json --prior-source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/code-generation/source-manifest.json --approved-plan aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/code-generation/code-generation-plan.md --source-baseline aidlc/spaces/default/intents/261024-itsm-ticket-tools/.aidlc-engine/source-review/code-generation/baseline-6532efa31d44.tsv --include 'app/**/*.py' --fail-under 80
```

Helper는 base commit, U2 source manifest, 선행 U1 source manifest, approved plan, engine의 Code Generation stage-entry source baseline, 다른 Unit/기존 변경으로 제외한 path 수, 포함된 U2 files, covered/total changed executable lines와 percentage를 출력해야 한다. Denominator는 이번 stage에 변경되었고 U2 manifest가 claim하며 승인 계획에도 있는 application source로 제한한다. 승인 계획의 이번-stage changed application path가 manifest에서 누락되거나 manifest가 승인 밖 application path를 claim하면 실패한다. 승인 source set 밖에서 baseline 이후 변경된 path가 선행 Unit manifest에도 없으면 실패한다. 선행 Unit manifest가 claim한 path와 baseline 이전 기존 변경은 U2 분모에서 제외해 별도 집계한다. Stage baseline은 content hash listing이므로 공유 파일 내부에서는 merge-base 이후 executable lines 전체를 보수적으로 측정한다. U2는 application code를 변경하므로 empty denominator는 실패다. Coverage가 80% 미만이면 정당한 tests 또는 helper defect를 수정하며 threshold, source scope, branch mode를 낮추지 않는다.

최신 Code Generation 실행 evidence: base `89f48f9372635f443c719b7d64ca6900585bb112`, prior manifest 1개와 stage baseline `baseline-6532efa31d44.tsv` 적용, 다른 Unit/기존 application change 11개 분리, U2 manifest-bound changed executable lines `1401/1568 (89.35%)`, exit 0.

Repository-wide regression과 전체 application coverage는 Unit-only command가 아니므로 이 파일에 반복 실행 명령을 두지 않는다. Code Generation 마지막 gate와 Build and Test는 workflow에 기록된 construction verification command를 별도로 실행하고 그 결과를 U2 evidence와 함께 판정한다.

## Test Data and Isolation

- 각 test는 isolated temporary SQLite DB를 사용하며, restart case는 DB file을 복사하거나 새 repository instance로 다시 연다.
- Injected UTC/monotonic clock이 confirmation expiry, claim deadline, refresh deadline과 retention 경계를 제어한다. Wall-clock sleep으로 race를 만들지 않는다.
- Injected deterministic randomness는 test-only attempt/claim/reservation/key 값을 제공한다. Production path는 OS CSPRNG 128-bit 이상을 사용한다.
- Concurrency tests는 barrier event와 affected-row/POST/refresh/publication counters를 사용한다. Timing-based flaky assertion은 금지한다.
- MockTransport는 request body와 headers를 assertion 동안만 관찰하고 failure output에는 raw token, key 또는 canonical bytes를 넣지 않는다. Equality/digest/count만 출력한다.
- Catalog labels, ticket text와 problem data에는 HTML/Markdown control, fake confirm, identity/permission/tool/retry 지시문을 주입해도 data boundary를 벗어나지 않아야 한다.

## Failure Recording

실패한 exact command, test node, safe error category, affected-row/attempt counter와 repair를 `code-summary.md`에 기록한다. Credential, Authorization, key, canonical bytes, raw body/header/problem detail, exception text 또는 secret canary 원문은 artifact에 복사하지 않는다. 실행하지 못한 test가 있으면 이유와 필요한 prerequisite를 별도 목록으로 남기며 CI에서 실행된 것으로 주장하지 않는다.
