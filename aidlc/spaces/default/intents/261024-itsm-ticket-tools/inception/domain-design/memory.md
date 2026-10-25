<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-25T03:59:47Z — 새 서비스 금지는 내부 논리 컴포넌트까지 금지하는 뜻이 아니다. 기존 단일 FastAPI 배포 안에 `TicketOperations` 경계를 두어 확인·멱등성·충돌·오류 복구의 소유권을 분명히 했다.
- 2026-10-25T03:59:47Z — 티켓과 카탈로그는 ITSM 소유 외부 데이터로 유지하고, Assistant는 서버 세션·대화·보류 변경·등록 시도만 소유한다.
- 2026-10-25T08:54:35Z — 등록 원장을 ledger-first로 확정했다. `TicketCreateAttempt`는 prepare·revise에서 `prepared`로 durable 저장된 뒤 U1 공개 pending review가 게시되며, U1 소비 증거와 U2 CAS claim이 함께 있어야 POST할 수 있다.
- 2026-10-25T09:01:27Z — 일반 불명확 결과는 결과 확인 뒤 티켓이 없고 시도 횟수가 2회 미만일 때만 동일 key·bytes 재시도를 허용한다. U1 소비 증거 결합 전 crash는 기존 attempt를 보존하되 새 review와 재확인을 요구한다.
- 2026-10-25T09:04:19Z — 불명확 결과 복구와 token-expired 401 복구는 하나의 전역 `attempt_count` 예산을 공유한다. 모든 POST CAS claim을 count < 2로 제한해 복구 원인의 조합과 무관하게 실제 POST가 최대 2회를 넘지 않도록 했다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-25T03:59:47Z — `ItsmGateway`를 하나의 논리 경계로 유지하면서 인증·카탈로그·티켓을 내부 어댑터로 분리했다. 컴포넌트 수를 억제하는 대신 내부 공개 API 규율이 필요하다.
- 2026-10-25T03:59:47Z — 확인·멱등 상태를 프로세스 메모리가 아닌 SQLite에 보존해 schema·정리 로직 비용을 감수하고 재시작·불명확 결과 복구의 결정성을 확보했다.
- 2026-10-25T03:59:47Z — `TicketPresentationV1` 의미를 서버가 소유해 서버·브라우저 계약 동기화 비용을 감수하고 모델·외부 텍스트의 UI 의미 조작을 차단했다.
- 2026-10-25T08:54:35Z — 별도 확인 전 테이블이나 cross-owner transaction port를 만들지 않는 대신 기존 create ledger에 고아 `prepared` 정리, claim identity·deadline, `retryable_no_apply` 상태를 추가해 exact bytes와 실행 중복 방지를 한 소유 경계에 모았다.
- 2026-10-25T09:01:27Z — cross-owner transaction 없이 consume evidence를 U2 원장에 idempotent하게 결합한다. 결합 전 crash에서 자동 재개 편의를 포기하고 재확인으로 fail closed하며, originating actor IDs는 live foreign reference가 아닌 역사적 binding으로 보존한다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
