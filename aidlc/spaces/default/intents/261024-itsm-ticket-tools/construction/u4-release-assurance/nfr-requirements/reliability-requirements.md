# U4 Reliability Requirements

## Sources

- `inception/requirements-analysis/requirements.md`의 `NFR3`, `NFR5`, `NFR6`, `NFR7`
- `inception/contract-design/contract-summary.md`의 verification matrix
- `construction/u4-release-assurance/functional-design/functional-spec.md`

## Requirements

| ID | Requirement | Target | Evidence |
|---|---|---|---|
| NFR3.5 | create의 durable attempt state는 revocable lifecycle cleanup 뒤에도 중복 방지에 충분히 남는다. | 확인 시점부터 보존 최소 24시간 | lifecycle cleanup 뒤 ledger read와 retention boundary |
| NFR3.6 | update replacement와 실행 authority는 crash에도 정확히 한 winner만 남긴다. | active execution 최대 1개; rollback failure에서 old review 보존 100% | staged/active/retired, crash, concurrent confirm/revise tests |
| NFR3.7 | refresh reservation은 실행별 at-most-once다. | create/update 각각 port invocation·token exchange 최대 1회; crash 뒤 second refresh 0회 | durable reservation과 credential generation reconciliation |
| NFR3.8 | source revision이 바뀐 보증 evidence를 섞지 않는다. | run당 immutable revision 1개; 이전 evidence 재사용 0건 | predecessor-linked new run과 evidence revision assertion |
| NFR5.1 | 기존·신규 전체 regression은 모두 통과한다. | final full-suite failed 0, skipped 0, exit status 0 | test command, total/pass/fail/skip count, output digest |
| NFR5.2 | 기존 Agent/Runner/model/reasoning/tracing/API/history/UI를 보존한다. | 승인되지 않은 회귀 0건 | API schema, history restore, UI/accessibility, configuration assertions |
| NFR5.3 | 최종 조립은 정확히 세 tool만 공개한다. | exact set 100%, duplicate/unknown version fail-closed | registry contract tests |
| NFR6.1 | 변경 application source line coverage를 측정한다. | 80% 이상 | U1~U3 승인 manifest 합집합 + U4 application 변경 경로의 고정 manifest |
| NFR6.2 | coverage manifest는 판정 전에 고정하고 결과에 digest를 남긴다. | 사후 path 제외 0건 | ordered path set, digest, executable/covered line count |
| NFR6.3 | 결함 수선은 같은 실패 검사와 전체 판정을 새 revision에서 다시 실행한다. | blocking defect `reverified` 전 release 0건 | predecessor run, repaired/reverified link, fresh evidence |
| NFR7.5 | recoverable read만 정해진 한 번의 retry를 사용한다. | 전체 HTTP 시도 최대 2회 | request counter와 fake clock |
| NFR7.6 | create의 모든 복구 원인은 하나의 POST budget을 공유한다. | 전역 attempt count 최대 2 | proactive refresh, 401, ambiguous reconciliation 통합 test |
| NFR7.7 | update ambiguity와 conflict는 자동 overwrite 없이 최신 detail과 새 확인으로 수렴한다. | 허용 밖 PATCH replay 0회 | 412/428/response-loss tests |
| NFR7.8 | 429는 무대기·무재시도다. | sleep 0, retry 0 | fake clock과 request counter |
| NFR7.9 | release assurance 상태는 불완전 증거에서 fail-closed다. | 필수 automation evidence 누락, 문서 evidence 실패 또는 blocking defect 존재 시 `blocked` | 최종 predicate와 state transition test |
| NFR9.1 | 모든 ticket 상태와 다음 행동은 텍스트로 구분된다. | 색상·아이콘·위치에만 의존하는 상태 0건 | presentation kind별 visible text assertion |
| NFR9.2 | 기존 keyboard와 screen-reader 흐름을 보존한다. | 신규 keyboard trap 0건, 기존 landmark·focus·live semantics 회귀 0건 | browser DOM/accessibility regression |
| NFR9.3 | 복원된 history는 중복 announce하지 않고 새 상태만 적절한 live priority를 사용한다. | restored message announce 0건, unknown metadata는 text fallback 100% | restart history와 live-region test |

## Release Evidence Ordering

1. `automated_verified`는 C-03, C-04, C-05와 `REL.01`~`REL.06`의 모든 자동화 evidence가 통과할 때만 가능하다.
2. `REL.07`은 문서·실제 smoke 분리 evidence이며 automation 전이의 선행조건이 아니다. Workflow 5에서 별도 생성한다.
3. `documentation_verified` 뒤 최종 predicate는 자동화 evidence의 freshness, coverage, `REL.07`, documentation result와 blocking defect를 다시 검사한다.
4. 최종 predicate가 참이면 `release_ready`, 거짓이면 `blocked`다. 따라서 `documentation_verified → blocked` 전이가 반드시 존재한다.
5. `blocked`는 해당 revision run의 terminal 상태다. 수선은 predecessor를 가리키는 새 run에서 전체 evidence를 다시 생성한다.

## Failure Classification

- 테스트·계약·문서 실패: `blocked`
- 필수 검증 미실행: 통과가 아니며 `blocked`
- NFR8 정상 조건 trial 실패: 해당 성과 시나리오 `not_met`
- NFR8 미실행: `not_measured`
- NFR8 환경 조건 위반: measurement session `invalid`

## Assumptions & Open Questions

None.

