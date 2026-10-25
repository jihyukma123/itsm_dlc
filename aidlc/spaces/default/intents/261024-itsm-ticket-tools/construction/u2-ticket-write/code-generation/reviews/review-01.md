## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T11:59:08Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | app/ticketing/create_repository.py > `TicketCreateAttemptRepository.begin_reconciliation` | `status='ambiguous' OR claim_deadline_at <= now` 조건 때문에 첫 recovery owner가 설정된 뒤에도 상태가 `ambiguous`인 동안 현재 recovery claim ID를 관찰한 호출이 deadline 전에 새 recovery ID로 owner를 교체할 수 있다. 이는 active recovery owner를 탈취하지 않는다는 SEC-U2-07과 계획 Step 8을 직접 위반하며, 현재 테스트는 active send claim만 검사한다. | 최초 ambiguous 진입과 이미 active인 recovery claim을 구분해 active recovery는 deadline 전 교체할 수 없도록 CAS predicate를 수정하고, recovery ID를 알고 있는 두 번째 caller의 조기 takeover가 실패하며 stale recovery 결과가 0건 쓰이는 repository 동시성 테스트를 추가한다. | New |
| R-02 | Major | app/ticketing/create_operations.py > `prepare`, `revise`, `_publish_review` 호출 순서 | 새 draft의 schema 외 catalog·관계·시간 normalization이 유효한지 확인하기 전에 기존 `prepared` ledger를 `terminal_failure`로 만들고 pending review를 무효화한다. BR3.2는 새 **valid** review를 저장할 때만 기존 권한을 교체하도록 정했으므로, 사용자가 모호하거나 폐기된 catalog 값으로 revise를 시도하기만 해도 이전의 유효한 검토가 복구 불가능하게 사라진다. | 새 draft의 catalog resolution과 normalization을 부작용 없이 먼저 완료한 뒤 기존 row terminalization과 pending invalidation을 수행하도록 순서를 바꾸고, invalid revise/prepare가 기존 pending과 prepared row를 그대로 유지하며 POST 0회인 테스트를 추가한다. | New |
| R-03 | Major | app/ticketing/create_operations.py > `confirm` 및 `_republish_existing_review` | consume 후 bind 중 예외를 같은 process에서 잡은 경우에만 기존 attempt를 재게시한다. 실제 process가 `consume_once` commit 직후 종료되면 재시작 후 pending은 `consumed`여서 `_pending_matches`가 거부하고, 다음 prepare는 기존 row를 닫고 새 attempt/key를 만든다. 따라서 C-04의 “same attempt/key/bytes를 보존한 새 review와 새 explicit confirmation” crash 계약은 구현되지 않았고, 이름에 crash가 들어간 테스트도 repository method가 한 번 예외를 던지는 동일-process 모의일 뿐 process restart를 재현하지 않는다. | 재시작 후 `consumed` pending과 evidence 없는 기존 `prepared` attempt를 인식해 같은 attempt/key/bytes로 새 pending review를 게시하는 durable recovery 경로를 구현하고, 첫 process가 consume까지만 commit한 DB를 두 번째 repository/operations instance가 복구하는 테스트를 추가한다. | New |
| R-04 | Major | app/ticketing/create_operations.py > `_send`의 token-expired refresh branch | refresh reservation 사용과 session credential atomic commit 뒤 process가 success return 전에 종료되면 ledger는 `retryable_no_apply`, pending은 `consumed`로 남는다. 다음 요청은 이 attempt를 다시 진입할 경로가 없어 committed credential로 남은 budget의 send claim을 얻지 못하며, 새 prepare는 새 key와 새 attempt를 만든다. SEC-U2-10/C-01의 post-commit response-loss 복구와 “second refresh 0” 계약을 충족하지 않는다. 현재 테스트는 한 coroutine 안에서 refresh 성공 직후 재전송하는 경우만 검증한다. | `retryable_no_apply`와 durable reservation을 재시작 후 복원하고, session store에 이미 commit된 same-binding credential로 refresh 재호출 없이 기존 attempt의 새 send claim을 얻는 경로를 구현한다. credential commit 직후 response loss를 만든 뒤 새 service instance에서 같은 key/bytes·global count로 재개되고 refresh invocation이 총 1회인 통합 테스트를 추가한다. | New |
| R-05 | Minor | tests/test_ticket_create_security.py > `SECRET_CANARIES` 및 safe-output 테스트 | U2 전용 idempotency key와 canonical bytes canary는 dataclass `repr` 및 정상 safe result/presentation에서만 검사된다. 계획 Step 11과 SEC-U2-12가 요구한 application log, API response, stdout/stderr, traceback·assertion diff의 의도적 실패 경계에는 이 두 U2 전용 secret-like 값이 주입되지 않아 `code-summary.md`의 전 경계 노출 0건 주장이 현재 증거보다 넓다. | idempotency key와 canonical bytes를 포함하는 의도적 실패 subprocess 및 API/log capture를 추가하고, stdout·stderr·traceback·assertion diff·HTTP body·log에서 두 canary가 0건인지 검증하거나 summary의 주장을 실제 검증 범위로 제한한다. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| Exact U2 verification command | PASS: 193 passed in 3.26s | 선언된 U2 파일 집합은 모두 통과했지만 위 crash/recovery 및 invalid-revise 경계가 suite에 없다. |
| Construction Verification Command | PASS: 246 passed in 4.38s; 2412 statements 중 228 miss, total 91% | 전체 회귀와 80% statement coverage floor는 통과했다. |
| Manifest/traceability integrity probe | PASS: writes 27, missing path 0, upstream 94, coverage 94, uncovered/extra/missing OK target 0 | 선언된 path와 ID 연결은 구조적으로 완전하다. |

### Summary

기본 흐름과 전체 회귀는 안정적으로 통과했지만, 승인된 설계의 핵심인 active recovery fencing과 두 crash-recovery 계약이 실제 재시작에서 성립하지 않는다. invalid revise가 기존 유효한 review를 먼저 파괴하는 순서 문제까지 있어 이 상태로는 durable create orchestration을 완료했다고 보기 어렵다.
