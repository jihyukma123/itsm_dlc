## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T06:12:16Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Critical | app/ticketing/repositories.py > PendingMutationRepository | U1이 소유해야 하는 `PendingMutationRepositoryV1`의 `confirm`과 `consume_once`가 구현되지 않았다. 현재 repository는 save, get, lifecycle invalidate만 제공하고 `CurrentTurnEvidenceV1`도 어떤 transition에 연결되지 않는다. 따라서 U2와 U3는 exact actor, operation, payload, target, version, expiry와 현재 turn 확인을 검증해 confirmed 상태로 만들거나 mutation 전에 원자적으로 한 번만 consume할 수 없다. 이는 downstream Unit이 U1 공통 migration 또는 repository를 다시 설계하게 만든다. | exact current-turn evidence와 모든 binding을 검사하는 `confirm`, confirmed row만 compare-and-set으로 `consumed`로 바꾸는 `consume_once`, expired·invalidated·reused·mismatched rejection을 U1 repository port에 구현하고 create/update variant contract test를 추가한다. | New |
| R-02 | Major | app/ticketing/capability.py and app/ticketing/gateway.py > TicketRequestCapability and ItsmGateway public methods | `TicketOperations._execute`가 `capability.delegated_token()`과 `refresh_once()`에서 raw token 문자열을 꺼낸 뒤 gateway에 전달한다. shared C-01은 credential value를 gateway만 접근하도록 하고 `ItsmGatewayV1` 입력도 capability로 고정하지만, 현재 정책 계층과 테스트 double이 token 값을 직접 소유·관찰한다. 비밀 격리 경계가 구현에서 한 계층 위로 확장됐다. | gateway 공개 메서드가 capability를 받고 gateway-only accessor를 통해 outbound 직전에 credential을 취득하도록 바꾼다. operation policy에는 token 값이 아니라 refresh outcome과 attempt state만 반환하고, policy·tool·model·repr에서 credential을 관찰할 수 없다는 contract test를 추가한다. | New |
| R-03 | Major | app/ticketing/operations.py > TicketOperations._execute and app/session.py > itsm_token_for | 전체 read deadline과 monotonic clock이 구현되지 않아 credential refresh를 포함한 `2 × ITSM_TIMEOUT_SECONDS + 0.25초` 상한을 강제하지 못한다. 또한 `itsm_token_for`의 pre-call refresh는 capability의 `_refresh_used`를 소비하지 않으므로, 만료 임박 token의 사전 갱신 뒤 401이 오면 `refresh_once`가 다시 실행되어 operation당 refresh 1회 계약도 깨진다. `tests/test_ticket_operations.py`에는 elapsed/deadline 또는 pre-call-refresh 조합 검사가 없는데 traceability는 NFR7.4를 `OK`로 표시한다. | 하나의 operation budget에 monotonic deadline, HTTP attempt 2회, refresh 1회를 함께 넣고 pre-call refresh도 같은 budget을 소비하게 한다. 각 attempt timeout을 남은 deadline으로 제한하고 first timeout, transient retry, pre-call refresh, 401 refresh, terminal second attempt 조합의 elapsed 경계를 fake clock으로 검증한다. | New |
| R-04 | Major | app/ticketing/repositories.py > CursorRepository.resolve_once | `DELETE ... RETURNING`으로 row를 먼저 소비한 뒤 actor/session/conversation/hash/expiry를 검사한다. 따라서 ref를 획득한 다른 actor의 binding mismatch가 정상 소유자의 아직 유효한 continuation까지 삭제한다. 테스트도 `test_cursor_binding_mismatch_fails_closed_and_consumes`에서 이 파괴적 동작을 성공 조건으로 고정하지만, functional contract는 binding 검증 후 원자적 once-only consume을 요구한다. | 한 transaction 안에서 row를 조회하고 exact binding, hash, expiry, canonical query validation을 먼저 통과한 경우에만 조건부 delete/consume한다. cross-actor, tamper와 expiry 실패가 저장 값을 노출하지 않으면서 유효 소유자의 row를 임의 소비하지 못함을 검증한다. | New |
| R-05 | Major | static/app.js > loadChatHistory, renderChatLog and appendMessage | restored history와 현재 응답을 모두 항상 `aria-live="polite"`인 같은 log에 append하며 history 복원 중 announcement를 끄는 경로가 없다. shared rendering contract의 `restored_history_announce: false`와 달리 페이지 시작 시 과거 메시지 전체가 다시 발표될 수 있고, 현재 static test는 live region 존재만 확인한다. | history DOM을 live region 밖에서 구성하거나 복원 중 `aria-live`를 비활성화한 뒤 현재 응답에만 기존 live semantics를 적용한다. 실제 DOM 또는 접근성 harness에서 restored rows announcement 0건과 current response announcement를 각각 검증한다. | New |
| R-06 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/code-generation/traceability.json > NFR1.1 and tests/test_ticket_gateway.py | NFR1.1을 `OK`로 매핑한 유일 target은 gateway safe-error serialization 검사다. 요구된 model input, tool result, API response, persistence row, application log와 의도적 실패의 stdout, stderr, traceback, assertion diff 전체에 대한 canary 검사가 없고, `rg` 확인에서도 failure-output capture가 존재하지 않았다. code summary의 비밀 0건 주장은 이 범위를 입증하지 못한다. | credential class별 canary를 모든 관찰 경계에 주입하고, 의도적으로 실패하는 격리 subprocess의 stdout, stderr, traceback, assertion diff를 수집해 0건을 판정한다. traceability target을 실제 종합 검증 test로 바꾸고 code summary에는 실행 결과만 기록한다. | New |
| R-07 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/code-generation/code-summary.md > 테스트와 품질 결과 and 계획 차이와 제한 | 필수 coverage 명령을 현재 환경에서 실행하면 `/Users/jihyukma/Documents/c/itsm_dlc/.venv/bin/python: No module named coverage`로 즉시 실패했다. summary는 임시 `PYTHONPATH`를 사용한 별도 실행으로 92% passed를 주장하지만 승인된 exact command와 pinned environment가 재현되지 않으며, dependency compile/install도 미완료라고 스스로 기록한다. | `coverage==7.17.0`이 lock/install 절차를 통해 `.venv`에 설치되도록 dependency 산출물을 재생성·동기화한 뒤 필수 coverage 명령을 그대로 실행한다. 실제 exit code와 report를 code summary에 기록하고 임시 import-path 결과를 완료 evidence로 사용하지 않는다. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| U1 scoped pytest | PASS: `71 passed in 0.44s` | 지정된 8개 U1 test file은 통과했지만 위 계약 누락을 검증하는 test가 없다. |
| Full pytest | PASS: `108 passed in 0.83s` | 전체 회귀 test는 현재 환경에서 통과했다. |
| Required coverage command | FAIL: `.venv/bin/python: No module named coverage` | code summary의 exact-environment coverage gate 통과 주장을 재현하지 못했다. |
| Source manifest and traceability structure | PASS: manifest 34개 path 모두 존재; traceability 73개 row, duplicate ID와 missing `OK` file target 0건 | 파일 존재와 JSON 구조는 유효하지만 일부 `OK` target의 의미적 증거가 부족하다. |

### Summary

기존 및 U1 pytest는 통과하지만 공통 confirmation repository의 핵심 transition이 없고, credential confinement·deadline/refresh budget·cursor atomicity·history accessibility 계약이 구현과 어긋난다. 비밀 경계와 coverage의 완료 주장도 필수 검증 명령으로 재현되지 않아 downstream Unit이 안전하게 확장할 수 있는 상태가 아니다.
