## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T17:17:45Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | app/ticketing/update_operations.py > `_publish` and `_prepare_or_revise`; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/code-generation/code-generation-plan.md > Step 7 and Step 9 | U1 replacement가 commit된 뒤 U3 `activate_replacement`가 실패하면 `_publish`는 `ticket_update_activation_pending`만 반환한다. 다음 `prepare`의 접근 복구는 `find_active_for_actor_ticket`만 조회하므로 그 `staged` execution과 유효한 U1 pending을 승격하지 못하고, 사용자는 공개되지 않은 `pending_ref`를 알 수 없어 confirm/revise/cancel도 할 수 없다. 현재 복구는 process startup 또는 이미 mutation ID를 아는 confirm에만 존재해, 계획이 완료로 표시한 “다음 접근 또는 startup recovery” 중 접근 경로가 구현되지 않았다. | prepare/revise 접근 시작 시 현재 actor/ticket 범위의 staged 후보를 U1 pending과 exact binding으로 조정하고, 일치하는 row만 expected-state CAS로 승격한 뒤 같은 review를 재구성하라. U1 commit 직후 activation 실패를 주입하고 process restart 없이 다음 접근이 같은 pending을 복구하는 통합 테스트를 추가하라. | New |
| R-02 | Major | app/ticketing/update_migration.py > `verify_ticket_update_schema`; tests/test_ticket_update_migration.py > fingerprint 검증 | 저장된 marker hash는 상수와 비교하지만 실제 SQLite table/index 정의의 hash를 다시 계산하지 않는다. 검증은 column 이름 tuple과 index 이름 존재만 보므로, 같은 이름의 non-unique/non-partial active index나 변경된 column type·constraint도 정상으로 통과할 수 있다. 이는 단일 active execution과 migration fail-closed를 물리적으로 보장한다는 계획·요약의 주장보다 약하다. | `sqlite_master.sql`, `PRAGMA table_info`, `PRAGMA index_list/index_xinfo`에서 실제 table·locator·unique partial-index 정의를 canonicalize해 기대 fingerprint 및 uniqueness/predicate/column 계약과 대조하라. 같은 이름을 유지한 채 unique/partial predicate 또는 column constraint를 변조한 DB가 repository/plugin 활성화 전에 거부되는 테스트를 추가하라. | New |
| R-03 | Major | app/ticketing/capability.py > `UpdateCredentialRefreshPortV1.refresh_update_capability_once`; tests/test_ticket_update_operations.py > update refresh tests | U1 refresh port는 reservation ID가 `update.`로 시작하고 credential generation이 같은지만 검사한다. `UpdateCredentialRefreshReservationV1`에는 actor/session/conversation binding이나 인증 envelope가 없고, port는 active U3 execution, durable reservation, consumed U1 evidence와 mutation binding을 검증하지 않는다. 따라서 C-02와 계획 Step 6의 “durable reservation + operation-domain-separated actor binding”은 현재 호출 순서에 의존할 뿐 port 경계에서 강제되지 않으며, 테스트도 정상 흐름과 호출 횟수만 검증한다. | U1 port에 durable reservation을 인증·조회하는 좁은 verifier를 주입해 mutation과 current capability의 user/session/conversation, active execution, consumed binding, base generation을 한 번에 검증한 뒤에만 exchange를 허용하라. 조작된 prefix, 다른 actor/session/conversation, 미예약·retired execution, 미소비 U1 pending에서 refresh/exchange가 0회인 provider contract 테스트를 추가하라. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| Exact U3 pytest command | PASS: 219 passed in 2.97s | 기록된 Unit 테스트 수와 통과 주장을 재현했다. 위 세 경계의 누락 시나리오는 현재 수집된 테스트가 행사하지 않는다. |
| Manifest-bound changed-line coverage helper | PASS: 1937/2227 = 86.98%, floor 80% | source manifest, U1/U2 prior manifests, approved plan, source baseline binding과 coverage floor를 재현했다. |
| Repository-wide pytest | PASS: 513 passed in 6.69s | 기존 회귀 전체가 통과했지만 접근 중 staged recovery, 실제 schema-definition drift, 위조 refresh reservation의 부정 경로는 검증되지 않는다. |
| `git diff --check` | PASS | whitespace 오류는 발견되지 않았다. |

### Summary

핵심 update 흐름과 수치화된 테스트·coverage는 재현됐지만, crash 접근 복구, 물리 schema 검증, credential refresh 신뢰 경계가 승인된 C-02/C-05 안전 계약을 완전히 강제하지 않는다. 세 항목을 수선하고 부정 경로 테스트를 추가한 뒤 재검토가 필요하다.
