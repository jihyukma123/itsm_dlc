# U4 Infrastructure Specification

## Sources

- `../nfr-design/performance-design.md`
- `../nfr-design/security-design.md`
- `../nfr-design/scalability-design.md`
- `../nfr-design/reliability-design.md`
- `../nfr-design/observability-design.md`
- `../nfr-design/logical-components.md`
- `../functional-design/functional-spec.md`
- `../../../inception/domain-design/components.md`
- `../../../inception/contract-design/contract-summary.md`

## Deployment

| Facet | Choice | Rationale |
|---|---|---|
| Compute model | 기존 단일-process Python 3.13 FastAPI 배포를 그대로 사용한다. U4 전용 service, worker, queue 또는 scheduler를 추가하지 않는다. | 기존 배포와 Agent/Runner 수명주기를 보존하고 U4를 test/release-time 보증 경계로 제한한다. |
| Networking topology | production ingress/egress는 기존 경로를 변경하지 않는다. 기본 자동화에서는 pytest process가 in-process transport와 `httpx.MockTransport` 외 DNS/TCP를 거부하고 deliberate bypass probe로 fence를 검증한다. | 실제 ITSM/OpenAI 호출 없는 결정적 검증과 NFR1.4/NFR1.6을 충족한다. |
| Storage strategy | 기존 Server Session SQLite, Agents SDK history SQLite와 U1~U3 migration namespace를 재사용한다. 변경 전 회귀는 `.release-assurance/baselines/<baseline-source-revision>/<baseline-id>/`의 immutable baseline receipt로, 구현 완료본 evidence는 `.release-assurance/runs/<final-source-revision>/<run-id>/`의 immutable bundle로 분리하며 업무 payload와 credential을 저장하지 않는다. | 구현 전·후 서로 다른 revision의 evidence를 한 run에 섞지 않으면서 승격·rollback이 final revision-bound source of truth를 회수하게 한다. |
| Environments | local/승격 검증은 같은 pinned dependency와 명령 계약을 사용한다. 실제 smoke와 NFR8 측정은 credential이 있는 사람이 명시적으로 선택한 기존 실제 환경에서만 별도 수행한다. | 기본 자동화와 실제 연동을 분리하고 재현성과 안전성을 유지한다. |
| IaC approach | 추가 IaC 없음. AWS/CDK/Terraform/CloudFormation resource를 만들지 않는다. | 이번 Unit은 새 runtime infrastructure가 아니라 기존 승격 경로의 blocking evidence를 설계한다. |
| Resource sizing | 새 capacity를 할당하지 않는다. 자동화 catalog 73개는 final revision의 current evidence 72개(C03 15, C04 25, C05 27, REL.02~REL.06 5)와 별도 immutable baseline receipt를 검증하는 current-run `REL.01` reference 1개로 구성한다. 문서는 REL.07, NFR8은 18개 측정 trial로 유한하다. | 승인된 throughput 목표가 없으며 기존 단일-process topology를 유지한다. |
| Deployment strategy | 기존 저장소 밖 승격 경로를 유지한다. U4는 배포 방식을 새로 선택하지 않고 release-assurance predicate가 통과한 revision만 승격 가능하게 한다. | 팀이 확정한 “새 CI/CD 없음, 전체 자동화 통과가 승격 전 조건”을 구현 가능한 계약으로 만든다. |
| Cost impact | 추가 상시 compute, storage, network 또는 관리형 서비스 비용 없음. 테스트 실행 시간과 실제 NFR8 측정 인력만 증가한다. | 새 cloud resource가 없으므로 비용 추정 대상을 실행 시간으로 한정한다. |

## Infrastructure Services

| Service | Role | Configuration | Notes |
|---|---|---|---|
| 기존 FastAPI process | application compute | Python 3.13, single process, 기존 app-scoped async HTTP client | U4가 scaling 또는 process topology를 변경하지 않는다. |
| Server Session SQLite | database | U1 `ticket_tools_state_v1`, U2 `ticket_tools_create_v1`, U3 `ticket_tools_update_v1` namespace와 기존 migration order 유지 | U4는 schema fingerprint와 restart/crash 동작만 검증하며 migration을 소유하지 않는다. |
| Agents SDK history SQLite | database | 기존 SDK history와 U1 `ticket_tools_history_v1` companion metadata | sequence/text-hash correlation, restart restore, text fallback을 회귀 검증한다. |
| pytest process | verification runtime | FakeModel, `httpx.MockTransport`, process-wide network default-deny, deterministic fake clock/barrier | 실제 OpenAI/ITSM 호출은 0이어야 한다. |
| coverage.py | coverage engine | `coverage==7.17.0`, JSON output, U1~U4 source-manifest union, 80% changed executable line threshold | 합집합 application source가 JSON에서 누락되면 line 수와 관계없이 실패한다. |
| Existing promotion path | release gate | finalized evidence bundle의 archive digest와 locator, normalized command ID, command digest, tool version, exit status, output digest와 source revision을 보존 | 공급자별 workflow를 새로 만들지 않으며 기존 경로는 권위 bundle의 projection만 소비한다. |
| Existing real environment | explicit smoke/performance target | credential·대상 환경·일회용 데이터·정리 절차를 사람이 명시적으로 선택할 때만 사용 | 자동화 pass와 smoke/NFR8 결과를 서로 대체하지 않는다. |

새 database, cache, queue, search, CDN, DNS 또는 load balancer는 추가하지 않는다.

## Shared Infrastructure

| Shared Resource | Owner Unit | Consumer Units | Access Boundary |
|---|---|---|---|
| Server Session SQLite | U1 physical DB; U1/U2/U3가 각 namespace 소유 | U1, U2, U3; U4는 검증만 수행 | Unit별 migration namespace를 교차 수정하지 않는다. credential은 기존 server-session field 밖으로 나오지 않는다. |
| Agents SDK history SQLite | U1 AgentConversation | U1, U4 | U4는 public history/presentation contract만 검증하며 raw tool trace를 읽거나 저장하지 않는다. |
| Tool/presentation registry | U1 | U2, U3, U4 | V1 plugin registration만 허용하고 duplicate/unknown version은 fail-closed다. |
| pytest verification process | U4 | U1~U4 contract와 regression suite | network default-deny, FakeModel, MockTransport, safe evidence allowlist를 process 전체에 적용한다. |
| Source manifests | 각 Unit의 Code Generation | U4 CoverageGate | U1~U3 prior manifest와 U4 current manifest를 정규화·digest한 뒤 합집합을 denominator로 사용한다. |

## Evidence Storage and Revision Boundary

### Authoritative evidence bundle

권위 매체는 workspace-relative `.release-assurance/` 아래의 immutable bundle 하나다. 이 디렉터리는 Code Generation에서 VCS 제외 대상으로 추가하며, 기존 승격 경로는 finalized bundle 전체를 `release-assurance-<source-revision>-<run-id>`라는 immutable build artifact로 보존한다. terminal summary, dashboard와 배포 승인 화면은 이 bundle의 projection일 뿐 독립 source of truth가 아니다.

| Path | Owner/access | Atomicity and lifecycle |
|---|---|---|
| `.release-assurance/baselines/<baseline-source-revision>/<baseline-id>/baseline.json` | baseline runner만 finalize 전 owner-write; final runner와 promotion은 read-only | 구현 시작 전에 `REGRESSION_FULL_V1`을 실행한 revision, normalized command와 environment fingerprint를 고정한다. sibling temp file + flush/fsync + `os.replace` 뒤 directory를 immutable로 봉인하고 receipt digest를 계산한다. |
| `.release-assurance/pending/<run-id>/run.json` | 구현 완료 뒤 생성된 현재 assurance runner만 owner-write; 다른 runner와 promotion은 접근 금지 | final source revision이 고정된 뒤 exclusive `run.lock` 아래 생성하며 run ID, final source revision, baseline receipt locator/digest, predecessor run locator/digest와 environment fingerprint를 고정한다. |
| `.release-assurance/pending/<run-id>/evidence/baseline-reference.json` | current final runner만 write; finalizer와 promotion은 read-only | final source revision에서 `REL.01`을 판정한 locator/digest-only `BaselineReceiptReference`다. final run ID/revision, baseline locator/digest/revision, expected command/environment digest와 validation result/time만 저장하고 baseline 실행 count·output digest·실행 시각을 복사하지 않는다. |
| `.release-assurance/pending/<run-id>/evidence/<evidence-id>.json` | 현재 runner만 write | allowlist schema 검증 뒤 sibling temp file에 쓰고 flush/fsync 후 `os.replace`한다. 각 record는 run ID/source revision을 중복 보유한다. |
| `.release-assurance/pending/<run-id>/coverage-inputs.json` | Coverage freeze command만 write; collector/gate는 read-only | coverage 실행 전에 manifest·approved-plan·attempt-baseline path/digest와 sorted union/digest를 원자적으로 고정한다. |
| `.release-assurance/runs/<source-revision>/<run-id>/` | finalize 뒤 immutable; promotion/rollback은 read-only | finalizer가 lock 아래 required evidence set과 digest를 검증하고 `final.json`을 temp+replace로 쓴 뒤 pending directory를 final path로 atomic rename한다. `final.json` 이후 write는 거부한다. |

- baseline receipt와 final run에는 각각 한 writer만 허용한다. 서로 다른 runner는 서로 다른 baseline ID/run ID를 사용하며 서로 다른 revision의 evidence를 합치지 않는다.
- baseline 회귀 실행 record는 current final run의 evidence가 아니다. final run은 immutable baseline receipt의 locator/digest, baseline source revision, command digest와 environment fingerprint를 `BaselineReceiptReference`로만 참조하며 baseline count·output·execution record를 복사하거나 자기 revision의 evidence로 가장하지 않는다.
- 73개 automation 판정은 `72 current-final-revision VerificationEvidence + 1 current-run REL.01 BaselineReceiptReference`의 합성이다. REL.01 reference validator가 locator/digest로 baseline receipt를 다시 읽어 receipt 자체의 exit 0·failed 0·skipped 0, 불변성, command/environment 호환성을 검증한다. reference가 stale·mutable·unresolvable하거나 final run identity와 맞지 않으면 73/73은 실패한다.
- Functional Design의 `RegressionExecutionEvidence(phase=baseline)` 논리 record는 별도 `BaselineRegressionReceipt` 안에만 materialize한다. `ReleaseAssuranceRun`은 그 실행 payload가 아니라 locator/digest-only relationship을 소유한다. `RegressionExecutionEvidence(phase=final)`만 final run의 current execution evidence다.
- final `ReleaseAssuranceRun`은 구현과 test-after 변경이 끝나 final source revision을 고정한 뒤에만 시작한다. 그 뒤 source가 바뀌면 current run을 폐기하고 새 final revision으로 새 run을 만든다.
- `final.json`은 모든 evidence path/digest, terminal state, source revision, predecessor locator, bundle digest와 완료 UTC를 포함한다. 일부 파일만 존재하는 pending run은 승격 입력이 아니다.
- predecessor는 finalized bundle locator와 digest로만 참조한다. repair revision은 predecessor evidence를 읽어 defect lineage를 보여줄 수 있지만 current predicate 입력으로 복사할 수 없다.
- 기존 승격 경로는 final directory를 archive하고 archive digest + locator를 promotion receipt와 rollback metadata에 기록한다. rollback은 이 locator로 직전 정상 revision의 finalized bundle을 회수한다.
- 접근 경계는 owner-only workspace write, promotion/rollback read-only다. bundle에는 credential, ticket payload, canonical mutation bytes, raw output이 없으므로 별도 secret store가 아니다.
- finalized bundle은 최소 90일이며, 해당 revision이 배포·rollback 후보이거나 다른 bundle이 predecessor로 참조하는 동안은 90일을 넘어도 삭제하지 않는다. pending run은 7일 뒤 안전하게 정리할 수 있으나 finalized bundle과 predecessor chain은 건드리지 않는다.

| Record | Required infrastructure fields | Rejection condition |
|---|---|---|
| `BaselineRegressionReceipt` | baseline ID/source revision, environment fingerprint, normalized command text, command ID/SHA-256, Python/pytest version, start/end UTC, exit status, total/pass/fail/skip, sanitized output SHA-256, immutable receipt locator/digest | non-zero exit, fail/skip > 0, mutable/unverifiable receipt |
| `BaselineReceiptReference` | final assurance run ID/revision, check ID=`REL.01`, baseline locator/digest/revision, expected command/environment SHA-256, validation UTC, validation result | baseline 실행 payload 복제, locator/digest 불일치, mutable/unresolvable receipt, baseline 자체 실패·skip, command/environment incompatibility, stale final run identity |
| `RegressionExecutionEvidence` | phase=`final`, final source revision, baseline receipt locator/digest, environment fingerprint, normalized command text, command ID, command SHA-256, Python/pytest version, start/end UTC, exit status, total/pass/fail/skip, sanitized output SHA-256 | baseline receipt command·환경과 불일치, non-zero exit, fail/skip > 0, final source revision drift |
| `CoverageAssessment` | source revision, approved base revision, `coverage==7.17.0`, freeze/run/json/gate command ID·digest·exit status, 각 Unit의 manifest/approved-plan/attempt-baseline path·digest, sorted union source paths, union digest, executable/covered lines, percent, threshold | command 실패, frozen input 누락/변경, 승인 set과 claim 불일치, baseline 이후 승인 밖 변경, union source가 coverage JSON에 없음, percent < 80 |
| `VerificationEvidence` | assurance run ID, source revision, check ID(C03/C04/C05 또는 REL.02~REL.06), procedure key, result, safe counts, evidence digest, UTC time | 72개 current-final check의 중복·누락, stale revision, payload/secret field |
| `PerformanceTrial` | session ID, UTC observation time, source revision, deployment ID, anonymized role, method, scenario, trial 1~3, generated-data ref, browser/device/OS/network/cache fingerprints, monotonic start/end, duration, completion event, result, failure reason, screen transitions | trial 교체, fingerprint 불일치, 필수 field 누락, 실제 업무 data 또는 credential 포함 |

`blocked`와 `release_ready`는 한 source revision의 terminal state다. 수선은 predecessor를 가리키는 새 run과 새 evidence를 요구하며 이전 결과를 복사하지 않는다.

## Failure and Recovery Boundaries

| Failure | Infrastructure response |
|---|---|
| 예상 밖 DNS/TCP | 현재 test를 즉시 실패시키고 destination category/count만 기록한다. |
| secret canary match | boundary ID만 남기고 전체 release를 차단한다. canary 값·prefix·substring을 출력하지 않는다. |
| coverage source 누락 | `missing coverage source: <path>`로 gate를 실패시키고 denominator 축소를 금지한다. |
| baseline/final 비교 불가 | 회귀 evidence를 invalid 처리하고 같은 command/environment로 새 run을 수행한다. |
| documentation mismatch | automation evidence는 보존하지만 현재 run을 terminal `blocked`로 끝낸다. |
| NFR8 환경 불일치 | 측정 session을 `invalid`로 보존하고 정상 조건 실패인 `not_met`과 구분한다. |

## Assumptions & Open Questions

None.
