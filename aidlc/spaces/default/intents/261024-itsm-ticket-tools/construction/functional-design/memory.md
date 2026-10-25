<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations

- 2026-10-25T09:33:00Z — [unit u1-ticket-read-skeleton] 갱신된 C-01의 `confirm`과 `consume_once`를 하나의 실행 단계로 합치지 않고 별도 repository 전이로 반영했다. U1은 `mutation_id`와 `confirmed_at`만 담은 일회성 증거를 반환하고, U2의 durable ledger 결합·CAS claim은 별도 실행 권한 경계로 유지한다.
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-25T10:46:58Z — [unit u2-ticket-write] 갱신된 상위 설계의 ledger-first lifecycle을 권위 기준으로 반영했다. U2 create attempt는 U1 review 공개 전에 exact bytes와 key를 `prepared`로 저장하고, `consume_once`의 mutation ID·확인 시각을 별도로 결합한 뒤 claim identity·deadline을 가진 CAS 승자만 POST한다.

- 2026-10-25T12:20:52Z — [unit u3-ticket-update] 수정 성공을 PATCH 응답 자체가 아니라 실제 적용 변경과 증가한 version의 권위 있는 증거로 한정했다. 412·428뿐 아니라 전송 결과 불명확 상태도 자동 PATCH 재전송 없이 최신 상세 조회와 새 확인으로 수렴시킨다.

- 2026-10-25T12:25:37Z — [unit u3-ticket-update] confirm이 별도 HTTP 요청과 process restart를 건너도 실행 payload를 복원해야 하므로 U1 pending authority와 분리된 U3 `PendingUpdateExecution` durable record를 추가했다. canonical patch와 U1 검증 `IfMatchVersion`만 보존하고 U1 full binding·consume_once 없이는 실행 권한이 생기지 않게 했다.

- 2026-10-25T13:03:09Z — [unit u1-ticket-read-skeleton] 갱신된 C-01·C-02를 U1 provider 계약에 반영했다. U2의 durable refresh reservation은 U1 호출 전에 소비되어야 하고, U1은 token exchange 최대 1회와 기존 session credential의 원자적 commit만 소유한다. Update review 교체는 예상한 기존 mutation의 정확한 binding을 검증한 뒤 U1 namespace 안에서만 수행한다.

- 2026-10-25T13:11:02Z — [unit u1-ticket-read-skeleton] 수명주기 정리가 대화 이력을 건드리는 모든 경우에 Runner와 같은 conversation lock을 적용하고, lock 획득 뒤 사용자·세션·대화 binding을 재검증하도록 보강했다. Confirm과 consume 사이 crash로 남은 confirmed update는 정확한 소비·만료·수명주기 무효화 전까지 새 update 공개를 차단한다.

- 2026-10-25T17:40:00Z — [unit u4-release-assurance] C-03의 필수 계약 검사와 C-04·C-05 verification manifest를 유한한 `RequiredVerificationCase` catalog로 승격했다. 넓은 suite 이름만으로 release-ready를 판정하지 않고 각 stable check ID의 passed evidence가 정확히 하나씩 있어야 한다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs

- 2026-10-25T06:31:28Z — [unit u1-ticket-read-skeleton] 일반 상세 조회와 수정 전 조회를 별도 typed port로 분리했다; 일반 조회의 가용성을 유지하면서 U3에는 유효한 strong ETag가 없으면 실패하는 엄격한 계약을 제공한다. 세션 만료와 continuation reference 품질도 후속 Unit이 다시 공통 경계를 수정하지 않도록 U1 소유 계약으로 명시했다.
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-25T10:46:58Z — [unit u2-ticket-write] U1 공개 confirmation port와 U2 durable ledger를 cross-owner transaction으로 묶지 않았다. consume 뒤 evidence 결합 전 crash에는 같은 attempt·key·bytes로 새 확인을 요구하고, 401 미적용과 결과 불명확은 각각 `retryable_no_apply`와 `retryable_after_reconcile`로 분리해 안전성을 우선했다.

- 2026-10-25T12:20:52Z — [unit u3-ticket-update] revise에서 기존 유효한 review를 먼저 폐기하지 않고 새 patch 검증·최신 상세·실제 diff가 모두 준비된 뒤 교체한다. 잘못된 수정 입력이 이미 검증된 선택지를 파괴하지 않도록 사용성보다 안전한 교체 순서를 명시했다.

- 2026-10-25T12:25:37Z — [unit u3-ticket-update] U1 pending과 U3 execution을 cross-owner transaction으로 묶는 대신 U3 staged-first, U1 atomic same-operation replacement, U3 active 승격 순서를 선택했다. U1 put 전 실패는 이전 review를 보존하고 put 후 activation 전 crash는 두 durable row의 정확한 binding으로 복구한다.

- 2026-10-25T13:03:09Z — [unit u1-ticket-read-skeleton] refresh와 update publication 모두 cross-owner transaction으로 확장하지 않았다. Crash 뒤 두 번째 token exchange를 금지해 가용성보다 일회성 안전성을 우선하고, update는 U3 staged/active 수명주기와 U1 exact-old replacement를 분리해 각 namespace의 단일 소유권을 유지한다.

- 2026-10-25T13:11:02Z — [unit u1-ticket-read-skeleton] refresh reservation의 actor binding은 V1 필드를 늘리지 않고 서버 인증 opaque envelope로 검증하며, restart replay 차단은 U2 durable one-invocation claim이 담당하도록 했다. U1은 U2 저장소를 읽지 않고 envelope 검증과 단일 exchange·session commit만 담당한다.

- 2026-10-25T17:40:00Z — [unit u4-release-assurance] release evidence를 같은 run에서 revision별로 분기하는 대신 `blocked` run을 terminal로 두고 수선 revision마다 predecessor를 가리키는 새 run을 만든다. NFR8도 성공 trial을 추가 실행으로 대체하지 않고 사전 지정 1·2·3 중 하나라도 정상 조건에서 실패하면 해당 시나리오를 미충족으로 판정해 표본 선택 편향을 막는다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
