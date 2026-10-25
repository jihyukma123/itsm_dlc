## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T16:13:01Z
**Iteration:** 2
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/entities.md > Source of Truth > PendingUpdateMutation relationships | 확인 요청에서 실행할 실제 patch와 검증된 `IfMatchVersion`을 복원할 권위 있는 저장 경로가 없다. durable `PendingUpdateMutation`에는 patch의 hash와 `base_version`만 있고 관계도도 `TicketPatch` digest만 참조한다. 반면 C-03A의 `ticket_update confirm` 입력은 patch를 금지하고, C-02는 `IfMatchVersion`을 U1 adapter가 만든 값으로 제한하며 U3의 재구성을 금지한다. 따라서 prepare와 별도 HTTP 요청인 confirm 사이에서 어떤 PATCH body와 `If-Match`를 보내야 하는지 구현할 수 없고, 재시작 후 확인은 특히 실행 불가능하다. | canonical normalized patch와 U1이 검증한 `IfMatchVersion`을 confirm 시 권위 있게 조회할 수 있는 durable 계약을 정의한다. U1 pending variant를 확장할지 U3 소유 저장소를 둘지 소유권과 migration을 명시하고, 저장·조회·binding 검증·재시작 round-trip을 entities, workflow, 상위 계약과 테스트에 일관되게 반영한다. | Resolved (reviewer) |
| R-02 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/functional-spec.md > UC-U3-01 Prepare or Revise Update > Ordered Flow step 8 | revise가 이전 pending을 먼저 `invalidated`로 만든 뒤 새 pending을 저장한다. C-02의 repository 계약에는 원자적 replace가 없으므로 두 호출 사이의 저장 실패나 프로세스 중단은 유효했던 review를 파괴하고 새 review도 남기지 않는다. 이는 질문 요약의 “잘못된 수정 요청은 기존 review를 파괴하지 않는다”보다 넓은 실패 경로를 다루지 못한다. | 새 pending 저장과 이전 pending 무효화를 하나의 원자적 repository operation으로 정의하거나, 새 pending을 먼저 durable하게 저장한 뒤 실패 시 기존 pending이 계속 유효하도록 명시적인 전이·보상·동시성 규칙을 설계한다. 해당 crash-window 계약 테스트를 추가한다. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/functional-spec.md > UC-U3-01 Prepare or Revise Update > Outcomes; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/rules.md > BR3.1 and BR3.2 | 설계는 validation 실패에 `invalid_input`을 반환한다고 규정하지만, 상위 `TicketMutationToolResultV1.state` enum에는 `invalid_input`이 없고 `failed`만 있다. 같은 functional spec의 edge-case matrix는 동일 조건을 `failed`로 표기해 단일 산출물 내부에서도 결과 상태가 충돌한다. 구현자와 mapper가 서로 다른 wire state를 선택할 수 있다. | validation/no-op의 공개 state와 `SafeErrorV1` code 조합을 상위 result 계약에 맞춰 하나로 확정하고, UC outcomes, BR3.1~BR3.3, edge-case matrix, presentation mapping과 테스트 기대값을 동일하게 수정한다. 새 state가 필요하면 먼저 versioned 상위 계약을 변경한다. | Resolved (reviewer) |
| R-04 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/traceability.json > upstream_ids and coverage | traceability 검증이 U3에 매핑된 공유 story의 `AC4.1.1`, `AC5.1.1`, `AC5.1.3`, `AC5.1.5`, `AC5.1.6`이 `upstream_ids`와 `coverage`에 없다고 실패했다. 이 기준들이 다른 Unit 소유이더라도 현재 표에는 그 사실을 나타내는 `N/A` row가 없어 공유 story 전체의 배분을 기계적으로 증명할 수 없다. | 누락된 다섯 AC를 `upstream_ids`와 `coverage`에 추가하고, 각 row를 소유 Unit과 범위를 명시한 `N/A` target으로 기록한 뒤 traceability 검증을 다시 실행한다. | Resolved (reviewer) |
| R-05 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/entities.md > Source of Truth > PendingUpdateExecution; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/functional-spec.md > Scope | 새 `ticket_tools_update_v1.pending_update_executions` migration과 durable entity가 상위 저장·소유권 계약에 없다. `components.md`의 TicketOperations 저장 범위와 외부 의존성은 U1 `ticket_tools_state_v1`과 U2 `ticket_tools_create_v1`만 열거하고, `unit-of-work.md`와 C-02/C-05도 U3-owned persistence, migration 적용 순서, U4 assembly·verification 책임을 정의하지 않는다. 이 상태에서는 기능 설계가 승인된 Unit 경계를 조용히 넓히며, 배포가 migration을 적용하고 lifecycle cleanup과 최종 검증이 이 record를 포함한다는 보장이 없다. | U3 durable execution store를 유지하려면 shared component/entity ownership, Unit deliverables, C-02/C-05 계약, migration 적용·rollback 책임, lifecycle cleanup과 U4 verification manifest에 `ticket_tools_update_v1`을 명시한다. 그렇지 않으면 승인된 U1 pending contract 안에서 실행 자료를 보존하도록 shared contract를 versioned하게 확장한다. | Resolved (reviewer) |
| R-06 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/functional-spec.md > UC-U3-02 Confirm and Execute Update, Ordered Flow step 6 and State Machine | 확인 상태 전이와 `consume_once`가 순차적인 두 단계로 기술되고 `Pending → Confirmed → Consumed`로 모델링되어 있다. 확인 저장 뒤 소비 전에 중단되면 실행 증거 없이 `confirmed` 상태가 남으며, 이 상태는 exact-old replacement가 요구하는 `pending` 상태에도 맞지 않는다. 명세에는 이 crash point의 복구 또는 폐기 경로도 없다. | U1 repository가 확인 표시와 일회 소비를 한 원자적 연산으로 수행해 `ConsumedMutationEvidenceV1`을 반환하도록 흐름·sequence·상태 전이를 명시하고, 두 상태 사이에 관찰 가능한 `confirmed` 중간 상태가 남지 않게 한다. 해당 경계의 crash 주입 테스트도 추가한다. | Resolved (reviewer) |
| R-07 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/functional-spec.md > UC-U3-02 Confirm and Execute Update, Ordered Flow steps 3–5 | step 3은 ticket ID를 현재 capability와 대조한다고 하지만 capability에는 user·session·conversation만 있고 현재 `TicketUpdateToolInputV1.ticket_id`는 포함되지 않는다. step 4도 U1 pending과 U3 execution끼리만 대조하므로, 같은 actor의 유효한 `pending_ref`와 다른 ticket ID를 넣은 confirm/cancel 호출을 명시적으로 거부하는 경계가 없다. | 현재 tool input의 ticket ID를 U1 pending과 U3 active execution의 ticket ID에 각각 대조하고, mutation·actor·patch hash·base version 검증과 함께 consume 전에 실패하도록 명시한다. ticket ID 불일치 시 PATCH 0회인 계약 테스트를 추가한다. | Resolved (reviewer) |
| R-08 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/functional-spec.md > Durable Publication and Crash Recovery, `active 승격 후, 응답 전` 행 | 응답이 사라진 뒤 "같은 review를 다시 로드"한다고 주장하지만 현재 저장소 연산은 mutation ID 기반 조회뿐이다. 클라이언트가 `pending_ref`를 받기 전에 응답이 유실되면 다음 요청에서 그 mutation ID를 찾을 actor/conversation-scoped locator가 없고, 새 prepare는 이미 존재하는 U1 pending 때문에 거부된다. | 응답 유실 뒤 exact active review를 찾는 durable actor/session/conversation-scoped 조회 계약을 추가하거나, 기존 pending과 execution을 안전하게 retire/invalidate한 뒤 새 prepare를 허용하는 명시적 복구 흐름을 정의한다. 어느 쪽이든 restart·응답 유실 테스트에서 사용자가 막히지 않음을 검증한다. | Resolved (reviewer) |
| R-09 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/functional-design/rules.md > BR3.8 and BR3.9 | BR3.8은 PATCH를 정확히 한 번 호출한다고 단정하지만 BR3.9는 미적용 보장 401 뒤 같은 PATCH를 한 번 더 계속하도록 허용한다. gateway 호출당 1회인지 사용자 operation 전체 1회인지 기준이 달라 총 PATCH 시도 상한을 구현자가 추측해야 한다. | 최초 PATCH 1회와 권위 있는 미적용 보장 401에서만 허용되는 추가 1회를 구분하고, 그 밖의 자동 재전송은 0회라는 총 시도 규칙을 한 곳에 명시한다. | Unresolved |

> R-02 Reviewer note: `replace_update_pending`이 expected-old를 검증하고 이전 row 무효화와 새 row 삽입을 U1 namespace 안의 한 transaction으로 수행한다. U3는 staged-first, U1 replacement, expected-state active CAS 순서를 사용하며 실패 시 이전 review를 유지한다.

> R-05 Reviewer note: 현재 C-02·C-03·C-05는 U3가 `PendingUpdateExecutionV1`과 `ticket_tools_update_v1.pending_update_executions`를 소유함을 명시하고, migration 순서·namespace 격리·lifecycle cleanup·U4 검증 사례까지 고정한다.

> R-06 Reviewer note: confirm과 `consume_once`가 한 U1 repository transaction으로 pending에서 consumed로 전이하며, 관찰 가능한 confirmed 중간 상태를 남기지 않는다. flow·sequence·state machine과 crash test가 같은 의미로 정렬되었다.

> R-07 Reviewer note: confirm 흐름이 현재 `TicketUpdateToolInputV1.ticket_id`를 U1 pending과 U3 execution 양쪽에 consume 전에 대조하며 mismatch에서 consume·PATCH 0회를 검증한다. cancel도 full binding 검증 뒤에만 invalidation한다.

> R-08 Reviewer note: U3 내부 `find_active_for_actor_ticket` locator와 exact U1 binding 재검증이 추가되었다. 응답 유실 뒤 같은 pending_ref를 복구하고, version이 달라 review를 안전하게 재구성할 수 없으면 PATCH 없이 revise/cancel로 수렴한다. restart·actor/ticket 격리 테스트도 명시되었다.

> R-09 Reviewer note: BR3.8과 BR3.9 및 실행 흐름은 gateway 호출당 1회, 전체 operation은 권위 있는 미적용 보장 401 뒤 추가 1회를 포함해 최대 2회로 명확해졌다. 다만 `functional-spec.md`의 Derived Rules Summary는 여전히 “PATCH는 한 번”이라고 축약해 파생 뷰만 최신 규칙과 어긋난다.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| Ruby YAML safe-load of fenced source-of-truth blocks | PASS for `entities.md` and `rules.md` | 두 YAML 원천 블록은 파싱 가능하다. |
| jq traceability shape check | PASS: stage/unit 일치, upstream 18개, coverage 18개 | 공유 story를 포함한 모든 배정 acceptance criterion이 선언되었다. |
| Rule-target and orphan cross-check | PASS: missing targets `[]`, unexplained orphans `[]` | 모든 OK target이 실제 BR ID로 해석되고 BR3.20을 포함한 모든 rule이 upstream criterion에 연결된다. |
| git diff whitespace check | PASS | 검토 대상 산출물에 whitespace 오류가 없다. |
| Mermaid CLI | NOT RUN: `mmdc` unavailable | ER·sequence·state diagram을 수동 재검토했으며 문법상 차단 문제는 보이지 않았지만 CLI 렌더 검증은 수행하지 못했다. |

### Summary

이전의 crash-safety와 cross-unit ownership 차단 항목은 모두 구현 가능한 계약과 검증 시나리오로 닫혔다. 남은 문제는 PATCH 시도 상한에 대한 파생 요약 한 줄의 경미한 표현 불일치뿐이며, source-of-truth rule과 ordered flow는 일관되므로 구현을 막지 않는다.
