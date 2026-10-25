# U1 Ticket Read Skeleton — CI/CD Pipeline Design

## Sources

- `construction/u1-ticket-read-skeleton/infrastructure-design/infrastructure-design-questions.md`
- `construction/u1-ticket-read-skeleton/nfr-design/security-design.md`
- `construction/u1-ticket-read-skeleton/nfr-design/logical-components.md`
- `construction/u1-ticket-read-skeleton/nfr-requirements/security-requirements.md`
- `construction/u1-ticket-read-skeleton/nfr-requirements/tech-stack-decisions.md`
- `construction/u1-ticket-read-skeleton/functional-design/functional-spec.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`
- `aidlc/spaces/default/memory/team.md`
- `aidlc/spaces/default/memory/project.md`

## Purpose and Applicability

U1은 기존 FastAPI application artifact에 포함되는 Python library다. 이 설계는 새 CI provider, workflow file, cloud resource, container, IaC stack 또는 deployment environment를 만들지 않는다. 저장소 밖의 기존 build·promotion 경로가 U1을 포함할 때 실행해야 하는 재현 가능한 quality contract를 정의한다.

`cicd-pipeline.md`라는 이름은 검증과 승격 순서를 뜻한다. 현재 저장소에 project-owned CI/CD 설정이 없으므로 특정 vendor, runner image, credential store, deployment strategy 또는 production topology를 추측하지 않는다. Code Generation은 application·test·dependency 파일만 변경하며 pipeline automation 자체를 생성하지 않는다.

## Pipeline Invariants

| ID | Invariant | Enforcement |
|---|---|---|
| PIPE-U1-01 | Python runtime은 3.13이고 dependency는 repository lock output에서 설치한다. | environment-preparation gate |
| PIPE-U1-02 | 실제 OpenAI와 ITSM network 호출은 모든 기본 자동화에서 0건이다. Python test process의 autouse default-deny fixture가 DNS와 TCP 진입점을 막고 FakeModel·MockTransport만 허용한다. | FakeModel, MockTransport, process-level unexpected-network blocker와 deliberate bypass probe |
| PIPE-U1-03 | credential persistence는 보호된 기존 `ServerSession.itsm_token` 하나만 허용하고 IdentitySession만 복원·원자 교체한다. access token, client secret, OpenAI API key, Authorization과 raw upstream detail은 model/result/API/log/test output에 나타나지 않으며 pending/cursor/history/create/update namespace에는 credential 복제가 0건이다. | protected ServerSession 전용 access/rotation fixture, namespace별 row scan, secret-canary suite와 isolated failing-test output scan |
| PIPE-U1-04 | 기존 전체 pytest와 모든 U1 contract/security/concurrency test가 통과해야 한다. | test gate; failure stops promotion |
| PIPE-U1-05 | U1에서 새로 만들거나 변경한 application source의 line coverage는 80% 이상이다. | coverage 7.17.0 JSON report with Code Generation source manifest |
| PIPE-U1-06 | 보호 chat, user switch, logout, conversation clear, session expiry는 동일한 per-conversation lock을 사용한다. 각 lifecycle event는 lock 뒤 expected user/session/conversation을 재검증하고 presentation-before-history cleanup, pending/cursor invalidation과 terminal commit까지 lock을 유지한다. stale/expired Runner 결과는 correlation·fallback·publication 전에 폐기한다. | 네 event별 deterministic Runner-history-write barrier; same-lock wait, post-lock actor revalidation, cleanup ordering, terminal commit과 commit 후 old-scope SDK message/session·presentation 재생성 0건 |
| PIPE-U1-07 | test 또는 coverage failure를 외부 smoke, manual override, skipped test, lowered threshold로 우회하지 않는다. | promotion gate |
| PIPE-U1-08 | U1 release는 기존 application artifact와 기존 environment promotion/rollback 절차를 사용한다. | deployment handoff; no standalone artifact |
| PIPE-U1-09 | 기존 session table의 인증·사용자·권한·위임 credential column과 복원 의미를 그대로 보존하고 `session_expires_at`만 additive하게 추가한다. | legacy schema snapshot, migration rehearsal, exact-expiry/restart regression |
| PIPE-U1-10 | pending mutation의 `confirm`과 `consume_once`는 분리된 CAS transition이다. 미만료 `confirmed` update가 있으면 exact consume 재개·expiry·lifecycle invalidation 전 새 update prepare/revise publication을 원자 거부한다. 성공한 consume은 정확히 `ConsumedMutationEvidenceV1 { mutation_id, confirmed_at }`만 최대 한 번 반환하고 이 evidence만으로 POST/PATCH authority를 만들지 않는다. | concurrent CAS, confirm-then-crash fault injection, concurrent update prepare/revise, repeat/expiry/binding matrix, exact schema assertion, pending/PATCH counter |
| PIPE-U1-11 | U1 lifecycle cleanup은 U2 `ticket_tools_create_v1` ledger row, idempotency key와 canonical request bytes를 삭제·재작성하지 않는다. U1 consume 뒤 U2 bind 전 crash에서는 같은 attempt/key/bytes를 보존하고 새 pending review와 재확인을 요구하며 unbound POST는 0건이다. | U2 fake durable ledger snapshot, cleanup-before/after comparison, crash-before-bind fault injection |
| PIPE-U1-12 | server session의 `credential_expires_at`이 server UTC clock의 `utc_now + 60초` 이하이면 expired/imminent로 판정한다. 첫 public gateway call 전에 gateway-only credential accessor가 이 predicate를 평가하고 `TicketOperations`의 one-shot read budget으로 internal `ReadCredentialRefreshPortV1`을 호출한다. pre-call refresh 실패 시 ticket HTTP 호출은 0건이고 성공 시 refreshed capability만 첫 HTTP attempt에 사용한다. 첫 HTTP 401도 남아 있는 같은 budget만 사용할 수 있으므로 trigger 조합 전체에서 refresh는 최대 한 번이다. | injected UTC/monotonic clocks, boundary fixtures at 60초 ±1µs, fake `ReadCredentialRefreshPortV1`, capability-handle probe, refresh/HTTP counters |
| PIPE-U1-13 | U2 create refresh는 U2가 durable하게 소비한 one-invocation `CredentialRefreshReservationV1`만 public `CredentialRefreshPortV1`에 전달한다. U1은 authenticated opaque envelope의 create-attempt·actor binding을 검증하고 U2 storage에 접근하지 않으며 exchange 최대 1회와 기존 `ServerSession.itsm_token` atomic commit만 수행한다. | fake U2 durable repository와 reservation verifier, mismatch/tamper/expiry/restart replay, pre/post-commit crash, U2-table access·exchange·atomic-commit counters |

## Execution Environments

| Environment | Purpose | Network and credential stance | Required outcome |
|---|---|---|---|
| Developer/local verification | 계층 구현 직후 targeted test와 전체 회귀 실행 | FakeModel·MockTransport만 사용; real provider credential 불필요 | 선택한 test와 전체 suite 통과 |
| Existing CI or promotion runner | merge·승격 전 repeatable release evidence | outbound OpenAI/ITSM 차단; deterministic canary만 사용 | 모든 blocking gate 통과와 sanitized evidence 보존 |
| Existing staging | 기존 application artifact의 배포 후 기존 smoke 절차 | 현재 조직 절차가 소유; 이 Unit은 provider credential을 새로 요구하지 않음 | 기존 application smoke와 rollback readiness |
| Existing production | 기존 manual approval 이후 기존 방식으로 승격 | 현재 production secret·deployment 통제를 그대로 사용 | 기존 service health 기준 충족 |

환경 topology와 scale은 바뀌지 않는다. staging과 production이 실제로 어떤 provider나 strategy를 쓰는지는 저장소 근거가 없으므로 이 설계의 선택 사항이 아니다.

## Stage-to-Gate Sequence

| Order | Stage | Inputs and action | Blocking gate | Evidence |
|---:|---|---|---|---|
| 1 | Source integrity | 승인된 U1 source manifest와 dependency files를 checkout하고 uncommitted/generated drift를 판별한다. | manifest에 없는 U1 application source 변경 또는 dependency drift가 있으면 중단 | commit identity, source manifest |
| 2 | Python environment | Python 3.13 환경에서 repository의 기존 dependency-install 절차를 사용한다. Code Generation이 `coverage==7.17.0`을 test-only direct dependency로 pin하고 기존 uv compile 절차로 lock을 갱신했는지 확인한다. | Python version mismatch, lock mismatch, installation failure | Python version, dependency resolution result |
| 3 | Static contract and migration checks | Pydantic/tool schema, strict V1 serialization, registry exactness와 migration ownership을 검사한다. legacy session DB에 migration을 적용해 기존 column 이름·type·nullability·값·restore 의미가 유지되고 `session_expires_at`만 추가되는지, parse 가능한 `created_at + 8시간` backfill과 malformed row fail-closed expiry를 검증한다. 새 linter/type checker는 quality gate로 추가하지 않는다. | schema snapshot·contract mismatch, 기존 field 변경, unsafe backfill | pytest contract and migration results |
| 4 | Targeted U1 tests | capability, gateway, operations, repositories, registry, presentation과 lifecycle test를 FakeModel/MockTransport로 실행한다. | failure, unexpected network, leaked canary | sanitized pytest output |
| 5 | Security and concurrency tests | injection, delegated-token marker, persistence-boundary secret scan, safe error, cursor binding, confirmation/consumption CAS와 confirmed-update publication block, U2 ledger isolation·crash-before-bind, internal read preflight·401 budget, U2 authenticated create-refresh reservation, process-level network bypass, lock/correlation, orphan cleanup과 네 lifecycle barrier를 실행한다. 각 barrier는 Runner SDK history write 중 경쟁 event를 시작해 same-lock wait, post-lock actor revalidation, presentation-before-history cleanup, revocable cleanup, terminal commit과 stale-result discard를 관찰한다. | secret boundary 위반, authority change, competing confirmed-update pending/PATCH, U2 ledger 변경, unbound POST, reservation replay·second exchange, refresh 초과·실패 뒤 HTTP 호출, unregistered network, metadata mismatch, lifecycle lock/ordering 위반, commit 후 old-scope SDK message/session·presentation 재생성 | boundary matrix, CAS/ledger/reservation/refresh/network counters와 event별 barrier/row-count evidence |
| 6 | Full regression | repository의 전체 pytest suite를 실행한다. | 기존 또는 신규 test 하나라도 실패하면 중단 | full-suite pass/fail |
| 7 | Coverage | 모든 test를 coverage 아래 실행하고 Code Generation source manifest가 가리키는 changed application paths만 80% floor로 판정한다. | report 누락, source 누락, line coverage <80% | `coverage.json`, terminal summary |
| 8 | Release evidence | test count, failures, skipped tests, network-call count, secret-scan result와 coverage를 한 summary로 묶는다. | 불완전하거나 secret-bearing evidence면 중단 | sanitized verification summary |
| 9 | Existing deployment handoff | application artifact를 기존 staging/production promotion 경로로 넘긴다. | 기존 promotion gate와 production approval | 기존 deployment record |
| 10 | Post-deploy decision | 기존 health/smoke 기준을 적용하고 이상 시 전체 application artifact를 rollback한다. | 기존 health 기준 실패 | 기존 smoke and rollback record |

## Verification Commands

### Recorded construction verification

기존 전체 회귀를 실행하는 명령은 다음과 같다. 이 명령은 U1의 80% coverage 판정 명령이 아니며 별도의 whole-application coverage threshold를 만들지 않는다.

```text
.venv/bin/python -m pytest -q
```

U1의 유일한 80% blocking coverage 판정은 Code Generation source manifest가 가리키는 changed application paths에 대해 아래 순서로 생성하는 machine-readable JSON 결과다. 이 coverage run 자체가 전체 pytest suite를 다시 실행하므로 결과가 서로 다른 test subset을 측정하지 않는다.

```text
.venv/bin/python -m coverage erase
.venv/bin/python -m coverage run --source=app -m pytest -q
.venv/bin/python -m coverage json --include='<source-manifest comma-separated app paths>' --fail-under=80 -o coverage.json
```

`<source-manifest comma-separated app paths>`는 Code Generation이 확정한 regular application source paths로 치환한다. placeholder 상태로 명령을 실행하거나 저장소 전체를 임의 glob으로 대체하지 않는다. `coverage.json`이 대상 path를 하나도 측정하지 못하면 성공으로 처리하지 않는다.

## Test Automation Integration

| Suite | Required cases | Test seam | Pass rule |
|---|---|---|---|
| Tool and schema | exactly `ticket_read` at U1 checkpoint, strict modes, unknown field rejection, safe result states | Agents SDK FakeModel, Pydantic schema inspection | 모든 expected call/result가 exact V1과 일치 |
| Gateway contract | allowlisted query/path/header, one attempt per call, delegated token marker, uniform 404 | `httpx.MockTransport` | real network 0건, service-token ticket call 0건 |
| Read policy | timeout/transport/500/502/503/504 retry, server UTC 기준 `credential_expires_at <= utc_now + 60초` pre-call refresh, 401 refresh, 429 immediate return, max two attempts and one shared refresh budget | injected UTC/monotonic clocks, 60초 ±1µs fixtures, sleeper, internal `ReadCredentialRefreshPortV1`, capability-handle and request counters | pre-call success는 refreshed handle로 첫 HTTP attempt; pre-call failure의 ticket HTTP 0건; pre-call success 뒤 401에는 second refresh 0건; non-imminent 첫 401은 refresh 1회와 final attempt; 전체 elapsed ≤ `2 × ITSM_TIMEOUT_SECONDS + 0.25`; third HTTP call 0건 |
| U2 create credential refresh | durable one-invocation claim, authenticated opaque reservation, exact create-attempt/user/session/conversation binding, atomic ServerSession rotation, crash/replay closure | fake U2 `ticket_tools_create_v1` repository, fake verifier/server secret, exchange and commit barriers, restart fixture | durable restart replay와 second invocation은 U2가 port 호출 전 거부하여 U1 call 0건; first-call tamper·expiry·actor/create-attempt mismatch는 U1 verifier call 1건, exchange 0건; 모든 거부 경로의 session credential mutation 0건; accepted invocation당 exchange≤1; U1의 U2-table access 0건; 성공 전 `ServerSession.itsm_token` atomic commit; pre/post-commit crash 뒤 second exchange 0건 |
| Safe projection | malicious body/header/exception, malformed success, instruction-shaped text | controlled fixtures | raw detail/authority change/false success 0건 |
| ETag profiles | ordinary detail without usable ETag, read-for-update valid/invalid ETag matrix | typed gateway outcomes | ordinary read may succeed without evidence; invalid read-for-update fails and PATCH evidence 0건 |
| Cursor repository | issue/resolve, 128-bit CSPRNG seam, 100,000 collision sample, actor/query/tamper/replay | isolated repository DB and entropy source seam | collision/binding bypass/raw cursor exposure 0건 |
| Pending repository and downstream ledger isolation | create/update variants, exact-old replacement, 15-minute expiry, lifecycle invalidation, separate `confirm`/`consume_once` CAS, confirm 직후 crash와 concurrent update prepare/revise, concurrent/repeat consume, exact evidence schema, U1 cleanup 전후 U2 ledger snapshot, consume-after/bind-before crash | isolated session DB, fake clock, U2 fake `ticket_tools_create_v1` ledger and fault-injection seam | successful consume ≤1회; 미만료 confirmed update에서 exact consume/expiry/lifecycle 전 새 pending·PATCH 0건과 confirmed authority 보존; evidence가 정확히 `{mutation_id, confirmed_at}`; U2 row/key/bytes 불변; unbound mutation 0건 |
| Presentation/history | before-Runner conversation lock, persisted-message correlation, commit/readback, restart, orphan cleanup | concurrent FakeModel runners and isolated history DB | metadata mismatch 0건; cleanup failure gives text fallback and later retry |
| Runner/lifecycle serialization | user switch, logout, conversation clear, session expiry 각각 Runner history-write barrier에서 경쟁 event 시작; post-lock expected actor 재검증, presentation-before-history cleanup, revocable invalidation, terminal commit과 stale-result discard | event별 controllable FakeModel Runner barrier, shared lock probe, isolated session/history DB, ordering recorder와 direct row counters | 네 event 모두 same lock에서 대기하고 terminal commit까지 보유; actor mismatch는 새 scope를 건드리지 않음; commit 후 old-scope SDK message/session·presentation 재생성 0건; expiry는 success reply/metadata publication도 0건 |
| Browser fallback | unknown/corrupt/missing presentation, text-node escaping, live/restored semantics | DOM-level or existing browser test harness | reply text preserved; markup execution 0건 |
| Secret containment and persistence boundary | protected ServerSession row, pending/cursor/history/create/update rows, schema/result/API/log와 intentional isolated test failure | distinct canaries, IdentitySession-only accessor/atomic-rotation probe, namespace별 SQLite scan, captured stdout/stderr/traceback/assertion diff | 기존 `ServerSession.itsm_token`만 persistence 허용; IdentitySession 이외 read/write 0건; 다른 namespace와 모든 관찰 경계 canary 0건; rotation은 commit 전 외부 성공 0건 |
| Existing experience | login, user switch, session, chat/history/clear, model/reasoning/tracing configuration | existing pytest/FakeModel fixtures | 승인되지 않은 회귀 0건 |
| Session migration and expiry | representative legacy session DB, fake UTC clock, restart/activity/token-refresh fixtures | isolated session DB and existing restore path | 기존 field/value·복원 의미 100% 보존; exact/after expiry capability·Runner·ITSM 0건; deadline 연장 0건 |
| Rollback write compatibility | additive migration 뒤 직전 release의 session create, restore, login, logout/write paths 실행 후 새 release 재기동 | migrated copy of a representative legacy DB and prior-release application fixture | `session_expires_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z'` 때문에 이전 INSERT/UPDATE가 schema error 없이 성공; prior release가 만든 default-deadline row는 새 release에서 expired로 fail closed하고 재로그인을 요구 |

Skipped tests are listed in release evidence. A newly skipped or xfailed U1 security, contract, concurrency or regression test is a blocking failure unless the user separately approves a scoped requirement change through the lifecycle; CI configuration alone cannot waive it.

## Network Isolation

- Default automation installs no real OpenAI or ITSM credential.
- FakeModel is the only model provider used by U1 tests.
- `httpx.MockTransport` is injected into ITSM boundaries; any unregistered outbound request fails the test.
- 전체 pytest session의 autouse fixture는 allowlist 없는 default-deny로 `socket.getaddrinfo`, `socket.create_connection`, `socket.socket.connect`/`connect_ex`, 그리고 asyncio event-loop TCP connection 진입점을 `UnexpectedNetworkError`로 교체한다. MockTransport와 in-process ASGI test transport는 socket을 사용하지 않으므로 별도 host allowlist를 만들지 않는다.
- deliberate bypass probe는 injection 경계를 사용하지 않는 새 `httpx.AsyncClient`와 raw socket 경로를 각각 호출해 둘 다 DNS lookup 또는 socket I/O 전에 `UnexpectedNetworkError`로 실패하는지 확인한다. blocker가 설치되지 않았거나 probe가 다른 network 예외까지 진행하면 전체 gate를 실패시킨다.
- DNS/network availability must not be required for test execution after dependencies are present.
- A manually triggered real-environment smoke, if an existing operating procedure owns one, is non-blocking supplemental evidence and never replaces deterministic gates.
- Failure in deterministic automation cannot be retried against production or a live ITSM tenant.

## Secrets Management in CI/CD

| Data | Default automation | Existing deployment path | Evidence rule |
|---|---|---|---|
| OpenAI API key | absent; FakeModel only | unchanged existing secret injection | never print, persist, serialize or include in test fixture |
| ITSM delegated token | deterministic canary object, not a valid token | current server session path only | value unavailable to model/result/log |
| Protected session credential | 기존 `ServerSession.itsm_token` fixture에만 저장 | IdentitySession-only restore and atomic rotation | pending/cursor/history/create/update row에는 복제 0건; session row 자체는 허용된 persistence로 분류 |
| ITSM client secret | deterministic canary for redaction tests only | unchanged existing server-side configuration | not required by CI test execution |
| Authorization header | MockTransport marker without value disclosure | created only at outbound boundary | raw header absent from evidence |

No secret is placed in repository files, command arguments, coverage output or test artifact names. CI logs retain only allowlisted error codes, safe request IDs and counts. An intentional failing-test subprocess verifies that pytest diagnostics do not reveal injected canaries.

## Artifact and Evidence Management

| Artifact | Contents | Confidentiality | Retention owner |
|---|---|---|---|
| Sanitized pytest result | pass/fail/skip counts and safe failure locations | no payloads, headers or credentials | existing CI/promotion system |
| `coverage.json` | file/line coverage for source-manifest paths | source path and line metrics only | existing CI/promotion system |
| Verification summary | Python/dependency identity, network count, canary count, coverage, gate results | allowlisted metadata only | existing CI/promotion system |
| Network-blocker evidence | autouse fixture installation, AsyncClient/raw-socket bypass probe pass, attempted unregistered network count | endpoint, payload, credential 없이 blocker 이름과 count만 | existing CI/promotion system |
| Security boundary evidence | lifecycle event별 barrier 순서·row/publication count, reservation verifier/exchange/commit count, confirmed-update publication count, namespace별 credential scan | 비밀 값 없이 event·boundary 이름과 count만 | existing CI/promotion system |
| Application artifact | existing FastAPI application including U1 library | existing application classification | existing deployment system |

The design does not set a new retention duration because no pipeline provider or compliance retention requirement is established. Whatever existing system stores evidence must preserve its current policy without adding raw tool traces or external response bodies.

## Deployment and Promotion Strategy

| Facet | Decision | Rationale |
|---|---|---|
| Deployable unit | existing FastAPI application artifact | U1 is not independently deployable |
| Staging promotion | existing on-merge or current external process after all gates | team practice says keep the existing path |
| Production promotion | existing manual approval | organization rule requires separate production approval |
| Deployment strategy | unchanged and unspecified here | no repository evidence for blue-green/canary/rolling/recreate |
| Feature flag | none added | U1 registry checkpoint and exact contracts provide release boundary; no existing flag system is established |
| Database change | 기존 session table에 `session_expires_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z'`를 additive하게 추가하고 기존 parseable row를 `created_at + 8시간`으로 backfill하며 U1 tables/namespaces를 기존 SQLite files에 추가 | default가 직전 release의 column-omitting write를 허용하고, 새 release는 backfill 불가·rollback 중 새로 쓰인 epoch row를 expired로 fail closed함; no new database service |

The promotion path must not deploy U1 separately from the migration and application code that consume it. Startup applies additive migrations before the feature can use repositories; migration failure prevents the new application version from serving ticket-tool behavior.

## Rollback Design

1. Stop promotion or remove the failed new application artifact using the existing deployment mechanism.
2. Restore the last known-good whole application artifact; do not attempt a partial U1 module rollback.
3. Leave additive `session_expires_at`, `ticket_tools_state_v1`, `ticket_tools_history_v1`, and downstream-owned `ticket_tools_create_v1` in place during code rollback. U1 cleanup or rollback must not delete or rewrite the U2 ledger. `session_expires_at`의 NOT NULL epoch default 덕분에 직전 release가 column을 생략한 session write를 계속할 수 있고, forward redeploy는 그 row를 만료 상태로 처리해 재로그인을 요구한다. Destructive down-migration would add data-loss risk.
4. Do not reuse pending mutation or cursor state to infer success after rollback. A reintroduced version applies normal expiry and lifecycle validation.
5. Presentation companion rows remain optional; the prior browser/API continues with existing text-only history.
6. Investigate using sanitized request IDs and gate evidence. Never copy raw credential, header or problem body into an incident record.

Rollback readiness is verified by migration idempotency, migrated DB 위에서 실행하는 직전 release의 session create/restore/login/logout write rehearsal, forward redeploy의 epoch-row fail-closed 검사와 old-code/text-only compatibility tests, not by creating a new environment or deployment script. 이 rehearsal이 현재 직전 release fixture로 통과하지 않으면 rollback 가능성을 주장하지 않고 기존 배포 절차의 database restore 또는 forward-fix 경로를 사용한다.

## Failure and Retry Policy

| Failure | Pipeline action | Retry allowance |
|---|---|---|
| Dependency installation or lock mismatch | stop before tests | retry only after repository/dependency issue is corrected |
| Test failure | stop promotion and preserve sanitized result | rerun only after code/test/environment fix; no flaky auto-pass |
| Unexpected external network | fail immediately | none until injection/isolation defect is fixed |
| Secret canary detected | fail immediately and suppress unsafe artifact publication | none until leak source and any persisted evidence are remediated |
| Coverage below 80% or target absent | stop promotion | add legitimate tests or correct source manifest; never lower threshold |
| Existing deployment failure | execute existing rollback procedure | existing deployment system owns retry decision |
| Optional real smoke unavailable | do not reinterpret deterministic gates | follow separate operating procedure; never block deterministic test diagnosis |

## Ownership and Handoff

| Responsibility | Owner |
|---|---|
| U1 source, tests, dependency pin and source manifest | U1 Code Generation |
| Exact full-suite and coverage execution | existing CI/promotion runner or local release verifier |
| Final three-tool assembly, README and whole-feature verification | U4 Release Assurance |
| Existing staging/production deployment, approval and rollback | current external deployment process |
| New CI provider, workflow or cloud infrastructure | out of scope; no owner created by this feature |

## Release Gate Summary

U1 can be handed to the existing deployment path only when every blocking gate passes: Python/dependency identity, exact contracts, backward-write-compatible additive session migration과 prior-release rollback rehearsal, protected `ServerSession.itsm_token` sole-persistence/IdentitySession-only atomic rotation, separate confirmation/consumption CAS와 confirmed-update publication block, U2 ledger isolation과 crash-before-bind recovery, internal read port의 deterministic 60초 pre-call/401 shared budget, U2 durable authenticated reservation의 exchange≤1·restart/crash closure, 네 lifecycle event의 same-lock barrier·post-lock actor revalidation·terminal commit과 old-scope regeneration 0건, process-level network default-deny, full regression, secret non-disclosure and the sole U1 80% gate over changed application code paths. The pipeline adds no runtime infrastructure and grants no exception to existing production approval or rollback controls.
