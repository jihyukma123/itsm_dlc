# U4 Observability Design

## Sources

- `../nfr-requirements/observability-requirements.md`
- `../nfr-requirements/security-requirements.md`
- `../nfr-requirements/reliability-requirements.md`

## Evidence Architecture

U4는 새 production monitoring stack을 추가하지 않는다. 관찰 가능성은 deterministic test/release evidence로 구현하며 기존 SDK tracing 비활성을 보존한다.

| Record | Required fields | Forbidden fields |
|---|---|---|
| Verification evidence | run ID, source revision, check ID, result, procedure key, safe counts, digest, UTC time | ticket payload, canonical mutation bytes, credential, raw header/problem |
| Regression evidence | phase, command digest, environment fingerprint, total/pass/fail/skip, exit status, output digest | full captured output containing secrets |
| Coverage evidence | base/tested revision, manifest digests, sorted union path set, union digest, covered/executable lines, percent, threshold | source content, credential |
| Defect route | failed check ID, owning Unit, contract reference, severity, status, fresh evidence link | raw external error |
| Performance trial | method, scenario, trial 1~3, generated data ref, monotonic start/end, duration, success/failure, screen transitions | real ticket body, direct identifier in product code |

## Collection Flow

1. test fixture가 request, refresh, retry, sleep, publication, network와 canary boundary count를 수집한다.
2. 각 check는 pass/fail/not-run과 safe counters를 반환한다.
3. evidence writer는 schema allowlist와 secret scanner를 통과한 record만 저장한다.
4. completeness evaluator가 expected check-ID set과 actual evidence set의 차이를 계산한다.
5. release evaluator가 phase별 predicate를 계산하며 missing/stale evidence를 fail-closed 처리한다.

## Signals and Stop Rules

| Signal | Pass | Stop rule |
|---|---:|---|
| required automation check missing count | 0 | automation blocked |
| documentation check missing count | 0 before final predicate | final release blocked |
| unexpected network attempt count | 0 | test immediately fails |
| secret canary exposure count | 0 | test immediately fails without printing value |
| final suite failed count | 0 | owning Unit defect route |
| final suite skipped count | 0 | release blocked |
| changed-line coverage | >= 80% | release blocked below threshold |
| open blocking defects | 0 | final release blocked |

## Correlation and Privacy

- evidence는 source revision + assurance run ID + check ID로 상관한다.
- external request ID는 비밀이 아니고 검증된 경우에만 선택적으로 저장한다.
- user identity는 raw username 대신 test actor alias 또는 익명 role로 기록한다.
- canary failure는 boundary ID만 남기고 canary value를 assertion, traceback, stdout/stderr, runner report에 포함하지 않는다.

## NFR8 Outcome Model

- `met`: 사전 지정 세 trial 모두 성공, Assistant median 우세, 화면 전환 0회
- `not_met`: 정상 조건에서 trial 실패 또는 median/transition target 실패
- `not_measured`: 절차 미실행
- `invalid`: environment fingerprint 불일치 또는 필수 record 누락

## Assumptions & Open Questions

None.

