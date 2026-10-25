# U4 Reliability Design

## Sources

- `../nfr-requirements/reliability-requirements.md`
- `../nfr-requirements/performance-requirements.md`
- `../../functional-design/functional-spec.md`
- `inception/contract-design/contract-summary.md`

## Release Assurance Evaluator

`ReleaseAssuranceEvaluator`는 source revision에 고정된 evidence만 받아 fail-closed predicate를 계산한다.

### Phase A — Automated verification

- C03.01~C03.15
- C04.01~C04.25
- C05.01~C05.27
- REL.01 baseline suite
- REL.02 final suite
- REL.03 manifest-union coverage
- REL.04 network default-deny/bypass probe
- REL.05 all-secret-boundary canary scan
- REL.06 API/UI/history/model/accessibility regression

위 73개 check ID에 현재 run의 `passed` evidence가 정확히 하나씩 있고 final suite의 failed/skipped count가 0이며 coverage가 80% 이상일 때만 `automated_verified`가 된다.

### Phase B — Documentation verification

`REL.07`은 README 필수 주제와 실제 smoke 분리를 검증한 별도 evidence다. 이는 Phase A completeness에 넣지 않고 Workflow 5에서 생성한다.

### Phase C — Final predicate

`documentation_verified` 뒤에 다음을 다시 평가한다.

```text
automation evidence current
AND coverage passed
AND REL.07 passed
AND documentation result passed
AND open blocking defect count = 0
```

참이면 `release_ready`, 거짓이면 `blocked`다. 두 상태 모두 현재 revision run의 terminal state다. 수선된 revision은 predecessor run을 가리키는 새 run을 만들며 이전 evidence를 복사하지 않는다.

## Manifest-Union Coverage Gate

현재 `scripts/changed_line_coverage.py`의 current-unit-only denominator를 U4 gate에 그대로 사용하지 않는다. Code Generation에서 다음 design을 구현한다.

1. current U4 manifest와 모든 `--prior-source-manifest`의 claimed path를 정규화한다.
2. 각 manifest path가 workspace-relative application source이며 승인된 plan/source baseline과 일치하는지 검증한다.
3. 모든 manifest claim의 합집합과 approved base revision 사이의 changed executable line을 계산한다. prior claim을 denominator에서 제외하지 않는다.
4. 합집합의 application source path가 coverage JSON에 하나라도 없으면 `missing coverage source: <path>`로 실패한다.
5. denominator가 0이면 합집합에 실제 application change가 없음을 증명한 경우만 통과한다.
6. output에는 sorted path set, 각 manifest digest, union digest, covered/executable lines, percentage, threshold, base/tested revision을 남긴다.

기존 script를 확장하거나 U4 전용 wrapper를 두되, 두 경우 모두 `coverage==7.17.0` JSON을 입력으로 사용하고 기존 U1~U3 invocation의 의미를 깨지 않는다.

## Retry and Crash Recovery Patterns

| Concern | Pattern | Covers |
|---|---|---|
| Read transient failure | policy-owned one retry with fake-clock fixed delay | NFR7.1, NFR7.5 |
| Create ambiguity | ledger-first, claim deadline, reconcile-before-retry, global count | NFR3.1, NFR3.2, NFR3.5, NFR7.2, NFR7.6 |
| Update conflict/ambiguity | exact ETag, no blind replay, latest read and reconfirm | NFR3.3, NFR3.6, NFR7.3, NFR7.7 |
| Refresh crash | durable one-shot reservation and generation reconciliation | NFR3.7 |
| Lifecycle race | conversation lock, actor revalidation, terminal commit fence | NFR3.4, NFR3.8 |
| Rate limit | immediate safe response, no wait/retry | NFR7.4, NFR7.8 |

## Regression and Accessibility

- baseline/final suite evidence는 동일 command와 environment fingerprint를 사용한다.
- 기존 Agent/Runner/model/reasoning/tracing, chat API, history restore와 fallback을 snapshot/contract test로 고정한다.
- presentation kind별 visible text, keyboard flow, landmark/focus/live semantics와 restored-history no-announce를 검증한다.
- blocking failure는 owning Unit과 contract reference로 route하고 새 revision의 fresh evidence로만 `reverified` 처리한다.

## Backup and Recovery Boundary

새 backup, replication, failover infrastructure는 U4에서 만들지 않는다. 기존 SQLite 보존 정책을 바꾸지 않으며 production backup/restore 증거는 저장소 밖 기존 운영 경로의 책임이다. U4는 migration·schema fingerprint와 test-time restart/crash recovery를 검증한다.

## Assumptions & Open Questions

None.

