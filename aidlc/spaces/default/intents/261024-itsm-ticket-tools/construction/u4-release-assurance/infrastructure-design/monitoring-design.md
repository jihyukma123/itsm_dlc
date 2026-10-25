# U4 Monitoring Design

## Sources

- `../nfr-design/observability-design.md`
- `../nfr-design/reliability-design.md`
- `../nfr-design/security-design.md`
- `infrastructure-specification.md`

## Monitoring Boundary

U4는 새 production metrics/log/tracing stack을 만들지 않는다. 기존 SDK tracing 비활성을 보존하고, 승격 시점의 deterministic test/release evidence를 관찰 가능성 경계로 사용한다. production pager, dashboard 또는 log backend를 추측하지 않으며 기존 운영 경로가 있으면 이를 변경하지 않는다.

## Metrics & KPIs

| Metric | Source | Threshold | Why it matters |
|---|---|---:|---|
| final-revision automation evidence count | AssuranceCatalog와 current run evidence set | 72/72 passed | C03/C04/C05와 REL.02~REL.06이 모두 final source revision에 결합됐음을 보장한다. |
| REL.01 baseline reference count | BaselineReceiptReference validator | 1/1 passed | current run의 locator/digest-only reference가 별도 immutable baseline receipt를 검증하며 baseline 실행 payload를 복제하지 않았음을 보장한다. |
| composed automation catalog count | release evaluator | 73/73 passed | final 72개와 REL.01 reference 1개를 합성한 catalog completeness이며 서로 다른 revision evidence의 혼합을 금지한다. |
| documentation evidence count | DocumentationVerifier | REL.07 1/1 passed | README와 실제 smoke 분리가 최종 predicate에 포함됨을 보장한다. |
| final suite failed count | normalized pytest execution | 0 | 회귀가 있는 revision의 승격을 막는다. |
| final suite skipped count | normalized pytest execution | 0 | 필수 검사를 skip으로 숨기는 것을 막는다. |
| test command exit status | RegressionEvidenceCollector | 0 | count parsing과 별개로 실행 성공을 검증한다. |
| manifest-union changed-line coverage | CoverageGate | >= 80% | U1~U4가 주장한 application source 전체를 판정한다. |
| missing coverage source count | CoverageGate | 0 | coverage JSON에서 빠진 source를 denominator 밖으로 밀어내지 못하게 한다. |
| unexpected network attempt count | NetworkFence | 0 | 기본 자동화가 실제 외부 서비스를 호출하지 않음을 보장한다. |
| deliberate bypass blocked count | NetworkFence self-test | 1 | default-deny fixture가 실제로 동작함을 증명한다. |
| secret canary exposure count | SecretBoundaryProbe | 0 | model/tool/log/error/test failure surface의 비밀 노출을 차단한다. |
| open blocking defect count | DefectRouter | 0 | 알려진 결함이 남은 revision을 막는다. |
| tool-name cardinality | registry preflight | exact set of 3 | 최종 Agent surface가 계약과 일치함을 보장한다. |
| NFR8 valid trial count | PerformanceMeasurementRecorder | method 2 × scenario 3 × trial 3 = 18 | 교체 trial 없이 비교 가능한 사용자 성과 증거를 확보한다. |
| Assistant external screen transitions | PerformanceMeasurementRecorder | each Assistant trial = 0 | NFR8의 workflow 단축 조건을 판정한다. |

## Alerts

| Alert | Condition | Severity | Routes to |
|---|---|---|---|
| Release blocked — contract/security | required check missing/failed, unexpected network > 0, secret exposure > 0 | blocking | failed check의 owning Unit과 C-01~C-07 contract reference |
| Release blocked — regression | final exit != 0 또는 failed/skipped > 0 | blocking | U1/U2/U3/U4 중 test ownership으로 결정된 Unit |
| Release blocked — coverage | command 실패, source 누락 또는 coverage < 80% | blocking | U4 CoverageGate; source 결함은 owning Unit에도 route |
| Release blocked — documentation | REL.07 또는 DocumentationAssurance 실패 | blocking | U4 release assurance |
| Evidence invalid | revision, environment, command ID/digest 또는 required field 불일치 | blocking | U4 evidence collector |
| NFR8 not met | 정상 조건 실패, Assistant median 비우세 또는 화면 전환 > 0 | outcome | U4 performance measurement owner; automation pass는 변경하지 않음 |
| NFR8 invalid/not measured | fingerprint 불일치/필수 field 누락 또는 절차 미실행 | outcome | 측정 owner; 성공 claim 금지 |

이 설계에서 `blocking`은 외부 pager severity가 아니라 현재 revision의 승격 차단 의미다. 연락 채널과 당직 정책은 저장소에 근거가 없으므로 지정하지 않는다.

## SLIs / SLOs

| SLI | SLO target | Measurement window |
|---|---|---|
| Required automation completeness | final-revision 72/72 + current-run REL.01 reference 1/1 = catalog 73/73 | 한 final source revision의 한 assurance run과 locator/digest로 고정된 별도 baseline receipt |
| Full regression success | 100% passed, 0 failed, 0 skipped, exit 0 | baseline/final 각각 한 normalized command execution |
| Manifest-union changed-line coverage | >= 80% | final coverage execution 한 번 |
| Secret containment | 0 canary exposure across all declared surfaces | current assurance run 전체 |
| Network isolation | 0 unexpected attempts and bypass probe blocked | current assurance run 전체 |
| Documentation readiness | REL.07 and DocumentationAssurance passed | current source revision |
| NFR8 outcome | scenario별 세 valid trial 성공, Assistant median 우세, 전환 0 | 한 fixed-fingerprint measurement session |

## Logs & Tracing

| Surface | Collection | Correlation | Redaction/retention rule |
|---|---|---|---|
| baseline pytest result | normalized counts, exit status, sanitized output digest | baseline source revision + baseline ID + command ID | 별도 immutable baseline receipt에 atomic record로 저장하고 final run evidence로 복사하지 않는다. |
| REL.01 baseline reference | baseline locator/digest/revision, expected command/environment digest, validation result/time | final source revision + assurance run ID + check ID=`REL.01` | baseline count·output digest·실행 시각을 저장하지 않는 locator/digest-only record; 참조 receipt와 함께 보존 |
| final pytest result | normalized counts, exit status, sanitized output digest, baseline receipt locator/digest | final source revision + assurance run ID + command ID | final `.release-assurance` bundle에 atomic record로 저장하고 full raw output을 복제하지 않는다. |
| verification case | check ID, procedure key, result, safe numeric counters, digest | source revision + assurance run ID + check ID | ticket body, canonical mutation bytes, raw error/header 금지 |
| coverage | tool version, command IDs/digests/status, manifest digests, union paths/digest, counts | source revision + assurance run ID | source content과 credential 금지 |
| defect route | failed check, owner Unit, contract reference, severity, state, fresh evidence link | assurance run ID + defect ID | 원본 외부 오류 금지 |
| performance | fixed-fingerprint trial ledger | measurement session + method + scenario + trial | 익명화 role와 generated-data ref만 사용 |

distributed tracing은 추가하지 않는다. release evidence는 기존 runtime request trace가 아니라 검증 실행의 구조화 record다.

## Dashboard Specification

| Panel | Display | Pass interpretation |
|---|---|---|
| Assurance summary | finalized bundle locator/digest, run revision, predecessor, terminal state, evidence freshness | `release_ready` finalized bundle만 승격 가능 |
| Catalog completeness | final-revision expected/actual/missing/duplicate IDs와 REL.01 reference 상태를 분리 표시 | final 72/72 + REL.01 1/1 = 73/73, missing 0, duplicate 0 |
| Regression comparison | immutable baseline receipt locator/digest, REL.01 reference validation, final command digest, environment fingerprint, final counts/exit | baseline receipt 역참조 검증, command/environment 동일, final 100%; baseline payload가 final bundle에 복제되면 실패 |
| Coverage | manifest 목록·digest, union paths, covered/executable, percent | missing source 0, >= 80% |
| Security boundary | network attempts, bypass probe, canary boundary count | 0 / 1 / 0 |
| Defects | owner Unit, contract, state, fresh reverify link | open blocking 0 |
| Performance outcome | fingerprint validity와 scenario별 medians/transitions | 세 trial 모두 valid일 때만 `met` 가능 |

별도 dashboard service를 만들지 않는다. 기존 승격 경로가 `.release-assurance/runs/<source-revision>/<run-id>/final.json`과 그 immutable archive를 읽어 이 표를 표시한다. 터미널·build UI는 같은 bundle의 read-only projection이며 독립 evidence를 만들거나 부분 record를 조합하지 않는다.

## Evidence Retention and Retrieval

| Consumer | Retrieval rule | Retention rule |
|---|---|---|
| final assurance run | current-run REL.01 reference의 baseline locator/digest로 정확한 immutable receipt를 읽고 command/environment 및 receipt 성공 조건을 비교한다. baseline 실행 payload를 current run으로 복사하지 않는다. | 참조하는 final run과 그 promotion/rollback 후보가 보존되는 동안 reference와 receipt 모두 삭제 금지 |
| promotion | archive locator와 digest로 정확한 finalized bundle 전체를 읽고 `release_ready`와 source revision 일치를 재검증 | promotion receipt와 함께 locator/digest 보존 |
| rollback | 직전 정상 revision의 promotion receipt가 가리키는 finalized bundle을 읽는다 | 배포·rollback 후보인 동안 삭제 금지 |
| re-verification | 새 run은 predecessor locator를 lineage로만 읽고 current evidence는 새 bundle에 쓴다 | predecessor chain이 참조되는 동안 삭제 금지 |
| audit/debug | owner-only 또는 기존 build artifact read 권한으로 safe fields만 읽는다 | finalized 최소 90일; pending은 7일 후 정리 가능 |

## Assumptions & Open Questions

None.
