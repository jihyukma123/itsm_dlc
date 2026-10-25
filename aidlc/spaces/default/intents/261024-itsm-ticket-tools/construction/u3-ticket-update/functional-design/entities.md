# U3 Ticket Update 엔터티 모델

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`
- `construction/u3-ticket-update/functional-design/functional-design-questions.md`

## Source of Truth

```yaml
entities:
  - name: PendingUpdateMutation
    description: U1이 저장하고 U3가 소비하는, 한 번만 실행할 수 있는 티켓 수정 확인 상태
    owner: U1.TicketOperations
    storage: ticket_tools_state_v1.pending_ticket_mutations
    discriminator: update
    attributes:
      - {name: mutation_id, logical_type: opaque_string, required: true, unique: true}
      - {name: operation, logical_type: enum, required: true, allowed_values: [update], default: update}
      - {name: user_id, logical_type: integer, required: true}
      - {name: session_id, logical_type: opaque_string, required: true}
      - {name: conversation_id, logical_type: opaque_string, required: true}
      - {name: ticket_id, logical_type: opaque_string, required: true}
      - {name: normalized_payload_hash, logical_type: sha256, required: true}
      - {name: base_version, logical_type: integer, required: true, min: 1}
      - {name: status, logical_type: enum, required: true, allowed_values: [pending, confirmed, cancelled, invalidated, expired, consumed], default: pending}
      - {name: expires_at, logical_type: utc_datetime, required: true}
    constraints:
      - 모든 binding 필드는 현재 요청 범위 capability와 정확히 일치해야 한다.
      - confirmation은 생성 후 15분 또는 lifecycle invalidation 중 먼저 발생한 시점까지만 유효하다.
      - confirmed mutation은 consume_once로 최대 한 번만 consumed가 될 수 있다.
      - credential, Authorization, ETag 원문과 전체 상세 응답은 저장하지 않는다.

  - name: PendingUpdateExecution
    description: confirm 요청에서 검증된 patch와 If-Match를 복원하기 위한 U3 전용 durable 실행 record
    owner: U3.TicketOperations
    storage: ticket_tools_update_v1.pending_update_executions
    attributes:
      - {name: mutation_id, logical_type: opaque_string, required: true, unique: true, references: PendingUpdateMutation.mutation_id}
      - {name: user_id, logical_type: integer, required: true}
      - {name: originating_session_id, logical_type: opaque_string, required: true}
      - {name: originating_conversation_id, logical_type: opaque_string, required: true}
      - {name: ticket_id, logical_type: opaque_string, required: true}
      - {name: base_version, logical_type: integer, required: true, min: 1}
      - {name: serialization_version, logical_type: integer, required: true, const: 1}
      - {name: canonical_patch_bytes, logical_type: opaque_bytes, required: true, encoding: compact_UTF8_JSON_fixed_key_order}
      - {name: patch_bytes_hash, logical_type: sha256, required: true}
      - {name: if_match_version, logical_type: opaque_string, required: true}
      - {name: status, logical_type: enum, required: true, allowed_values: [staged, active, retired], default: staged}
      - {name: created_at, logical_type: utc_datetime, required: true}
      - {name: expires_at, logical_type: utc_datetime, required: true}
      - {name: retired_at, logical_type: utc_datetime, required: false}
      - {name: refresh_reservation_id, logical_type: opaque_string, required: false}
      - {name: refresh_state, logical_type: enum, required: false, allowed_values: [reserved, committed, failed]}
      - {name: refresh_used_at, logical_type: utc_datetime, required: false}
      - {name: refresh_base_credential_generation, logical_type: non_negative_integer, required: false}
      - {name: refresh_committed_credential_generation, logical_type: non_negative_integer, required: false}
      - {name: refresh_committed_at, logical_type: utc_datetime, required: false}
    constraints:
      - canonical_patch_bytes는 TicketPatch의 omitted와 explicit null 의미를 보존하는 compact UTF-8 JSON이며 key order가 고정된다.
      - patch_bytes_hash는 canonical_patch_bytes의 정확한 bytes에서 쓰기 시와 PATCH 직전에 다시 계산해 일치해야 한다.
      - if_match_version은 U1 adapter가 body version과 함께 검증한 server-only 값 그대로 저장하고 U3가 재구성하지 않는다.
      - staged record와 record 보유만으로는 실행 권한이 없으며 PATCH에는 exact matching active execution, exact matching U1 pending, 현재 turn의 명시적 확인과 U1 consume_once evidence가 모두 필요하다.
      - credential, Authorization, raw header, 전체 상세 응답과 외부 오류 원문은 저장하지 않는다.
      - U1 pending과 불일치하거나 만료된 orphan은 idempotent cleanup 대상이다.
      - actor scope에서 active execution은 최대 하나이며 replacement activation은 exact old retire와 new promote를 한 U3 transaction으로 수행한다.
      - refresh reservation은 active execution에 최대 한 번 기록하고 reset하지 않으며 credential 값은 저장하지 않는다.

value_objects:
  - name: TicketPatch
    description: ITSM TicketPatchInV1에 맞게 검증되고 실제 변경만 남긴 부분 수정 값
    attributes:
      - {name: title, logical_type: nullable_string, required: false, min: 1, max: 200}
      - {name: description, logical_type: nullable_string, required: false, min: 1, max: 5000}
      - {name: component_id, logical_type: nullable_integer, required: false}
      - {name: model, logical_type: nullable_string, required: false, max: 50}
      - {name: impact_level, logical_type: nullable_enum, required: false, allowed_values: [extensive, significant, moderate, minor, null]}
      - {name: urgency, logical_type: nullable_enum, required: false, allowed_values: [critical, high, medium, low, null]}
      - {name: impact_note, logical_type: nullable_string, required: false, min: 1, max: 1000}
      - {name: is_major, logical_type: nullable_boolean, required: false}
    constraints:
      - omitted와 explicit null은 서로 다른 값이다.
      - 허용 필드가 하나 이상 있어야 하고 현재 상세와 비교한 실제 diff가 비어 있지 않아야 한다.
      - service, status, assignment_group, assignee, transition 필드는 허용하지 않는다.

  - name: UpdateBaseSnapshot
    description: review 생성 시점의 최신 allowlist 상세와 서버 전용 낙관적 잠금 값
    attributes:
      - {name: ticket_id, logical_type: opaque_string, required: true}
      - {name: public_version, logical_type: integer, required: true, min: 1}
      - {name: if_match_version, logical_type: opaque_string, required: true}
      - {name: current_values, logical_type: allowlisted_map, required: true}
    constraints:
      - if_match_version은 strong quoted-decimal ETag에서만 만들어진다.
      - ETag의 십진수 값은 public_version과 정확히 같아야 한다.
      - if_match_version은 모델, 표시 metadata, 로그에 노출하지 않는다.

  - name: SafeUpdateReview
    description: 사용자가 실행 전에 읽고 확인하는 변경 전후 요약
    attributes:
      - {name: pending_ref, logical_type: opaque_string, required: true}
      - {name: ticket_id, logical_type: opaque_string, required: true}
      - {name: base_version, logical_type: integer, required: true, min: 1}
      - {name: normalized_payload_hash, logical_type: sha256, required: true}
      - {name: fields, logical_type: list_of_safe_review_field, required: true, min: 1}
      - {name: choices, logical_type: fixed_list, required: true, allowed_values: [확인, 수정, 취소]}
    constraints:
      - field key와 label은 서버 allowlist에서만 정한다.
      - 외부에서 온 이전 값은 비신뢰 data로 표시한다.

  - name: CurrentTurnEvidence
    description: 현재 HTTP chat 요청의 raw 사용자 turn에서 서버가 계산한 실행 결정
    attributes:
      - {name: turn_id, logical_type: opaque_string, required: true}
      - {name: user_id, logical_type: integer, required: true}
      - {name: session_id, logical_type: opaque_string, required: true}
      - {name: conversation_id, logical_type: opaque_string, required: true}
      - {name: raw_message_sha256, logical_type: sha256, required: true}
      - {name: decision, logical_type: enum, required: true, allowed_values: [explicit_confirm, explicit_cancel, revise_or_ambiguous]}
    constraints:
      - explicit_confirm은 NFKC, outer trim, casefold 후 전체 값이 확인 또는 confirm일 때만 성립한다.
      - tool argument, 과거 turn, 인용문과 추가 문구는 실행 권한이 아니다.

  - name: SafeUpdateResult
    description: 실제 적용이 증명된 경우에만 생성되는 수정 성공 결과
    attributes:
      - {name: ticket_id, logical_type: opaque_string, required: true}
      - {name: applied_changes, logical_type: list_of_safe_review_field, required: true, min: 1}
      - {name: new_version, logical_type: integer, required: true, min: 2}
      - {name: request_id, logical_type: string, required: false}
    constraints:
      - new_version은 base_version보다 커야 한다.
      - applied_changes가 권위 있는 최신 상세에서 확인돼야 한다.

relationships:
  - from: PendingUpdateMutation
    to: PendingUpdateExecution
    cardinality: one-to-one
    direction: mutation_id, user, session, conversation, ticket_id, payload hash and base version must match exactly
  - from: PendingUpdateMutation
    to: TicketPatch
    cardinality: one-to-one-by-normalized-payload-hash
    direction: PendingUpdateMutation references TicketPatch digest
  - from: PendingUpdateMutation
    to: UpdateBaseSnapshot
    cardinality: one-to-one-by-ticket-and-version
    direction: PendingUpdateMutation binds ticket_id and base_version
  - from: SafeUpdateReview
    to: PendingUpdateMutation
    cardinality: one-to-one
    direction: SafeUpdateReview exposes only pending_ref and safe binding summary
  - from: CurrentTurnEvidence
    to: PendingUpdateMutation
    cardinality: one-turn-to-at-most-one-consumption
    direction: CurrentTurnEvidence authorizes confirm or cancel after full binding validation
  - from: SafeUpdateResult
    to: PendingUpdateMutation
    cardinality: zero-or-one-result-per-consumed-mutation
    direction: SafeUpdateResult exists only after authoritative application evidence

repository_queries:
  - name: find_active_for_actor_ticket
    owner: U3.TicketOperations
    scope: internal_response_loss_recovery_only
    input: [user_id, originating_session_id, originating_conversation_id, ticket_id]
    output: at_most_one_PendingUpdateExecution_or_not_found
    constraints:
      - exact actor와 ticket 범위를 모두 요구하며 다른 사용자·세션·대화의 row를 반환하지 않는다.
      - 반환된 row의 mutation ID와 모든 binding을 U1 pending과 다시 대조하기 전에는 pending_ref 또는 실행 권한으로 사용하지 않는다.
      - staged, retired, expired 또는 terminal/missing U1 pending에 연결된 row는 반환하지 않고 멱등 cleanup 대상이 된다.
      - 이 U3 내부 locator는 U1 repository나 다른 Unit 계약을 확장하지 않는다.
```

## Entity Summary

U3는 U1의 `PendingUpdateMutation`을 confirmation authority로 그대로 사용하고, U1 migration을 바꾸지 않는다. 별도 `ticket_tools_update_v1` namespace의 `PendingUpdateExecution`은 그 authority가 참조하는 `canonical_patch_bytes`, `patch_bytes_hash`와 U1이 검증한 `IfMatchVersion`을 재시작 뒤에도 복원하는 U3 내부 실행 record다. 이 record만으로는 실행 권한이 생기지 않으며 exact matching active execution, U1의 full binding, 현재 turn의 명시적 확인과 `consume_once` evidence가 모두 필요하다.

`TicketPatch`, `UpdateBaseSnapshot`, `SafeUpdateReview`, `CurrentTurnEvidence`, `SafeUpdateResult`는 값으로 비교되는 불변 value object다. `PendingUpdateExecution`은 새 review 발행 전에 staged로 저장되고 U1 pending 발행 뒤 expected-state CAS로 active로 승격된다. 중간 crash는 mutation·actor·ticket·patch hash·base version의 exact binding을 대조해 active로 복구하거나 orphan을 정리하므로 patch나 이전 review를 추측하지 않는다. 만료·terminal·고아 row 정리는 접근, startup과 lifecycle 경계에서 멱등 수행한다.

`find_active_for_actor_ticket`은 review 응답이 사용자에게 도달하기 전에 유실된 경우에만 같은 actor와 ticket의 exact active row를 다시 찾는 U3 내부 조회다. 이 조회 결과는 반드시 U1 pending과 재결합해야 하며, record 자체는 PATCH 권한이 아니다.

ITSM `Ticket`은 Assistant 소유 엔터티가 아니다. U3는 요청마다 최신 allowlist projection을 읽고, 수정 성공 여부도 그 권위 있는 projection과 증가한 version으로만 판단한다.

## Assumptions & Open Questions

None.
