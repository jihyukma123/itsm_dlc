<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations

- 2026-10-25T09:43:13Z [unit u1-ticket-read-skeleton] — confirmation을 실행 권한과 동일시하지 않고 `confirm`과 `consume_once`를 분리했다. U1은 정확히 한 번의 최소 증거만 제공하며 U2/U3가 각자의 실행 전제를 별도로 만족해야 한다.

- 2026-10-25T08:35:17Z [unit u2-ticket-write] — ledger-first는 NFR 문서가 기존 Functional Design을 덮어쓰는 결정이 아니라 그 단계를 다시 열어 정렬해야 하는 선호 remediation으로 제한했다; 서로 배타적인 두 흐름을 NFR Design이나 Code Generation이 임의 선택하지 못하도록 revision·review receipt를 구현 차단 조건으로 두었다.

- 2026-10-25T08:30:58Z [unit u2-ticket-write] — 계약 검토에서 남은 저장·원자성 우려를 비기능 차단 조건으로 해석했다; 새 cross-owner API를 추측하지 않고 C-01/C-04 공개 계약 안에서 ledger-first 실행 권한을 증명하도록 후속 NFR Design에 맡겼다.
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-25T10:55:34Z — [unit u2-ticket-write] 기능 설계가 ledger-first/public-port-only로 재검토됐으므로 이전의 "Functional Design 재개 전 차단" 조건을 제거하고, evidence binding·review replacement·claim deadline·retry state·claim-ID outcome fencing을 측정 가능한 NFR3.1~NFR3.8로 확정했다.

- 2026-10-25T11:06:00Z — [unit u2-ticket-write] transport 결과와 reconciliation 결과의 expected state·claim ID를 분리했고, credential refresh는 호출 전 durable one-shot reservation을 소비하도록 규정해 crash·동시성 상황에서도 attempt당 1회 상한을 검증 가능하게 했다.

- 2026-10-25T13:16:48Z — [unit u1-ticket-read-skeleton] 최신 기능 계약의 보안 경계를 NFR gate에 반영했다. History를 바꾸는 네 lifecycle event 모두 Runner lock·actor 재검증·terminal commit을 공유하고, confirmed update crash recovery와 authenticated refresh reservation을 별도 정량 기준으로 추가했다.

- 2026-10-25T16:19:26Z — [unit u3-ticket-update] 최신 C-02/C-05가 U1 exact-old replacement와 U3 execution store의 소유권·migration·cleanup을 확정했으므로 이전의 구현 차단 조건을 제거했다. Exact active execution, U1 pending, current-turn 확인과 원자적 consume evidence를 함께 요구하는 정량 경계로 대체했다.

- 2026-10-25T17:49:00Z — [unit u4-release-assurance] 상세 NFR ID는 문서별 numbering이 아니라 U4 전체에서 family별 전역 유일 번호로 재배정했다. Automation evidence는 C-03/C-04/C-05와 REL.01~REL.06, 문서 evidence는 REL.07로 분리하고 최종 predicate에서 다시 결합한다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs

- 2026-10-25T09:43:13Z [unit u1-ticket-read-skeleton] — lifecycle cleanup은 U1 revocable state만 제거하고 U2 durable ledger를 보존한다. consume 뒤 binding 전 crash에서는 자동 실행 대신 같은 attempt의 새 확인을 요구해 편의보다 중복 mutation 방지를 우선했다.

- 2026-10-25T08:35:17Z [unit u2-ticket-write] — 전체 파일 coverage 대신 `coverage==7.17.0` JSON과 git diff line 교집합으로 changed-code 80%를 계산한다; 기존 코드의 낮은 coverage가 신규 변경의 판정을 왜곡하지 않으면서 base commit·파일·분자·분모를 재현 가능하게 남긴다.

- 2026-10-25T08:30:58Z [unit u2-ticket-write] — 별도 pre-confirm table보다 승인된 `ticket_create_attempts`의 사전 `prepared` row를 선택했다; ledger-only 고아는 비권위 상태로 안전하게 남길 수 있고, U1 consume evidence와 CAS를 함께 요구하면 새 schema나 분산 조정 없이 crash·동시 confirm의 중복 POST를 차단할 수 있다.
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-25T10:55:34Z — [unit u2-ticket-write] 단일-process 범위에서는 per-conversation lock과 SQLite CAS를 함께 사용한다. 다중 process coordinator는 추가하지 않고, 배포 모델이 바뀔 때 shared lock 또는 transaction arbitration을 재설계할 잔여 위험으로 남겼다.

- 2026-10-25T11:06:00Z — [unit u2-ticket-write] refresh reservation 이후 crash는 자동 재갱신보다 fail-closed를 선택했다. 재시도 편의보다 중복 refresh·POST를 방지하는 안전 상한을 우선한다.

- 2026-10-25T13:16:48Z — [unit u1-ticket-read-skeleton] 사용자가 기존 산출물 유지를 선택했지만 현재 기능 계약과 충돌하는 항목은 검토 수선 범위에서만 보완했다. 기존 ServerSession credential field는 유일한 허용 persistence 경계로 유지하고, U1이 U2 storage를 읽는 대신 인증된 opaque reservation과 U2 durable replay gate를 사용한다.

- 2026-10-25T16:19:26Z — [unit u3-ticket-update] U1과 U3 저장소를 cross-owner transaction으로 묶지 않고 staged-first, U1 exact-old transaction, U3 active CAS를 유지했다. 단일-process SQLite 경계 안에서 이전 review 보존과 crash recovery를 얻는 대신, 향후 다중-process 배포에는 shared lock 또는 동등한 transaction 설계가 필요하다.

- 2026-10-25T17:49:00Z — [unit u4-release-assurance] 새 품질 stack이나 CI를 추가하지 않고 현재 requirements에 고정된 `coverage==7.17.0`과 `scripts/changed_line_coverage.py`를 사용한다. 테스트 실패 surface까지 secret canary 경계에 포함하고, NFR8은 정상 조건 실패·미실행·환경 invalid를 서로 다른 결과로 보존한다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
## U3 Ticket Update observations

- 상위 NFR1~NFR9는 U3에 필요한 보안·무결성·복구·회귀·테스트·성과·접근성 기준을 이미 정량화했으며 새 처리량·가용성 목표는 필요하지 않았다.
- Functional Design review에서 남은 C-02 atomic replacement 부재와 C-05 storage ownership 부재를 새 기술 선택으로 덮지 않고 Code Generation 전 차단 조건으로 보존했다.
- U3의 핵심 검증 경계는 exact ETag/version, full confirmation binding, PATCH 자동 재시도 0회, authoritative reconciliation, 비밀·외부 텍스트 canary와 deterministic crash/concurrency injection이다.
