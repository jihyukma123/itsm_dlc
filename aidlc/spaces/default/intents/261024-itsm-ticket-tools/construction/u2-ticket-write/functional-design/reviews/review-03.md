## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T08:45:50Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/entities.md > `PendingCreateMutationV1`, `CanonicalRequestBytesV1`, and `TicketCreateAttemptV1` | 확인은 별도 HTTP turn에서 `pending_ref`만 받고 draft를 금지하지만, 확인 전 상태에는 `normalized_payload_hash`만 있고 ledger에 넣을 canonical request bytes는 어디에도 지속되지 않는다. 따라서 확인 시점에 원래 byte sequence를 복원할 권위 있는 원천이 없으며, 대화나 모델 입력에서 본문을 재구성하면 확인된 hash와 byte-identical 멱등 계약을 깨뜨린다. | 준비·수정 시 canonical bytes, serialization version, hash를 `mutation_id`에 결합해 보존하는 U2 소유의 권위 있는 pre-confirm 상태를 정의하거나 shared pending 계약을 명시적으로 확장하라. 확인 시 해당 상태를 읽고 hash를 재검증해 ledger로 넘기는 흐름, 취소·교체·만료 시 삭제 규칙, credential 비저장 규칙도 함께 명시하라. | Resolved (reviewer) |
| R-02 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/rules.md > BR3.5 and functional-spec.md > FD-U2-02 | 설계는 U1 소유 pending mutation 소비와 U2 소유 attempt 삽입을 한 SQLite transaction으로 단정하지만, 공유 계약은 U1의 독립 `consume_once` port만 제공하고 U2 ledger와 transaction을 조합할 port 또는 transaction owner를 제공하지 않는다. 현재 경계대로는 U1 구현을 우회하거나 수정하지 않고 이 원자성을 구현할 수 없고, crash/race 시 consumed-without-ledger 또는 ledger-without-consumption 상태가 가능하다. | U1/U2 경계를 가로지르는 composite confirmation-to-attempt operation의 소유자와 port를 정의하고, 한 transaction 안에서 binding 재검증·consume-once·attempt insert를 수행하는 성공/중복/crash/concurrency 의미를 계약에 추가하라. U1 migration을 수정하지 않는다는 경계는 유지하되 구현자가 공개 contract만으로 원자성을 달성할 수 있게 하라. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/entities.md > `SafeCreateResultV1` and functional-spec.md > FD-U2-03 | 설계는 `SafeCreateResultV1`을 tool 결과로 사용하지만 shared model-to-tool 계약은 `TicketMutationToolResultV1.data`에 `SafeMutationResultV1`을 요구한다. 새 타입은 이름뿐 아니라 `idempotent_replayed`를 required로 바꿔 V1 consumer schema와 직접 호환되지 않는다. | 공개 결과는 정확히 `SafeMutationResultV1`과 `TicketMutationToolResultV1`을 사용하도록 정렬하라. 내부 create projection이 필요하다면 내부 전용임을 표시하고 shared result로의 결정적 mapping을 명시하되 V1 필수/선택 필드를 변경하지 마라. | Resolved (reviewer) |
| R-04 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/traceability.json > `upstream_ids` and `coverage` | Traceability 검사는 shared story가 이 Unit에 배정되면 다른 Unit 소유 criterion도 선언하도록 요구하며, 현재 파일은 `AC4.1.1`, `AC5.1.1`, `AC5.1.3`, `AC5.1.5`, `AC5.1.6`을 누락해 5건 실패한다. | 누락된 shared-story criterion을 `upstream_ids`와 `coverage`에 추가하고, U2가 직접 설계하지 않는 항목은 owning Unit 또는 후속 단계가 명확한 `N/A`나 `Deferred`로 기록하라. | Resolved (reviewer) |
| R-05 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/entities.md > Logical Storage Boundary | 수정안은 `ticket_tools_create_v1`에 새 `prepared_create_payloads` table을 추가하지만, 승인된 Unit 경계는 U2가 이 namespace에 `ticket_create_attempts`만 추가한다고 명시하고 C-04 storage contract도 그 table만 선언한다. 필요한 pre-confirm 저장소가 설계상 타당하더라도 현재 shared boundary에는 없는 schema 확장이다. | `prepared_create_payloads`를 U2의 승인된 소유 schema로 추가하도록 Unit/C-04 storage contract를 정렬하고 migration·consumer contract test 범위를 갱신하거나, 기존 승인된 `ticket_create_attempts`만으로 같은 비권위 pre-confirm 수명을 표현하는 계약 호환 설계로 바꿔라. | Resolved (reviewer) |
| R-06 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/functional-spec.md > FD-U2-01 and U2 Create Attempt Lifecycle | 설계는 review 공개 전에 `TicketCreateAttemptV1`을 생성하지만, 승인된 `unit-of-work.md`의 U2 책임과 `components.md`의 `TicketOperations` behaviour는 confirmation이 끝난 직후 첫 HTTP 전에 durable ledger를 저장한다고 정의한다. 같은 entity의 생성 trigger가 상위 설계와 현재 상태 모델에서 서로 달라 구현자는 어느 lifecycle을 authoritative하게 따라야 하는지 결정할 수 없고, 미확인 payload·key의 보존 및 cleanup 의미도 상위 경계에 없다. | Ledger-first prepare가 의도된 새 계약이면 `unit-of-work.md`와 `components.md`의 `TicketCreateAttemptV1` 생성 trigger, pre-confirm 보존·종료·cleanup 의미를 같은 lifecycle로 정렬하라. 상위 계약을 유지해야 한다면 현재 Functional Design을 confirmation 이후 ledger 생성으로 되돌리고 crash-safe handoff를 공개 경계로 정의하라. | New |
| R-07 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/functional-spec.md > Gateway Outcome Decisions and U2 Create Attempt Lifecycle | 첫 counted POST의 typed 401은 token refresh 뒤 same-key 재호출이 가능하다고 하지만, state machine의 재호출 진입은 `ambiguous -> in_flight`뿐이고 repository `record_outcome`도 `ambiguous`, `completed`, `terminal_failure`만 반환한다. 확정적으로 거절된 401을 어느 durable state에 기록한 뒤 CAS 재claim하는지 없어 구현자는 이를 부정확하게 `ambiguous`로 분류하거나 재호출 불가능한 `terminal_failure`로 닫아야 한다. | Refresh 가능한 typed 401의 명시적 durable transition과 CAS expected state를 정의하고, refresh 성공·실패·crash·경쟁 caller 각각에서 attempt count, same-key/bytes 검증, 최종 state를 state model·repository operation·gateway table에 동일하게 반영하라. | New |
| R-08 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/functional-design/functional-spec.md > Crash and Concurrency Semantics | Crash 후 `in_flight`를 `ambiguous`로 취급한다고만 되어 있고 row에는 claim owner, lease, claim timestamp 또는 stale 판정 조건이 없으며 이를 원자적으로 전이시키는 repository operation도 없다. 재시작한 caller는 죽은 sender와 아직 실행 중인 concurrent sender를 구별할 수 없어 active POST 중 두 번째 claim을 열거나 row를 영구 `in_flight`에 둘 수 있다. | `in_flight` recovery의 durable arbitration을 정의하라. 최소한 claim identity와 stale 기준, 원자적 `in_flight -> ambiguous` recovery operation, active claimant와 restart가 경쟁할 때의 승자·패자 동작, attempt ceiling 보존을 entity·rule·workflow에 명시하라. | New |

> R-02 Reviewer note: U1 pending 소비와 U2 attempt 삽입을 하나의 transaction으로 묶는 주장이 제거됐다. 설계는 U2 row를 먼저 독립 commit하고 U1의 공개 `get`, `confirm`, `consume_once`만 사용하며, consumption evidence 이후 U2-owned CAS 승자만 전송하도록 정의한다.

> R-05 Reviewer note: 별도 `prepared_create_payloads` 확장이 제거됐고 U2 저장소는 승인된 `ticket_tools_create_v1.ticket_create_attempts`만 사용한다.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| required-sections | PASS: `entities.md` 6개, `rules.md` 5개, `functional-spec.md` 12개 H2; `traceability.json` 비-Markdown quiet-pass | 모든 선언 산출물이 stage의 문서 구조 floor를 충족한다. |
| upstream-coverage | PASS: `unit-of-work`, `requirements`, `components` 모두 stage deliverable union에서 참조됨 | 필수 상위 산출물 인용은 완전하지만, 인용된 lifecycle과 현재 설계의 의미 충돌은 Critical finding으로 남는다. |
| traceability | PASS: 18/18 rows, gaps 0, orphans 0, invalid targets 0; 14 OK and 4 Deferred | U2에 배정된 US2.1, US4.1, US5.1 acceptance criteria와 stable BR target의 기계적 추적성이 완전하다. |
| linter | NOT APPLICABLE: Functional Design은 TS/JS code output을 만들지 않음 | 이 stage 산출물에 linter match 대상이 없다. |
| type-check | NOT APPLICABLE: Functional Design은 TS/TSX code output을 만들지 않음 | 이 stage 산출물에 type-check match 대상이 없다. |

### Summary

기존 cross-owner transaction 및 무승인 table 확장 문제는 해결됐고 구조·추적성 검증도 통과했다. 그러나 ledger lifecycle이 승인된 상위 설계와 충돌하며 retry와 crash recovery의 durable 상태 전이가 닫혀 있지 않아 현재 문서만으로 안전하게 구현할 수 없다.
