# U3 Ticket Update — CI/CD 및 승격 설계

## Sources

- `construction/u3-ticket-update/nfr-design/security-design.md` — trust boundary, migration·storage, retry·refresh, response-loss 및 release evidence 설계
- `construction/u3-ticket-update/nfr-design/logical-components.md` — U3 component ownership, U1 port dependency와 startup ordering
- `inception/domain-design/components.md` — 기존 FastAPI modular monolith, Server Session SQLite, Agent·Runner와 외부 ITSM 경계
- `construction/u3-ticket-update/functional-design/functional-spec.md` — prepare/revise/confirm/cancel, crash recovery와 상태 전이
- `inception/contract-design/contract-summary.md` — C-02·C-05·C-07의 typed port, migration, PATCH/refresh와 verification 계약
- `construction/u3-ticket-update/infrastructure-design/infrastructure-design-questions.md` — 새 runtime infrastructure와 CI provider를 추가하지 않는 확인된 방향
- `construction/u3-ticket-update/code-generation/code-generation-plan.md` — 승인된 U3 source/test 경로와 구현 순서
- `construction/u3-ticket-update/code-generation/source-manifest.json` — U3가 실제로 claim한 application/test source 경로
- `.aidlc-engine/source-review/code-generation/baseline-6532efa31d44.tsv` — code-generation source baseline; SHA-256 `6532efa31d446f68d70750db198e34c6ed4fe82b1fd17b96997a71a4db79a711`

## Infrastructure Applicability

U3는 `service`, `ui`, `packaging` Unit이 아닌 기존 애플리케이션 안의 `library` Unit이다. 새 compute, network, queue, cache, database service, container, cloud account, IaC stack, CI workflow 또는 별도 deployment pipeline을 만들지 않는다. 따라서 이 단계의 적용 가능한 산출물은 기존 저장소 밖 승격 경로가 실행해야 할 검증 계약인 이 문서와 `traceability.json`뿐이다.

| Facet | Choice | Rationale |
|---|---|---|
| Compute | 기존 Python 3.13 FastAPI process | 새 서비스 금지와 기존 Agent·Runner 수명주기 보존 |
| Network | 기존 same-origin browser ingress와 application-lifetime `httpx.AsyncClient` egress | 새 endpoint·proxy·VPC 변경 없이 C-06·C-07 유지 |
| Storage | 기존 Server Session SQLite 안의 U3 전용 `ticket_tools_update_v1.pending_update_executions` | 새 database 없이 durable patch material과 crash recovery 제공 |
| Concurrency | 기존 single-process per-conversation serialization + SQLite transaction/CAS | 현재 배포 가정에서 confirm/revise와 publication 경쟁을 결정적으로 중재 |
| Environments | 기존 저장소 밖 dev/staging/production 경로 | 저장소에 없는 환경 topology나 provider를 추측해 만들지 않음 |
| IaC | 추가 없음 | 새 cloud resource가 없고 기존 배포 경계를 유지함 |
| Promotion | 기존 외부 승격 경로에 아래 blocking test contract를 연결 | provider 종속 workflow 없이 재현 가능한 release evidence 제공 |

## Promotion Preconditions

다음 조건은 U3 merge 또는 어떤 환경으로의 승격보다 먼저 모두 충족되어야 한다.

| ID | Blocking condition | Required evidence | Failure effect |
|---|---|---|---|
| `PIPE-U3-01` | dependency와 runtime pin이 승인된 brownfield baseline과 일치 | Python 3.13, FastAPI, Pydantic, Agents SDK, httpx, pytest, coverage의 설치·pin 검증 | build 중단 |
| `PIPE-U3-02` | C-02·C-05·C-07의 required type·port·field·attempt limit가 현재 contract와 일치 | `UpdatePendingReplacementV1` 정의의 old/new mutation ID, actor binding, committed/affected-row invariant와 closed-field policy를 포함한 provider/consumer contract fixture 및 fingerprint check | type 정의가 없거나 reference만 존재해도 Code Generation·merge·승격 중단 |
| `PIPE-U3-03` | U3 migration이 U1 state migration 뒤, plugin registration 전에 성공 | migrated-copy startup test, marker/schema/index fingerprint, order spy | U3 plugin activation 중단 |
| `PIPE-U3-04` | namespace ownership과 schema isolation 유지 | U1·U2 write-spy 0건, U3 table·index inventory | merge 중단 |
| `PIPE-U3-05` | 전체 automated test green | 실제 OpenAI·ITSM 호출 없는 `pytest` 결과 100% pass | merge 중단 |
| `PIPE-U3-06` | 고정 U3 baseline 이후 U3 manifest가 claim한 changed executable application lines coverage ≥80%; denominator 0은 실패 | 승인 plan, strict manifest, baseline digest와 검증 대상 commit에 결합된 `coverage.py` JSON 및 `scripts/changed_line_coverage.py` 판정 | merge 중단 |
| `PIPE-U3-07` | unexpected external network 0건 | process-level DNS/TCP default-deny와 deliberate bypass probe | merge 중단 |
| `PIPE-U3-08` | secret·patch·header canary 노출 0건 | model input, tool schema/result, HTTP response, UI, log, exception과 test-failure capture sweep | merge 중단 |
| `PIPE-U3-09` | update authority·attempt·crash invariant 모두 충족 | deterministic counters, SQLite snapshots, fake clock/barrier/restart matrix | merge 중단 |
| `PIPE-U3-10` | 기존 session, history, fixed model/reasoning/tracing, UI/API 회귀 0건 | 전체 regression suite와 response/browser snapshots | merge 중단 |
| `PIPE-U3-11` | U4 outcome evidence가 최종 release에서 충족 | 동일 조건의 방식별 유효 trial 3회, Assistant median 개선, 외부 화면 전환 0회 | production release 중단 |
| `PIPE-U3-12` | Server Session SQLite와 backup의 data-at-rest 통제가 승인된 기존 정책 이상 | runtime DB·parent path의 owner/ACL, disk protection, session cleanup window, backup 포함 여부·암호화·접근 주체·retention evidence | evidence 누락, 과도한 ACL, 무보호 disk, 평문·무제한 backup 또는 기존보다 긴 retention이면 production release 중단 |
| `PIPE-U3-13` | 검증 직후 한 번 생성·봉인한 deployment artifact를 staging과 production이 byte-for-byte 동일하게 사용 | source commit, packaging recipe ID, immutable artifact locator, byte size와 SHA-256; staging/production deployment receipt의 동일 digest | artifact 재빌드, mutable locator, digest 불일치 또는 receipt 누락이면 승격 중단 |

## Ordered Verification Pipeline

| Order | Stage | Inputs | Blocking assertions | Evidence retained |
|---:|---|---|---|---|
| 1 | Source binding and baseline | clean committed checkout의 승인된 U3 plan, strict `source-manifest.json`, engine-captured source baseline과 fixed base commit | 검증 전후 `git status --porcelain=v1 --untracked-files=all`이 empty이고 `HEAD`가 unchanged; manifest schema/unit/version/unique path 유효; claim이 승인 plan 안에 있고 baseline digest가 고정값과 일치; fixed base commit은 tested `HEAD`의 ancestor; U1·U2·U4 other-Unit manifest claim은 U3 denominator와 unapproved-change 판정에서 제외 | pre/post clean-status output, plan·manifest·baseline digest, all four Unit manifest digests, fixed base commit, tested `HEAD`, resolved U3 path set |
| 2 | Contract drift | C-02, C-05, C-07와 generated/shared schemas | exact-old replacement, update refresh port, execution store, total PATCH ceiling이 누락·완화되지 않음 | contract digest와 provider/consumer results |
| 3 | Migration and storage | 기존 session DB copy, empty DB, partially-failing migration fixture | U1 → U3 → cleanup/recovery → plugin 순서; second startup no-op; rollback 뒤 partial schema·marker 0; single-active partial unique index 존재 | schema/index snapshot, affected rows, activation count |
| 4 | Repository and publication | staged/active/retired fixtures와 injected SQLite failures | U1 failure 때 old review 유지; U3 activation은 exact old retire + new promote의 한 transaction; actor scope active row ≤1 | before/after row snapshots와 transaction counters |
| 5 | Identity and confirmation | FakeModel, raw-turn fixtures, actor/target/hash/version matrix | current session + exact binding + atomic confirm/consume 없으면 consume/PATCH 0 | consume evidence count, transport count |
| 6 | Detail read policy | MockTransport, fake monotonic clock와 retry outcome matrix | read ≤2; retry는 timeout·transport·500/502/503/504만; 정확히 250ms; deadline 밖 second call 0 | call timestamps, outcome sequence, elapsed time |
| 7 | PATCH and refresh policy | strong ETag fixtures, MockTransport, durable refresh rows | 일반 PATCH ≤1; authoritative no-apply `token_expired` 401만 PATCH ≤2·refresh port ≤1; bytes와 `If-Match` 동일; 다른 401·412·428·timeout·429 hidden retry 0 | request bytes/header digests, patch/refresh/sleep counters |
| 8 | Crash and response loss | stage/replacement/activation/consume/refresh/network 경계 restart snapshots | authority 추측 0; second refresh 0; same actor/ticket pending만 복구; duplicate pending 0; version drift PATCH 0 | restart state table, locator result count, public state |
| 9 | Reconciliation and presentation | latest-detail fixtures, malformed responses, external-text canaries | 완전한 expected changes + version 증가만 success; partial/unknown success 0; text fallback과 safe next action 유지 | result/presentation snapshots, success publication count |
| 10 | Full regression and coverage | 전체 repository test set와 coverage data | tests 100% pass; changed executable application lines ≥80%; actual external network 0 | junit/terminal result, coverage JSON, changed-line report |
| 11 | Artifact seal | order 1~10을 통과한 clean `HEAD`와 기존 deployment packager의 단일 output | regular-file artifact를 한 번만 생성; source commit·recipe ID·size·SHA-256을 immutable locator에 결합; 이후 환경에서 rebuild 금지 | sealed artifact identity record와 package command/exit status |
| 12 | Data-at-rest release check | runtime Server Session SQLite, parent directory와 운영 backup policy | POSIX DB `0600`·parent `0700` 또는 플랫폼상 owner process만 read/write 가능한 동등 ACL; disk protection 확인; backup 암호화·접근 주체·retention이 기존 session-state 정책보다 약하거나 길지 않음 | redacted storage-control evidence record와 policy comparison verdict |
| 13 | Release assurance | U4 integrated Agent와 generated ticket fixtures | tool 이름 정확히 세 개; update evidence aggregation; 동일 조건 3+3 trial과 median 판정; staging·production receipt가 order 11의 digest와 일치 | U4 release manifest, anonymized measurement ledger와 immutable artifact receipts |

각 stage는 앞 단계가 실패하면 뒤 단계로 진행하지 않는다. 테스트 실패를 숨기기 위한 retry, test skip, threshold 완화 또는 evidence 수기 수정은 허용하지 않는다.

## Required Test Matrix

| Evidence family | Minimum cases | Observable invariant |
|---|---|---|
| Schema and validation | 여덟 허용 field, omitted/null, forbidden/unknown, no-op | invalid case PATCH 0 |
| ETag and version | valid strong quoted decimal, missing, weak, non-decimal, body mismatch | invalid pair review/PATCH 0; valid `If-Match` byte exact |
| Confirmation binding | raw `확인`/`confirm`, embedded text, model claim, actor/session/conversation/ticket/hash/version mismatch, expiry | exact current-turn match 외 consume/PATCH 0 |
| Publication | prepare, exact-old revise, stale old, insert failure, activation failure, concurrent confirm/revise | old review preservation; winner ≤1; loser PATCH 0 |
| Read attempts | success, timeout, transport, 500/502/503/504, other 4xx, 429, malformed, deadline exhausted | 허용 outcome에서만 call 2; delay 250ms; 그 밖에는 call 1 |
| PATCH attempts | success, 412, 428, timeout, transport, typed/untyped 401, repeated 401, 429 | 기본 call 1; safe-401만 최대 2; refresh ≤1; 429 sleep 0 |
| Refresh recovery | commit 전 crash, commit 뒤 response loss, same/higher credential generation | port 재호출 0; higher generation만 committed recovery |
| Lifecycle | switch, logout, clear, session expiry, pending terminal/missing, repeated cleanup | 즉시 non-authority; cleanup idempotent; cutoff 전 required row 보존 |
| Response loss | active 후 response drop, restart, actor/ticket mismatch, version drift | same pending recovery 0 또는 1; duplicate pending 0; drift PATCH 0 |
| Security and presentation | unique secret/patch/header/external-text canaries, malformed result, review·confirmation·cancel·success·auth error·conflict·rate limit·ambiguous·invalidated·unavailable 상태 | leak 0; instruction effect 0; 권위 증거 없는 success 0; 각 상태의 plain-text label과 safe next action 존재; keyboard/screen-reader snapshot 통과 |
| Regression | existing session/history/UI/API/model settings와 exact-three-tool assembly | 승인되지 않은 diff 0 |

## Commands and Evidence Contract

구현 전 baseline과 최종 Construction checkpoint는 프로젝트 root에서 기록된 Construction Verification Command를 실행한다.

```bash
.venv/bin/python -m coverage run --source=app -m pytest -q && .venv/bin/python -m coverage report --fail-under=80
```

U3 promotion evidence는 아래 하나의 fail-fast chain으로 한 번만 pytest를 실행한다. Promotion runner는 committed `HEAD`의 clean checkout만 받으며 시작과 종료 시 tracked·untracked change가 하나라도 있으면 실패한다. 따라서 helper가 계산하는 base-to-working-tree diff는 base-to-tested-`HEAD` committed diff와 동일하고, 검증한 bytes는 `aidlc_u3_tested_head`가 식별한다. `aidlc_u3_base`는 U3 검증 계약에 고정된 source base commit이며 매 실행 시 `main`에서 다시 계산하지 않는다. `aidlc_u3_baseline`은 engine-captured source baseline이고 digest가 다르면 실행을 중단한다. 모든 coverage consumer는 동일 `.venv` interpreter, unchanged tested `HEAD`와 동일 `coverage.json`을 사용한다. `scripts/changed_line_coverage.py`는 U3 manifest·승인 plan·baseline을 함께 검증하고 U1·U2·U4 manifest claim을 다른 Unit 변경으로 분리하며, U3 changed executable line denominator가 0이면 실패한다. 마지막 전체-source 80% 판정은 NFR6.1의 manifest-bound changed-line 80%보다 강한 조직 기본값을 추가로 확인하며, 이를 changed-line 판정의 대체물로 취급하지 않는다.

```bash
aidlc_u3_base=89f48f9372635f443c719b7d64ca6900585bb112 && \
  aidlc_u3_baseline=aidlc/spaces/default/intents/261024-itsm-ticket-tools/.aidlc-engine/source-review/code-generation/baseline-6532efa31d44.tsv && \
  test -z "$(git status --porcelain=v1 --untracked-files=all)" && \
  aidlc_u3_tested_head=$(git rev-parse --verify 'HEAD^{commit}') && \
  git cat-file -e "${aidlc_u3_base}^{commit}" && \
  git merge-base --is-ancestor "$aidlc_u3_base" "$aidlc_u3_tested_head" && \
  test "$(.venv/bin/python -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$aidlc_u3_baseline")" = 6532efa31d446f68d70750db198e34c6ed4fe82b1fd17b96997a71a4db79a711 && \
  .venv/bin/python -m coverage erase && \
  .venv/bin/python -m coverage run --branch --source=app -m pytest -q && \
  .venv/bin/python -m coverage json -o coverage.json && \
  .venv/bin/python scripts/changed_line_coverage.py \
    --base "$aidlc_u3_base" \
    --coverage-json coverage.json \
    --source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/code-generation/source-manifest.json \
    --prior-source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/code-generation/source-manifest.json \
    --prior-source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/code-generation/source-manifest.json \
    --prior-source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u4-release-assurance/code-generation/source-manifest.json \
    --approved-plan aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/code-generation/code-generation-plan.md \
    --source-baseline "$aidlc_u3_baseline" \
    --include 'app/**/*.py' \
    --fail-under 80 && \
  .venv/bin/python -m coverage report --fail-under=80 && \
  test "$(git rev-parse --verify 'HEAD^{commit}')" = "$aidlc_u3_tested_head" && \
  test -z "$(git status --porcelain=v1 --untracked-files=all)"
```

| Evidence field | Rule |
|---|---|
| Baseline | fixed base commit `89f48f9372635f443c719b7d64ca6900585bb112`, unchanged tested `HEAD`, source-baseline path와 SHA-256, pre/post clean-status result; 모두 한 evidence record에 고정 |
| Source binding | U3 plan·manifest digest, U1·U2·U4 other-Unit manifest digest, resolved U3 application path set과 non-zero changed executable line set |
| Commands | complete argv와 chain의 각 exit code; 단일 `.venv` interpreter identity; credentials and secret-valued environment data excluded |
| Tests | passed/failed/skipped counts and failing test IDs; captured raw provider payload excluded |
| Coverage | included changed files, covered/total executable changed lines, percentage and threshold |
| Network | denied DNS/TCP attempt counts and deliberate bypass probe result |
| Safety counters | detail read, PATCH, refresh, consume, active-row, pending-row and success-publication counts |
| Database | schema/index fingerprint and redacted row-state snapshots without canonical patch bytes |
| Data-at-rest | normalized DB/parent path reference, owner process identity, platform·ACL class, owner-only 판정, disk-protection mechanism/status, session cleanup window; backup included 여부·encryption status·접근 주체 class·retention과 기존 정책 비교. Secret, credential, canonical bytes와 backup content는 기록 금지 |
| Reproducibility | Python/dependency versions, commit, platform and UTC execution time |

`coverage.json`, raw logs 또는 failure artifacts에 canonical patch bytes, `IfMatchVersion`, Authorization, credential, raw problem detail을 넣지 않는다. Hash와 allowlisted state/counter만 evidence로 보존한다.

## Artifact Identity and Promotion Contract

새 registry나 배포 provider를 선택하지 않는다. 대신 기존 저장소 밖 packager와 deployment 경로가 다음 provider-neutral blocking interface를 충족해야 한다. 충족하지 못하면 U3를 staging 또는 production으로 승격하지 않는다.

| Field | Contract |
|---|---|
| `source_commit` | order 1~10을 통과한 clean checkout의 `git rev-parse --verify 'HEAD^{commit}'`; 이후 source 변경은 새 검증과 새 artifact를 요구 |
| `packaging_recipe_id` | 기존 packager command와 version/config digest를 식별하는 immutable ID; secret-valued argument는 제외 |
| `artifact_locator` | 한 번 게시된 뒤 bytes가 바뀌지 않는 기존 artifact-store locator; mutable tag나 working-directory path 금지 |
| `artifact_size_bytes` | sealed regular file의 정확한 byte length |
| `artifact_sha256` | sealed regular file bytes의 SHA-256; staging·production·rollback receipt가 이 값을 재계산·대조 |
| `created_at_utc` | order 1~10 성공 뒤 artifact를 한 번 생성·봉인한 시각 |

Order 11 runner는 `AIDLC_RELEASE_ARTIFACT_PATH`가 가리키는 기존 packager의 단일 regular-file output을 대상으로 source commit, recipe ID, size와 SHA-256을 한 번 기록한다. 이 값들을 immutable locator와 함께 atomically finalized evidence record에 저장한 뒤 local mutable path를 promotion authority로 사용하지 않는다. Staging은 locator에서 받은 bytes의 digest를 대조한 뒤 배포하고 receipt에 `source_commit`·`artifact_sha256`을 남긴다. Production은 staging receipt와 같은 locator·digest의 artifact를 승격하며 rebuild를 금지한다. Rollback도 이전에 검증·봉인된 receipt의 exact digest만 사용한다. 어떤 환경이 다른 bytes를 선택하거나 재빌드했거나 digest를 재현하지 못하면 `PIPE-U3-13`이 실패한다.

## Secrets and Network Controls

- Runtime secret source, server-session credential persistence와 rotation 경계는 기존 U1 `IdentitySession`을 유지한다. U3와 CI는 새 secret store나 credential 환경변수를 만들지 않는다.
- 실제 OpenAI API와 ITSM API 호출은 automated pipeline에서 금지한다. FakeModel과 `httpx.MockTransport`가 모든 정상·실패·recovery path를 제공한다.
- Network default-deny fixture는 DNS lookup, raw socket과 일반 HTTP client 우회를 모두 실패시킨다. Deliberate bypass probe가 실제로 차단되는지 별도 assertion한다.
- 테스트 output은 credential value 대신 source category(`delegated`, `service`, `none`)와 opaque request correlation만 기록한다. Ticket operation에서 `service` category count는 0이어야 한다.
- 실제 ITSM/OpenAI smoke는 이 automated pipeline 밖에서 별도 운영 승인, 격리된 환경과 명시적 credential이 있을 때만 수행하며 본 Unit의 merge 증거를 대체하지 않는다.

## Promotion and Deployment Strategy

| Environment step | Trigger | Gate | Result |
|---|---|---|---|
| Developer/Unit | U3 code change | targeted layer tests immediately after each testable layer | local implementation evidence |
| Merge candidate | Unit implementation complete | `PIPE-U3-01`~`PIPE-U3-10` 모두 통과 | tested source commit |
| Artifact seal | tested source commit | 기존 packager를 한 번 실행하고 `PIPE-U3-13` identity record를 atomic finalize | immutable locator와 source commit·recipe·size·SHA-256 |
| Staging | 기존 외부 승격 절차 | unified promotion evidence, migration rehearsal, network/canary gates + sealed digest 재검증 | `PIPE-U3-13`의 exact artifact 배포와 staging receipt |
| Production | 기존 외부 수동 승인 | staging receipt의 exact digest + `PIPE-U3-12` storage-control evidence + U4 `PIPE-U3-11` release manifest + 기존 승인자 | rebuild 없이 같은 artifact digest를 production으로 승격 |

Deployment topology와 strategy(rolling, canary, blue-green 등)는 저장소 밖 기존 절차가 소유한다. 이 문서는 관찰되지 않은 provider나 방식을 새로 선택하지 않는다. 어떤 방식이든 U3 migration은 application activation 전에 완료되고 schema fingerprint가 일치해야 한다.

## Rollback and Recovery

1. 승격 전 기존 절차로 `PIPE-U3-13`의 sealed application artifact와 Server Session SQLite backup/restore capability를 확인한다. Backup의 접근 통제·암호화·retention은 기존 session-state 정책보다 약하거나 길어질 수 없다.
2. Migration 또는 schema fingerprint 검증이 실패하면 U3 plugin을 등록하지 않고 기존 application version을 계속 유지한다. Partial schema와 marker는 SQLite transaction rollback으로 남지 않아야 한다.
3. Application 배포 뒤 U3 regression이 발견되면 이전의 검증·봉인 receipt가 지목하는 exact `artifact_sha256`로 되돌린다. Rollback 중 rebuild나 mutable tag 재해석은 금지한다. `ticket_tools_update_v1`은 additive namespace이므로 row/table/index를 자동 삭제하거나 downgrade하지 않는다.
4. Rollback된 version이 U3 namespace를 모르면 이를 그대로 무시해야 한다. 호환성을 입증하지 못하면 database snapshot rollback 대신 배포를 중단하고 운영 검토를 요구한다.
5. Active/consumed/ambiguous row를 성공으로 추측하거나 새 PATCH authority로 바꾸지 않는다. 재승격은 migration fingerprint, cleanup/recovery와 전체 verification을 다시 통과해야 한다.
6. 다중 process 또는 multi-host deployment가 필요해지면 기존 per-conversation serialization만으로 승격하지 않는다. Shared lock 또는 동등한 database arbitration을 먼저 설계·검증한다.

## U4 Release Handoff

U3는 U4에 다음 evidence를 전달한다.

- C-02 provider/consumer contract 결과와 C-05 verification manifest 완료 상태
- migration order, schema/index fingerprint, idempotent restart와 rollback 결과
- exact-old replacement, single-active activation, atomic confirm/consume, crash/restart와 response-loss matrix
- detail read/PATCH/refresh/sleep/network/success-publication counters
- secret·patch·header·external-text canary sweep 결과
- full regression과 changed-code coverage 보고서
- fixed base·U3 source baseline·approved plan·manifest digest 및 non-zero changed-line denominator
- source commit·packaging recipe·immutable locator·artifact size·SHA-256와 staging deployment receipt
- generated fixture factory와 Assistant 수정 시작/종료 instrumentation contract

U4는 exact-three-tool assembly, 전체 suite와 release evidence를 집계하고, 동일 actor·deployment·browser/device·network·warm-cache 조건에서 기존 ITSM UI와 Assistant를 각각 유효 3회 측정한다. Assistant median이 더 짧고 모든 Assistant trial의 `external_screen_transitions=0`일 때만 NFR8.1을 통과시킨다.

## Assumptions & Open Questions

None.
