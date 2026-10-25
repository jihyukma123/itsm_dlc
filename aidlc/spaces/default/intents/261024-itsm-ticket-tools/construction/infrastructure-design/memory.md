<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations

- 2026-10-25T18:02:02Z — [unit u4-release-assurance] Coverage 완전성은 manifest 합집합만으로 성립하지 않는다. 각 Unit의 manifest를 승인된 Planned Source Set과 그 attempt의 source baseline에 결합하고 coverage 실행 전에 전체 binding·union digest를 고정해야 한다.

- 2026-10-25T18:02:02Z — [unit u4-release-assurance] 출시 evidence의 권위 매체를 `.release-assurance/runs/<source-revision>/<run-id>/` immutable bundle로 고정했다. terminal/dashboard는 projection이며 promotion·rollback은 archive locator/digest로 같은 finalized bundle을 회수한다.

- 2026-10-25T16:43:30Z — [unit u3-ticket-update] Data-at-rest 통제는 rollback 설명만으로 충족되지 않으며 runtime DB/parent ACL, disk protection, cleanup window와 backup encryption·access·retention을 수집·판정하는 별도 production release gate가 필요하다. POSIX `0600`/`0700` 또는 플랫폼 동등 owner-only ACL을 최소 조건으로 고정했다.

- 2026-10-25T16:38:31Z — [unit u3-ticket-update] 새 runtime infrastructure는 필요하지 않지만 U3의 migration ordering, durable publication, retry·refresh 상한과 release evidence를 기존 승격 경로에 매핑해야 하므로 Infrastructure Design을 실행한다. 이 library Unit은 `cicd-pipeline.md`와 `traceability.json`만 소유한다.
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-25T07:51:00Z — R-17은 runtime infrastructure 추가가 아니라 기존 promotion gate에 deterministic concurrency evidence를 추가하는 변경으로 해석했다. barrier event, direct row count, response/publication counter가 blocking evidence다.
- 2026-10-25T10:02:28Z — NFR3.2와 credential refresh 보강은 새 runtime resource가 아니라 기존 승격 경로의 blocking test contract로 반영했다. confirmation CAS, U2 ledger isolation, crash-before-bind, pre-call/401 shared refresh budget을 각각 관찰 가능한 counter와 snapshot으로 검증한다.
- 2026-10-25T10:08:50Z — brownfield의 기존 60초 token refresh margin과 server UTC clock을 pre-call usability predicate로 명시하고, gateway-only accessor의 preflight를 첫 public gateway call 내부이지만 첫 socket I/O 이전의 단계로 고정했다.
- 2026-10-25T11:18:48Z — [unit u2-ticket-write] 새 runtime infrastructure가 아니라 기존 승격 경로의 blocking evidence contract로 설계했다. Ledger-first ordering, send/recovery CAS, durable refresh reservation, 동일 key·bytes와 전체 POST 상한을 row snapshot·barrier·counter로 입증한다.
- 2026-10-25T14:49:15Z — [unit u2-ticket-write] 승인된 상위 설계에 없는 stable refresh-envelope key source를 기존 infrastructure로 추정하지 않았다. Exact C-01 provider signature와 key ownership·rotation 계약을 code generation, merge, promotion의 명시적 blocker로 승격했다.
- 2026-10-25T14:49:15Z — [unit u2-ticket-write] 현재 result lookup이 없는 reconciliation은 별도 recovery owner가 아니라 existing send claim으로 fence된 단일 no-I/O finalization CAS로 검증한다. Crash 전후 barrier는 durable `started` 상태가 0건임을 증명해야 한다.
- 2026-10-25T14:53:18Z — [unit u2-ticket-write] rollback 안전성은 prose 권고가 아니라 배포 전 blocking rehearsal로 고정했다. Migrated representative DB의 네 durable state, schema와 immutable row digest를 last-known-good artifact identity에 결합하고, receipt가 없거나 binding이 다르면 rollback 대신 ledger-preserving forward-fix만 허용한다.
- 2026-10-25T19:57:02Z — [unit u2-ticket-write] 최신 code-generation plan·source manifest와 구현된 `Settings`/reservation signer·verifier 경계를 근거로 source allowlist와 refresh key 계약을 실행 가능한 형태로 닫았다. Plan 표, manifest, Git diff의 exact set binding과 세 `TICKET_REFRESH_*` 설정이 승격 전 차단 증거다.
- 2026-10-25T20:07:21Z — [unit u3-ticket-update] U3 changed-line 판정은 clean committed checkout에서 실행하고 pre/post empty status와 unchanged tested `HEAD`를 증거로 남긴다. 실행 시점의 `main` merge-base가 아니라 fixed base commit, engine-captured source baseline digest, 승인 plan과 U3 source manifest에 결합하며 U1·U2·U4 claim을 다른 Unit 변경으로 분리하고 U3 executable denominator가 0이면 실패하도록 고정했다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs

- 2026-10-25T18:02:02Z — [unit u4-release-assurance] 새 CI provider나 evidence service 대신 workspace-local atomic bundle과 기존 build artifact 보존 계약을 선택했다. 공급자 독립성을 유지하는 대신 기존 승격 경로가 archive·retention interface를 제공해야 한다.

- 2026-10-25T16:43:30Z — [unit u3-ticket-update] 전체-source coverage와 changed-line coverage를 서로 다른 test run으로 만들지 않고 동일 `.venv` interpreter의 한 coverage JSON에서 함께 판정한다. 전체 80%는 조직 기본값의 추가 gate이며 changed-line 80%를 대체하지 않는다.

- 2026-10-25T16:38:31Z — [unit u3-ticket-update] 특정 CI provider나 새 cloud resource를 도입하지 않고 저장소 밖 승격 경로가 실행할 deterministic pytest·coverage·network-deny 계약으로 설계를 제한한다. 배포 자동화 가시성보다 기존 배포 경계 보존과 재현 가능한 차단 증거를 우선한다.
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-25T07:51:00Z — 새 CI workflow나 provider를 만들지 않고 저장소 밖 기존 승격 경로가 실행할 test contract만 강화했다. 공급자 자동화는 U1 범위 밖으로 유지한다.
- 2026-10-25T10:02:28Z — U2 ledger를 U1 cleanup의 zero-row 목표에서 제외하고 불변성 snapshot으로 검사한다. U1 revocable state 정리와 downstream durable attempt 보존을 동시에 만족시키기 위한 소유권 경계다.
- 2026-10-25T10:08:50Z — whole-application 80% threshold를 새로 만들지 않고 changed-source JSON을 U1의 유일한 coverage 판정으로 삼았다. network 차단은 특정 CI provider 방화벽 대신 pytest process의 DNS/TCP default-deny fixture와 deliberate bypass probe로 증명한다.
- 2026-10-25T11:18:48Z — [unit u2-ticket-write] Rollback은 application artifact만 되돌리고 additive U2 ledger schema와 retention 중인 row는 유지한다. Destructive down-migration보다 duplicate-create 방지 evidence 보존을 우선하며, 이전 release 호환성이 입증되지 않으면 기존 DB restore 또는 forward-fix를 사용한다.
- 2026-10-25T14:49:15Z — [unit u2-ticket-write] Key 계약이 정해질 때까지 임시 환경변수·process-local key·stub refresh로 진행하지 않고 refresh가 필요한 등록을 fail closed한다. 단기 구현 속도보다 restart 이후 actor authority의 검증 가능성을 우선한다.
- 2026-10-25T14:53:18Z — [unit u2-ticket-write] 별도 source manifest 계약을 추가하지 않고 승인된 Code Generation plan의 파일 목록과 merge-base Git diff를 source-integrity 기준으로 사용한다. 새 manifest의 생성·승인 lifecycle을 만드는 복잡성을 피했다.
- 2026-10-25T19:57:02Z — [unit u2-ticket-write] 이전에는 plan 파일 목록만으로 source integrity를 판정했지만, 현재 Code Generation이 이미 소유하는 `source-manifest.json`을 machine-readable projection으로 사용한다. 별도 lifecycle은 추가하지 않으면서 reviewer와 승격 경로가 같은 path 집합을 재현할 수 있게 한다.
- 2026-10-25T20:07:21Z — [unit u3-ticket-update] 새 artifact registry를 도입하지 않고 기존 packager와 artifact store에 provider-neutral identity contract를 요구했다. 운영 경로 선택은 보존하되 검증 뒤 한 번 봉인한 source commit·recipe·size·SHA-256을 staging, production과 rollback이 동일하게 사용해야 한다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-25T14:49:15Z — [unit u2-ticket-write] Contract Design 또는 기술 결정에서 stable key source의 실제 설정 이름, owner, signer/verifier interface, bounded verification lifetime과 `kid` rotation·폐기 규칙을 확정해야 한다.
