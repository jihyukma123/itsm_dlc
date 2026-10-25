# U2 Ticket Write — CI/CD Pipeline Design

## Sources

- `construction/u2-ticket-write/infrastructure-design/infrastructure-design-questions.md`
- `construction/u2-ticket-write/nfr-design/security-design.md`
- `construction/u2-ticket-write/nfr-design/logical-components.md`
- `construction/u2-ticket-write/nfr-requirements/security-requirements.md`
- `construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md`
- `construction/u2-ticket-write/functional-design/functional-spec.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`
- `construction/u2-ticket-write/code-generation/code-generation-plan.md`
- `construction/u2-ticket-write/code-generation/source-manifest.json`
- `app/config.py`
- `app/ticketing/capability.py`
- `app/agent/service.py`
- `aidlc/spaces/default/memory/team.md`
- `aidlc/spaces/default/memory/project.md`

## Purpose and Applicability

U2는 기존 FastAPI application artifact에 포함되는 Python library다. 새 CI provider, workflow file, cloud resource, container, IaC stack, deployment environment, queue, cache, distributed lock 또는 database service를 만들지 않는다. 기존 Server Session SQLite 안에 승인된 U2 namespace인 `ticket_tools_create_v1.ticket_create_attempts`를 additive migration으로 추가하고, 저장소 밖 기존 build·promotion 경로가 U2를 포함할 때 실행해야 하는 재현 가능한 quality contract만 정의한다.

`cicd-pipeline.md`라는 이름은 검증과 승격 순서를 뜻한다. 현재 저장소에 project-owned CI/CD 설정이 없으므로 vendor, runner image, credential store, deployment topology 또는 blue-green/canary/rolling 전략을 추측하지 않는다. Code Generation은 application·test·dependency·검증 helper만 변경하며 pipeline automation 자체를 생성하지 않는다.

## Refresh Contract and Configuration Closure

| ID | Approved boundary | Implementation and blocking evidence |
|---|---|---|
| REFRESH-U2-01 | C-01의 유일한 create refresh operation은 `refresh_delegated_capability_once(TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline)`다. U1 `CredentialRefreshPortV1`이 provider이고 U2 create policy가 consumer다. | `tests/conftest.py`의 shared provider/consumer fixture와 U1/U2 contract tests가 exact signature, 동일 actor binding, session credential atomic commit, invocation/exchange 최대 1회를 함께 검사한다. U1 read 전용 `ReadCredentialRefreshPortV1.refresh_once`를 사용하면 contract test가 실패한다. |
| REFRESH-U2-02 | Stable key source는 application startup configuration의 `TICKET_REFRESH_KEYS_JSON`, `TICKET_REFRESH_CURRENT_KID`, `TICKET_REFRESH_VERIFICATION_SECONDS`다. `app.config.Settings`가 소유하고 `AgentService`가 application boot마다 signer/verifier를 조립한다. | `TICKET_REFRESH_KEYS_JSON`은 `kid`별 최소 256-bit base64url key map이고 current `kid`가 반드시 포함된다. Verification lifetime은 86,400~604,800초이며 create-attempt 최소 보존 24시간 이상이다. 설정 일부 누락, malformed/weak key, unknown current `kid`, 범위 밖 lifetime은 refresh를 fail closed한다. Production secret default는 없다. |
| REFRESH-U2-03 | U2에는 current-key signer만, U1에는 current+verification-only previous-key verifier만 주입한다. Raw key accessor, ledger 저장, model/result/log 출력은 없다. `creator_boot_id`는 매 boot CSPRNG memory 값이고 key ring은 environment-backed configuration으로 restart 뒤 동일하다. | Rotation은 새 `kid`를 current로 전환하되 이전 key를 verification map에 최소 `TICKET_REFRESH_VERIFICATION_SECONDS` 동안 유지한 뒤 폐기한다. Rotation 전후 restart, unknown/retired `kid`, MAC/binding/deadline tamper에서 exchange 0회와 raw-key canary 0건을 blocking test로 남긴다. |

이 계약은 `construction/u2-ticket-write/nfr-design/security-design.md`의 authenticated refresh reservation 설계와 현재 `app/config.py`, `app/ticketing/capability.py`, `app/agent/service.py` 경계를 구체화한다. 위 설정이 없거나 검증되지 않으면 refresh가 필요한 create request는 fail closed되고 ticket POST를 시작하지 않는다. 임시 secret, process-local signing key, hardcoded production key로 우회하지 않는다.

## Pipeline Invariants

| ID | Invariant | Blocking evidence |
|---|---|---|
| PIPE-U2-01 | Python 3.13과 repository-pinned dependency set을 사용한다. | Python version, dependency/lock consistency |
| PIPE-U2-02 | U2는 `ticket_tools_create_v1.ticket_create_attempts`만 소유하고 U1의 `ticket_tools_state_v1`·`ticket_tools_history_v1`을 수정하지 않는다. | migration inventory, before/after schema snapshot |
| PIPE-U2-03 | Ledger `prepared` commit이 U1 pending publication보다 먼저 성공해야 하며, U1 `consume_once` evidence가 같은 actor·payload attempt에 결합되기 전 POST는 0회다. | ordered fault injection, direct SQLite row snapshot, POST counter |
| PIPE-U2-04 | 모든 POST 전에 unique send claim ID, deadline, `in_flight`, 증가된 global attempt count가 한 CAS로 commit된다. Active claim은 deadline 전에 탈취하지 않는다. | concurrent barrier, affected-row count, fake clock, transport counter |
| PIPE-U2-05 | 현재 result-lookup 계약이 없으므로 ambiguous/stale send는 existing send claim으로 fence된 단일 no-I/O CAS에서 `lookup_unavailable_finalized`와 retryable/terminal state를 함께 확정한다. `ambiguous`에서 직접 POST하거나 durable `started` owner를 남기지 않는다. | no-I/O finalization CAS matrix, crash-before/after-CAS barrier, late-response barrier, stale-write count 0 |
| PIPE-U2-06 | REFRESH-U2-01~03의 configuration validation과 shared C-01 contract fixture가 통과한 경우에만 no-apply 401 refresh를 활성화한다. Durable one-shot reservation 승자만 exact C-01 port를 호출하고, U1은 envelope 검증과 성공 credential의 기존 session store 원자 commit 뒤 same-binding capability를 반환한다. | configuration contract tests, reservation row, shared contract fixture, provider exchange/commit probes, refresh invocation ≤1 |
| PIPE-U2-07 | 모든 create POST는 하나의 original key와 byte-identical stored body를 사용하며 전체 POST는 최대 2회다. 두 번째 불명확 결과 뒤 third POST는 0회다. | key/body capture, global attempt counter, terminal ambiguity assertion |
| PIPE-U2-08 | Created 또는 `Idempotent-Replayed` 응답의 ticket ID가 없으면 durable `completed`와 사용자 success를 만들지 않는다. | malformed/response-loss/replay matrix, success publication counter 0 |
| PIPE-U2-09 | 실제 OpenAI·ITSM network 호출은 기본 자동화에서 0건이다. FakeModel·MockTransport와 process-level default-deny network fixture만 사용한다. | deliberate AsyncClient/raw-socket bypass probes와 unexpected-network count 0 |
| PIPE-U2-10 | credential, Authorization, client secret, OpenAI API key, idempotency key, canonical bytes와 raw upstream detail은 model/result/API/log/test evidence에 나타나지 않는다. | distinct canary sweep over schema, rows, stdout/stderr and failure diagnostics |
| PIPE-U2-11 | 기존 전체 pytest와 모든 U2 contract/security/restart/concurrency test가 통과하고, U2가 변경한 `app/**/*.py` executable lines의 coverage가 80% 이상이다. | full-suite result와 changed-line coverage JSON/summary |
| PIPE-U2-12 | Confirmed row는 `retained_until >= confirmed_at + 24h`, orphan prepared row는 `retained_until >= created_at + 24h`를 유지하고 lifecycle cleanup이나 rollback이 그 전 삭제하지 않는다. | fake-clock cleanup matrix와 rollback DB snapshot |
| PIPE-U2-13 | 현재 배포 모델은 single-process다. Multi-process 배포 증거가 발견되면 shared lock 또는 transactional arbitration 재설계 전 승격을 중단한다. | startup/deployment configuration assertion and explicit release blocker |
| PIPE-U2-14 | Test, network-isolation, canary, coverage 또는 contract failure를 live smoke, skip, xfail, threshold 하향으로 우회하지 않는다. | promotion gate and release-evidence completeness check |
| PIPE-U2-15 | Refresh envelope는 세 `TICKET_REFRESH_*` 설정이 모두 유효할 때만 생성한다. Process-local signing key, hardcoded production key, U2 ledger의 raw key 저장, verification lifetime보다 짧은 previous-key retention을 금지한다. | configuration-presence/bounds assertion, raw-key scan, rotation/restart/retired-key fixtures |
| PIPE-U2-16 | Refresh를 이미 사용한 attempt가 다시 authoritative no-apply 401을 받으면 existing send claim으로 terminal authentication outcome을 한 번 기록하고 추가 refresh·claim·POST를 수행하지 않는다. | second-401 matrix, terminal-write count 1, additional refresh/claim/POST counts 0 |

## Execution Environments

| Environment | Purpose | Network and credential stance | Required outcome |
|---|---|---|---|
| Developer/local verification | 계층 구현 직후 targeted test와 전체 회귀 실행 | FakeModel·MockTransport만 사용; 실제 provider credential 불필요 | 선택한 test와 전체 suite 통과 |
| Existing CI or promotion runner | merge·승격 전 repeatable U2 evidence 생성 | OpenAI/ITSM outbound default-deny; deterministic canary만 사용 | 모든 blocking gate 통과와 sanitized evidence 보존 |
| Existing staging | 기존 application artifact 배포 후 조직의 현행 smoke 수행 | 외부 절차가 credential과 network를 소유하고 승인된 세 `TICKET_REFRESH_*` 설정을 secret injection 경계에서 제공 | 기존 application health와 rollback readiness; refresh configuration validation 성공 |
| Existing production | 기존 manual approval 이후 현행 방식으로 승격 | 현재 production secret·deployment 통제를 유지 | 기존 service health 기준 충족 |

환경 topology와 scale은 바뀌지 않는다. Staging과 production provider·전략·규모는 저장소 근거가 없으므로 이 설계에서 새로 선택하지 않는다.

## Stage-to-Gate Sequence

| Order | Stage | Inputs and action | Blocking gate | Evidence |
|---:|---|---|---|---|
| 1 | Source integrity | 승인 입력은 `aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/code-generation/code-generation-plan.md`의 `## Planned Source Set` 표이고, machine-readable projection은 같은 디렉터리의 `source-manifest.json`이다. Manifest schema는 top-level `stage="code-generation"`, `unit="u2-ticket-write"`, `version=1`, non-empty unique `writes[]`와 각 row의 repository-relative regular-file `path`만 허용한다. Promotion runner는 merge 대상의 검증된 commit을 `AIDLC_PROMOTION_BASE_SHA`로 반드시 주입하고 clean checkout에서 `MERGE_BASE=$(git merge-base "$AIDLC_PROMOTION_BASE_SHA" HEAD)`를 계산한다. 아래 `Source Integrity Commands`가 plan과 manifest의 exact set을 비교하고, manifest의 각 path가 `git diff --name-only --diff-filter=ACMRT "$MERGE_BASE" HEAD -- app tests scripts requirements.in requirements.txt`의 committed source set에 포함되는지 확인한다. `git status`는 로컬 진단에만 사용할 수 있고 promotion evidence가 될 수 없다. 다른 Unit의 변경 때문에 생기는 manifest 밖 path는 U2 소유로 간주하지 않으며 U4가 모든 Unit manifest 합집합과 최종 source set을 exact 비교한다. | Plan 승인 전 manifest 생성, missing/untrusted base SHA, non-clean promotion checkout, schema/unit/version 불일치, duplicate/missing/non-regular path, plan 표와 manifest 불일치, manifest path가 committed merge-base diff에 없음, unapproved rename 또는 dependency drift | Plan Approval-bound plan digest, manifest digest, base SHA와 merge-base, exact committed diff, plan↔manifest exact set과 manifest⊆committed-diff 판정 |
| 2 | Python environment | Python 3.13에서 repository-pinned dependency 설치 절차를 사용하고 `coverage==7.17.0` 가용성을 확인한다. | version/lock mismatch, installation failure | Python/dependency versions |
| 3 | Static contract, refresh configuration and migration checks | C-01/C-03A/C-04/C-07 V1 schema, exact `ticket_write` registration, U2 migration ownership과 additive optional claim/refresh fields를 검사한다. REFRESH-U2-01의 exact provider/consumer signature·shared fixture와 REFRESH-U2-02/03의 설정 이름, owner, key strength, lifetime, rotation, raw-key 비노출 계약을 확인한다. | 계약/설정 불일치, invalid or absent key configuration, U1 namespace 변경, unapproved table/required-field reinterpretation | schema snapshot, migration inventory, config validation matrix, shared contract-test result |
| 4 | Ledger-first and confirmation tests | Prepare/revise ordering, orphan prepared row, replacement race, `consume_once` evidence binding, crash-before-bind 재확인, retention 연장을 검사한다. | pending-without-ledger committed state, unbound POST, stale review execution, premature deletion | failure-injection events, row snapshots, POST counters |
| 5 | Send/reconciliation/refresh concurrency tests | Send claim, no-I/O reconciliation finalization, late response, active-deadline non-takeover, durable refresh reservation과 credential atomic commit을 deterministic barrier로 검사한다. Refresh suite는 두 blocker가 해제된 승인 계약을 fixture로 사용한다. | durable reconciliation `started`, owner가 둘 이상, stale write, direct ambiguous POST, second refresh, commit 전 success capability | CAS affected-row counts, crash barriers, claim/refresh/network counters |
| 6 | Transport and security tests | Exact key/bytes, POST ≤2, 429 no-retry, authoritative ticket-ID completion, malicious external text와 모든 secret boundary를 검사한다. | byte/key drift, third POST, false success, raw detail 또는 canary 노출 | MockTransport capture, result/publication counters, canary scan |
| 7 | Full regression | Repository 전체 pytest suite를 FakeModel/MockTransport와 network default-deny 아래 실행한다. | 기존 또는 신규 test 하나라도 실패, unexpected external call | full-suite pass/fail/skip counts, network count |
| 8 | Changed-line coverage | 전체 suite의 `coverage.json`과 merge-base diff로 U2 변경 executable line coverage를 계산한다. | denominator 없음, report/source 누락, coverage <80% | base commit, included paths, covered/total lines, percentage |
| 9 | Release evidence | Test, skip/xfail, network, secret, migration, CAS, attempt, retention, coverage 결과를 한 sanitized summary로 묶는다. | 불완전하거나 secret-bearing evidence | verification summary |
| 10 | Rollback compatibility rehearsal | U2 migration이 적용되고 non-expired `prepared`, `in_flight`, `ambiguous`, `completed` sample row를 포함한 disposable representative DB copy에 last-known-good application을 연결한다. Startup·기존 login/session/chat read가 성공하고 U2 table·columns·row bytes/count·`retained_until`·claim state가 rehearsal 전후 동일한지 검사한다. | startup/schema compatibility 실패, U2 row/claim/retention 변화, destructive migration 시도 | fixture DB digest, schema snapshot, per-state row counts and immutable-field digest before/after, test result |
| 11 | Existing deployment handoff | REFRESH-U2-01~03과 order 1–10의 evidence가 모두 통과한 경우에만 기존 FastAPI application artifact를 현행 staging/production 승격 경로로 넘긴다. | refresh contract/config failure, missing rollback-rehearsal evidence, 기존 promotion gate 또는 production approval 실패 | complete verification summary, rollback-rehearsal evidence, existing deployment record |
| 12 | Post-deploy decision | 현행 health/smoke 기준을 적용한다. 이상 시 order 10에서 검증된 last-known-good whole-application artifact rollback만 허용하고, 해당 receipt가 없거나 대상 artifact/DB schema fingerprint가 다르면 rollback 대신 ledger-preserving forward-fix로 전환한다. | 기존 health 기준 실패 또는 rehearsal binding mismatch | existing smoke record, exact rehearsal receipt and artifact/schema binding, rollback or forward-fix record |

## Verification Commands

### Source integrity commands

Promotion은 merge 대상 commit SHA를 `AIDLC_PROMOTION_BASE_SHA`로 주입한 clean checkout에서 다음 블록을 그대로 실행한다. 이 블록은 작업 트리 상태에 의존하지 않고 승인 plan, manifest, committed merge-base diff를 비교한다.

```sh
set -eu
: "${AIDLC_PROMOTION_BASE_SHA:?promotion pipeline must provide the verified merge-target commit SHA}"

aidlc_plan='aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/code-generation/code-generation-plan.md'
aidlc_manifest='aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/code-generation/source-manifest.json'
aidlc_source_tmp=$(mktemp -d)
trap 'rm -rf "$aidlc_source_tmp"' EXIT HUP INT TERM

test -z "$(git status --porcelain=v1 --untracked-files=all)"
aidlc_base_commit=$(git rev-parse --verify "${AIDLC_PROMOTION_BASE_SHA}^{commit}")
git merge-base --is-ancestor "$aidlc_base_commit" HEAD
aidlc_merge_base=$(git merge-base "$aidlc_base_commit" HEAD)

jq -e '
  .stage == "code-generation" and
  .unit == "u2-ticket-write" and
  .version == 1 and
  (.writes | type == "array" and length > 0) and
  (all(.writes[]; (.path | type == "string" and length > 0))) and
  (([.writes[].path] | length) == ([.writes[].path] | unique | length))
' "$aidlc_manifest" >/dev/null

awk '
  /^## Planned Source Set$/ { in_set=1; next }
  in_set && /^## / { exit }
  in_set && /^\| `[^`]+` \|/ {
    path=$0
    sub(/^\| `/, "", path)
    sub(/` \|.*$/, "", path)
    print path
  }
' "$aidlc_plan" | LC_ALL=C sort -u >"$aidlc_source_tmp/plan.paths"
jq -r '.writes[].path' "$aidlc_manifest" | LC_ALL=C sort -u >"$aidlc_source_tmp/manifest.paths"
cmp -s "$aidlc_source_tmp/plan.paths" "$aidlc_source_tmp/manifest.paths"

while IFS= read -r aidlc_source_path; do
  test -f "$aidlc_source_path"
done <"$aidlc_source_tmp/manifest.paths"

git diff --name-only --diff-filter=ACMRT "$aidlc_merge_base" HEAD -- \
  app tests scripts requirements.in requirements.txt \
  | LC_ALL=C sort -u >"$aidlc_source_tmp/committed.paths"
comm -23 "$aidlc_source_tmp/manifest.paths" "$aidlc_source_tmp/committed.paths" \
  >"$aidlc_source_tmp/missing-from-committed-diff.paths"
test ! -s "$aidlc_source_tmp/missing-from-committed-diff.paths"

printf 'base=%s\nmerge_base=%s\nplan_manifest=exact\nmanifest_in_committed_diff=yes\n' \
  "$aidlc_base_commit" "$aidlc_merge_base"
```

Runner는 plan과 manifest의 digest, 위 출력, `committed.paths`, 빈 `missing-from-committed-diff.paths`를 promotion evidence로 보존한다. `AIDLC_PROMOTION_BASE_SHA`가 없거나 commit으로 검증되지 않거나 `HEAD`의 ancestor가 아니면 fail closed한다.

### Recorded construction verification

Workflow에 기록된 전체 검증 명령은 다음과 같다.

```text
.venv/bin/python -m coverage run --source=app -m pytest -q && .venv/bin/python -m coverage report --fail-under=80
```

이 명령은 전체 application coverage floor를 확인한다. U2의 별도 changed-line floor는 NFR Requirements에서 확정한 repository-owned helper를 사용해 동일한 full-suite run의 JSON 결과와 merge-base diff를 판정한다.

```text
aidlc_cov_base=$(git merge-base HEAD main)
.venv/bin/python -m coverage erase
.venv/bin/python -m coverage run --branch --source=app -m pytest -q
.venv/bin/python -m coverage json -o coverage.json
.venv/bin/python scripts/changed_line_coverage.py --base "$aidlc_cov_base" --coverage-json coverage.json --include 'app/**/*.py' --fail-under 80
```

`scripts/changed_line_coverage.py`는 base commit, 포함 파일, covered/total changed executable lines와 percentage를 출력하고 80% 미만이면 non-zero로 종료한다. U2는 application code를 변경하는 Unit이므로 empty denominator를 성공으로 처리하지 않는다.

## Test Automation Integration

| Suite | Required cases | Test seam | Pass rule |
|---|---|---|---|
| Tool/schema/registry | strict `TicketWriteToolInputV1`, unknown field rejection, exact `ticket_write` plugin and mapper registration | FakeModel, Pydantic/dataclass schema inspection | V1 shape와 exact tool name 일치; server-only field 노출 0건 |
| Catalog and canonicalization | active exact ID/name match, component/service relation, explicit-now single capture, fixed-order compact UTF-8 bytes | catalog fixtures, fake UTC clock, deterministic serializer | ambiguous/retired selector의 ledger·pending·POST 0건; stored bytes exact match |
| Ledger-first publication | ledger insert failure, pending publish failure, orphan cleanup, revise replacement | isolated Server Session SQLite, fault injection | pending-without-ledger 0건; orphan authority 0; stale review POST 0 |
| Confirmation binding | raw-current-turn exact confirm, quoted/model-generated text, actor/hash/expiry mismatch, concurrent consume | U1 public fake ports, fake clock and barriers | valid evidence ≤1; mismatch/unbound POST 0 |
| Send claim | concurrent claimers, pre/post deadline restart, outcome fencing | fake UTC/monotonic clock, transport barrier, direct rows | active owner 1개, deadline-before takeover 0, stale transport write 0 |
| Reconciliation finalization | ambiguous/stale send, lookup unavailable, crash immediately before/after CAS, retryable/terminal transition | direct rows, fake clock, deterministic CAS barriers | one finalization winner, durable `started` 0, direct ambiguous POST 0, stale write 0 |
| Credential refresh | exact C-01 signature, pre-call/401 trigger, actor/attempt/time/generation/deadline/MAC mismatch, concurrent reservation, commit-before-registry race, same-boot observer, rotation 전후 restart, crash before/after provider commit | durable reservation row, shared provider/consumer fixture, fake `CredentialRefreshPortV1`, approved signer/verifier fake, provider exchange/commit probes | open blocker 0, mismatch/unknown/retired key exchange 0, refresh invocation/exchange ≤1, success only after session credential commit, second refresh 0 |
| Refresh-used second 401 | proactive 또는 401-triggered refresh 뒤 authoritative no-apply 401 재발 | send-claim-fenced repository probe and exact counters | terminal authentication write 1, additional refresh/claim/POST 0 |
| Attempt/key/body budget | initial, refreshed, reconciled send paths | MockTransport exact body/header capture | original key·bytes only, POST ≤2, third POST 0 |
| Success evidence | created, replayed, missing/malformed ticket ID, response loss | controlled transport outcomes and publication probe | authoritative ticket ID 없는 completed/success 0 |
| Lifecycle/retention | logout, switch, clear, expiry, restart, confirmed/orphan cleanup | fake clock, copied SQLite DB, U1 cleanup adapter | revocable state만 정리; ledger/key/bytes 불변; 24시간 전 delete 0 |
| Rollback compatibility | U2 migration이 적용된 representative DB의 각 durable state와 last-known-good application startup/read path | disposable copied SQLite DB, schema/row digest probes, deployment-artifact identity fixture | 기존 login/session/chat read 성공, destructive migration 0, U2 schema·row count·retention·claim/key/bytes digest 변화 0 |
| Network isolation | unregistered AsyncClient and raw socket bypass | autouse DNS/TCP default-deny fixture | DNS/socket I/O 전에 deterministic failure; real calls 0 |
| Secret containment | credential, Authorization, client secret, key, canonical bytes, raw body/header/exception | unique canaries, isolated expected-failure subprocess | model/result/API/log/traceback/assert diff 노출 0 |
| Existing experience | login, user switch, session, chat/history/clear, fixed model/reasoning/tracing, browser fallback | existing pytest, FakeModel, ASGI/browser fixtures | 승인되지 않은 회귀 0 |
| Coverage helper | modified/new/deleted/renamed/non-executable lines and 80% boundary | synthetic diff and coverage JSON fixtures | calculation and exit status exactness |

새로 skip 또는 xfail된 U2 security, contract, concurrency, restart, retention, network 또는 regression test는 별도 요구사항 변경 승인 없이는 blocking failure다.

## Network Isolation

- 기본 자동화에는 실제 OpenAI 또는 ITSM credential을 설치하지 않는다.
- FakeModel만 model provider로 사용하고, 모든 ITSM request는 injected `httpx.MockTransport`로 처리한다.
- Pytest session의 autouse fixture는 allowlist 없는 default-deny 방식으로 DNS와 동기·비동기 TCP 진입점을 차단한다. MockTransport와 in-process ASGI transport는 socket을 사용하지 않는다.
- Deliberate bypass probe는 injection을 사용하지 않는 새 `httpx.AsyncClient`와 raw socket을 각각 호출해 DNS lookup 또는 socket I/O 전에 지정된 test exception으로 실패하는지 확인한다.
- Deterministic automation failure는 production 또는 live ITSM tenant 호출로 재시도하지 않는다.
- 실제 smoke가 기존 운영 절차에 있다면 별도 승인과 명시적 credential이 있는 수동 보조 증거일 뿐, blocking deterministic gate를 대체하지 않는다.

## Secrets Management in CI/CD

| Data | Default automation | Existing deployment path | Evidence rule |
|---|---|---|---|
| OpenAI API key | absent; FakeModel only | unchanged existing secret injection | test fixture, command, artifact, log에 값 포함 금지 |
| ITSM delegated credential | invalid deterministic canary/capability handle | current server-session path only | raw value는 gateway 내부 outbound boundary 밖에서 관찰 불가 |
| ITSM client secret | redaction canary only | unchanged server-side configuration | 기본 test 실행에 실제 값 불필요 |
| Refresh-envelope signing key | 실제 key 없이 invalid deterministic config와 test key ring만 사용 | 기존 secret injection 경계가 `TICKET_REFRESH_KEYS_JSON`, `TICKET_REFRESH_CURRENT_KID`, `TICKET_REFRESH_VERIFICATION_SECONDS`를 제공한다. `Settings`/`AgentService`가 signer와 verifier를 분리하고 raw key를 노출하지 않는다. | 설정 3종·owner·86,400~604,800초 lifetime·current/previous `kid` rotation 계약, raw-key 출력 0, restart/rotation/retired-key contract test |
| Authorization header | MockTransport marker/capture with redacted value | outbound boundary에서만 구성 | raw header는 evidence에서 제외 |
| Idempotency key/canonical bytes | deterministic unique canary and hash/length evidence | U2 ledger and gateway boundary only | 값 대신 equality/count/digest assertion만 보존 |

CI evidence에는 allowlisted error code, safe opaque request ID, count와 digest 비교 결과만 남긴다. 의도적으로 실패하는 isolated subprocess도 stdout, stderr, traceback과 assertion diff에서 canary 0건을 입증해야 한다.

## Artifact and Evidence Management

| Artifact | Contents | Confidentiality | Retention owner |
|---|---|---|---|
| Sanitized pytest result | pass/fail/skip counts and safe failure locations | payload/header/credential/key/bytes 없음 | existing CI/promotion system |
| `coverage.json` | application file/line metrics | source path and line metrics only | existing CI/promotion system |
| Changed-line summary | base commit, included paths, covered/total and percentage | source path and counts only | existing CI/promotion system |
| Concurrency evidence | barrier names, affected-row counts, POST/refresh/publication counters | actor/payload/claim/key raw values 없음 | existing CI/promotion system |
| Migration/retention evidence | schema names, row counts, boundary timestamps and pass/fail | credential/canonical bytes 없음 | existing CI/promotion system |
| Rollback rehearsal receipt | last-known-good artifact identity, migrated DB schema digest, state별 row counts, immutable-field digest와 pass/fail | raw actor, key, bytes, credential 없음 | existing CI/promotion system |
| Verification summary | Python/dependency identity and every blocking gate result | allowlisted metadata only | existing CI/promotion system |
| Application artifact | existing FastAPI application including U2 library | existing application classification | existing deployment system |

새 evidence retention 기간은 설정하지 않는다. 기존 시스템의 현행 정책을 유지하되 raw tool trace, external body, secret, key 또는 canonical bytes를 저장하지 않는다.

## Deployment and Promotion Strategy

| Facet | Decision | Rationale |
|---|---|---|
| Deployable unit | existing FastAPI application artifact | U2는 독립 deployable service가 아님 |
| Runtime resources | existing process, application-lifetime AsyncClient and Server Session SQLite | 새 runtime resource가 필요하지 않음 |
| Database change | additive `ticket_tools_create_v1.ticket_create_attempts` migration and optional claim/refresh fields | 승인된 C-04 ownership과 restart durability 구현 |
| Staging promotion | all gates 뒤 existing on-merge/current external process | 팀 관행이 기존 경로 유지를 확정 |
| Production promotion | existing separate manual approval | 조직 규칙 유지 |
| Deployment strategy | unchanged and unspecified | repository에 vendor/topology 근거 없음 |
| Feature flag | none added | 기존 registry/contract/test gate가 release boundary이고 flag system 근거가 없음 |
| Refresh activation | REFRESH-U2-01~03 contract/configuration tests가 모두 통과한 artifact에서만 활성화 | 설정 부재·오류·unknown/retired `kid`는 fail closed하고 refresh가 필요한 ticket POST를 허용하지 않음 |

Startup은 기존 application migration 순서에서 U2 additive migration을 적용한 뒤 ticket-write registration을 활성화한다. Migration 실패 시 새 버전은 ticket-write behavior를 제공하지 않고 승격을 중단한다.

## Rollback Design

1. 기존 deployment mechanism으로 failed promotion을 중단하거나 새 whole-application artifact를 제거한다.
2. 마지막 known-good application artifact를 복원하고 U2 module만 부분 rollback하지 않는다.
3. `ticket_tools_create_v1` table과 additive claim/refresh fields, retention 중인 row를 삭제하거나 downgrade하지 않는다. Destructive down-migration은 duplicate-create 조정 증거와 보존 의무를 훼손한다.
4. Stage-to-Gate order 10에서 직전 release가 unknown table/optional fields를 무시하고 기존 session/login/logout/chat read path를 수행할 수 있음을 U2 migration이 적용된 disposable representative DB copy로 검사한다. DB copy는 non-expired `prepared`, `in_flight`, `ambiguous`, `completed` row를 포함해야 하며, rehearsal 전후 U2 schema, state별 row count, `retained_until`, claim state와 immutable key/bytes digest가 동일해야 한다. Receipt는 last-known-good artifact identity와 migrated schema fingerprint에 결합한다.
5. Rehearsal이 실패하면 code rollback도 차단하고 현재 U2 ledger와 application version을 그대로 보존한 채 forward-fix만 허용한다. 이 U2 pipeline은 database restore를 rollback 수단으로 허용하지 않는다.
6. 특히 U2 write 이후 시점보다 오래된 DB snapshot restore는 non-expired `ticket_create_attempts` row, claim state와 동일 key·bytes reconciliation evidence를 잃을 수 있으므로 금지한다. 별도 disaster-recovery 절차가 필요하면 모든 U2 row와 schema를 손실 없이 보존·병합하고 retention·claim 불변식을 재검증하는 별도 설계와 승인을 먼저 받아야 하며, 이 문서는 그 절차를 승인하지 않는다.
7. Rollback 뒤 pending reference나 ambiguous row를 성공 근거로 사용하지 않는다. Forward redeploy는 같은 ledger/key/bytes와 current state를 복원해 정상 reconciliation 규칙을 적용한다.
8. Incident evidence에는 safe request ID와 gate counts만 사용하고 raw credential, header, upstream body, idempotency key 또는 canonical bytes를 복사하지 않는다.

## Failure and Retry Policy

| Failure | Pipeline action | Retry allowance |
|---|---|---|
| Dependency installation or lock mismatch | tests 전에 중단 | repository/dependency issue 수정 후 재실행 |
| Contract or migration mismatch | 승격 중단 | approved contract와 ownership에 맞춘 뒤 재실행 |
| Refresh provider signature 또는 stable key contract 미승인 | Code Generation의 refresh 구현, merge와 승격 중단 | 상위 계약/기술 결정을 승인하고 shared fixture를 통과한 뒤 재실행 |
| Test failure | sanitized result를 보존하고 승격 중단 | code/test/environment 수정 후만 재실행; flaky auto-pass 금지 |
| Unexpected external network | 즉시 실패 | isolation/injection defect 수정 전 재시도 없음 |
| Secret/key/body canary 발견 | 즉시 실패하고 unsafe artifact publication 중단 | leak와 이미 남은 evidence를 교정한 뒤 재실행 |
| CAS owner/count invariant failure | 즉시 실패 | concurrency/state design 수정 후 재실행; timing sleep으로 우회 금지 |
| Coverage below 80% or denominator absent | 승격 중단 | legitimate test, coverage helper 또는 Git diff scope 오류 수정; threshold 하향 금지 |
| Multi-process deployment detected | 승격 중단 | shared coordination design 승인 후만 재개 |
| Rollback compatibility rehearsal failure 또는 receipt binding mismatch | destructive restore와 code rollback을 모두 중단하고 ledger-preserving forward-fix로 전환 | 같은 artifact/schema binding의 rehearsal이 통과한 뒤에만 rollback 재허용 |
| Existing deployment failure | 현행 rollback 실행 | existing deployment system이 retry 결정 |
| Optional real smoke unavailable | deterministic gate 결과를 재해석하지 않음 | 별도 운영 절차만 따름 |

## Ownership and Handoff

| Responsibility | Owner |
|---|---|
| `code-generation-plan.md`의 `## Planned Source Set`, `source-manifest.json`, 실제 Git diff의 exact set binding | U2 Code Generation이 projection 생성; Code Generation Plan Approval과 architecture review가 승인·검증 |
| U1 public confirmation/gateway/refresh ports and existing runtime boundaries | U1 contract owner; U2 consumes only the approved public ports |
| Stable refresh-envelope configuration schema와 rotation lifecycle | `app.config.Settings`와 기존 deployment secret injection 경계; `AgentService`가 U2 signer/U1 verifier를 분리 조립 |
| Exact full-suite, network isolation and coverage execution | existing CI/promotion runner or local release verifier |
| Final three-tool assembly, performance trials, README and whole-feature verification | U4 Release Assurance |
| Existing staging/production deployment, approval and rollback | current external deployment process |
| New CI provider, workflow, cloud resource or distributed coordinator | out of scope; no owner created by this feature |

## Release Gate Summary

U2는 Python/dependency identity, C-01/C-03A/C-04/C-07 exact contract, REFRESH-U2-01~03의 provider/consumer·설정·rotation 계약, plan/manifest/diff의 exact source binding, additive migration ownership, ledger-first publication, current-turn confirmation evidence, send claim과 no-I/O reconciliation finalization, one-shot credential refresh, refresh-used second-401 terminalization, same-key/same-bytes two-POST ceiling, authoritative ticket-ID success, 24-hour retention, process-level network default-deny, secret/key/body non-disclosure, full regression, 80% coverage와 migrated representative DB rollback rehearsal이 모두 통과한 뒤에만 기존 deployment path로 넘긴다. Rollback은 exact artifact/schema-bound rehearsal evidence가 있을 때만 허용하고, 그렇지 않으면 ledger-preserving forward-fix를 사용한다. 이 pipeline은 runtime infrastructure를 추가하지 않고 기존 production approval 또는 rollback control을 완화하지 않는다.
