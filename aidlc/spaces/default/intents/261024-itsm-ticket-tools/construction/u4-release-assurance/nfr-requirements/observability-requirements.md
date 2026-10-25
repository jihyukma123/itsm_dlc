# U4 Observability Requirements

## Sources

- `inception/requirements-analysis/requirements.md`의 `NFR1`, `NFR5`, `NFR6`, `NFR8`
- `construction/u4-release-assurance/functional-design/entities.md`
- `inception/contract-design/contract-summary.md`

## Requirements

| ID | Requirement | Target | Record |
|---|---|---|---|
| NFR1.5 | 보증 log와 evidence에 credential 또는 raw provider detail을 남기지 않는다. | 비밀 canary 0건 | safe check ID, count, digest, request ID only |
| NFR1.6 | 예상하지 않은 network attempt를 관찰 가능하게 실패시킨다. | 허용 밖 attempt 0건; bypass probe 탐지율 100% | destination category와 차단 count, 비밀 없는 failure |
| NFR5.4 | baseline과 final 전체 suite를 같은 shape로 기록한다. | command, environment, total/pass/fail/skip, exit, digest 필드 완전성 100% | `RegressionExecutionEvidence` |
| NFR5.5 | 필수 verification catalog의 completeness를 계산할 수 있어야 한다. | C-03 15개, C-04 25개, C-05 27개, `REL.01`~`REL.06` automation check 각각 evidence 1개 | check-ID set difference 0 |
| NFR5.6 | 문서 evidence를 automation evidence와 별도 관찰한다. | `REL.07` exactly 1개, automation 전이 계산에서 제외, final predicate에는 포함 | documentation result와 smoke separation record |
| NFR6.4 | coverage 판정 입력과 결과를 재현 가능하게 기록한다. | manifest path set·digest, executable·covered lines, percentage, threshold 필드 완전성 100% | `CoverageAssessment` |
| NFR6.5 | 결함의 소유권과 재검증 상태를 추적한다. | 모든 blocking failure에 owning Unit·contract reference; repaired만으로 closure 0건 | `DefectRoute`와 fresh evidence link |
| NFR8.5 | 실제 환경 trial은 요구된 모든 측정 필드를 기록한다. | UTC 시각, revision, 환경, 익명 역할, method, scenario, trial, data ref, cache/network, monotonic start/end, duration, success/failure, transitions 필드 완전성 100% | `PerformanceTrial` |
| NFR8.6 | 성과 결과 상태를 구분한다. | `met`, `not_met`, `not_measured`, `invalid` 중 정확히 하나 | scenario outcome record |

## Logging and Metrics Boundary

- 새 production monitoring stack, dashboard, distributed tracing 또는 alerting system을 추가하지 않는다.
- 기존 SDK tracing 비활성 설정을 유지한다.
- U4가 만드는 것은 release evidence와 test-time counters이며 production request payload logging이 아니다.
- 업무 text, canonical request bytes, patch body, credential과 Authorization header는 evidence에 저장하지 않는다.

## Required Assurance Signals

| Signal | Pass condition | Alert/stop action |
|---|---|---|
| `required_check_missing_count` | 0 | release predicate를 `blocked`로 판정 |
| `unexpected_network_attempt_count` | 0 | test 즉시 실패 |
| `secret_canary_exposure_count` | 0 | test 즉시 실패, value는 출력하지 않음 |
| `full_suite_failed_count` | 0 | owning Unit defect route |
| `full_suite_skipped_count` | 0 | release block |
| `changed_line_coverage_percent` | >= 80 | 미달 시 release block |
| `open_blocking_defect_count` | 0 | release block |

## Assumptions & Open Questions

None.

