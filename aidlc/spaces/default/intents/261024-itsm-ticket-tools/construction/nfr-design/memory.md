<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-25T07:48:36Z — R-17은 단순한 SQLite retry 문제가 아니라 같은 conversation의 Runner/history/presentation과 session-expiry cleanup이 공유해야 하는 단일 동시성 경계 문제로 해석했다. pre/post-Runner persisted-expiry 검사를 publication fence로 설계했다.
- 2026-10-25T09:50:42Z — NFR3.2의 confirmation은 승인과 실행 권한 부여를 같은 연산으로 보지 않는다. U1은 분리된 confirm/consume_once CAS와 최소 일회성 evidence까지만 소유하고, 실제 mutation 권한은 U2·U3가 자체 state와 precondition에 결합한 뒤에만 성립한다.
- 2026-10-25T09:54:51Z — architecture review에서 lifecycle coordinator와 identity/Runner component 사이의 역참조가 one-way dependency 주장과 충돌함을 확인했다. 별도 conversation-serialization port와 opaque lock-held context로 acquisition ownership과 consumer proof를 분리했다.
- 2026-10-25T11:18:00Z — [unit u2-ticket-write] send outcome과 reconciliation outcome을 같은 claim predicate로 다루지 않고 `claim_kind`·state·claim ID 조합으로 분리했다. Send/recovery deadline은 각 HTTP timeout보다 1초 길게 계산해 active owner takeover를 막는다.
- 2026-10-25T11:24:00Z — [unit u2-ticket-write] U1의 기존 identity refresh 설계를 cross-Unit에서 추측해 호출하지 않도록 C-01 `CredentialRefreshPortV1`로 계약화했다. Durable U2 reservation evidence, provider 한번 호출, session credential 원자 commit, same-binding capability 반환을 명시했다.
- 2026-10-25T14:36:25Z — [unit u2-ticket-write] reconciliation ownership은 별도 recovery identity가 아니라 기존 send `claim_id`, expected state, 만료된 deadline, 기존 `last_outcome` phase의 단조 CAS로 한정했다. Transport와 reconciliation outcome 모두 같은 send claim을 기준으로 늦은 writer를 거부한다.
- 2026-10-25T14:43:14Z — [unit u2-ticket-write] 현재 계약에는 authoritative result lookup이 없으므로 reconciliation을 ownership 시작과 outcome write로 나누지 않고, 기존 send claim으로 fence된 하나의 no-I/O CAS가 lookup-unavailable와 retryable/terminal state를 함께 확정하도록 해 crash 후 `started` 고착을 제거했다.
- 2026-10-25T14:43:14Z — [unit u2-ticket-write] `refresh_reservation_id`는 기존 server-secret primitive가 인증하는 actor·attempt·generation·creator-boot envelope로 구체화했다. 같은 boot에서는 registry 상태와 무관하게 복구하지 않고, 다른 boot에서만 session generation을 비교해 second refresh 없이 결과를 복원한다.
- 2026-10-25T16:25:49Z — [unit u3-ticket-update] U3 실행 권한은 active execution row 하나로 표현하지 않고 exact U1 pending, current-turn confirmation, atomic consume evidence와의 교집합으로 설계했다. 응답 유실 locator도 동일 binding 재검증 뒤 같은 pending reference만 복구한다.
- 2026-10-25T16:33:08Z — [unit u3-ticket-update] Architecture review에서 C-02의 safe-401 allowance에 대응하는 U3 refresh port가 없음을 확인했다. U3 durable one-shot reservation과 U1 atomic session-credential commit port를 계약에 추가하고 generation 비교로 crash 뒤 second refresh를 금지했다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-25T07:48:36Z — 현재 단일-process 배포에서는 application per-conversation lock으로 직렬화한다. 다중 process 확장은 이번 Unit 범위에 넣지 않고 shared lock 또는 transaction 설계가 필요한 잔여 위험으로 유지한다.
- 2026-10-25T09:50:42Z — consume 후 downstream bind 전 crash에서는 evidence 재발급보다 재검토·재확인을 택한다. 사용자 단계가 하나 늘지만 U2의 동일 attempt/idempotency key/request bytes를 보존하고 unbound POST를 막아 중복 생성 위험을 줄인다.
- 2026-10-25T09:54:51Z — credential refresh는 identity boundary가 실행하되 정책 소유권은 TicketOperations에 남겼다. one-shot budget token과 remaining deadline을 narrow port로 전달해 dependency inversion을 추가하는 대신 gateway나 identity component의 독립 retry를 금지한다.
- 2026-10-25T11:18:00Z — [unit u2-ticket-write] refresh reservation을 호출 전 durable하게 소비하므로써 refresh 성공 전 crash에서 자동 재시도를 포기했다. 편의보다 refresh 최대 1회와 중복 POST 방지를 우선한다.
- 2026-10-25T14:36:25Z — [unit u2-ticket-write] 같은 process의 `reserved` observer는 조기 실패 write 없이 현재 state만 반환하고, generation 비교 복구는 실제 process restart에서만 허용했다. 자동 복구 가용성보다 live owner 비간섭과 refresh 최대 1회를 우선한다.
- 2026-10-25T14:43:14Z — [unit u2-ticket-write] process-local refresh owner task가 죽어도 같은 process에서는 예약을 회수하지 않는다. 실제 restart 전까지 해당 attempt의 자동 복구가 지연될 수 있지만 commit-to-registry race에서 live owner를 잘못 terminalize하는 것보다 안전성을 우선한다.
- 2026-10-25T16:25:49Z — [unit u3-ticket-update] U1·U3 cross-owner transaction 대신 staged-first, U1 exact-old transaction, U3 active CAS를 선택했다. Crash recovery가 복잡해지지만 namespace 단일 소유권과 이전 review 보존을 함께 유지하고, 다중-process 확장은 별도 arbitration 설계로 남겼다.
- 2026-10-25T16:33:08Z — [unit u3-ticket-update] U3 active locator의 단일성을 위해 old retire와 new promote를 같은 U3 transaction으로 묶고 actor-scope partial unique index를 선택했다. U1과의 cross-owner 원자성은 만들지 않되 crash recovery가 동일 transaction을 재실행하도록 했다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
