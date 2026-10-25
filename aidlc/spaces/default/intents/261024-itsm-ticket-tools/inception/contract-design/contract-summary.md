# ITSM 티켓 도구 계약 설계

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-dependency.md`
- `inception/domain-design/components.md`
- `inception/domain-design/decisions.md`
- `inception/requirements-analysis/requirements.md`
- `inception/refined-mockups/interaction-spec.md`
- `docs/itsm/integration-guide.md`
- `docs/itsm/openapi.json`
- `inception/contract-design/contract-design-questions.md`

## Scope and Contract Principles

- 네 Unit은 하나의 기존 FastAPI 애플리케이션 안에 포함되는 개발 경계다. Unit 사이에 새 HTTP 서비스, 이벤트 버스, gRPC 또는 별도 Agent를 만들지 않는다.
- Unit 간 계약은 동기 typed Python port/interface와 versioned shared schema로 구현한다. 아래 YAML은 구현 언어와 저장 형식에 독립적인 논리 계약이며 Python protocol, Pydantic model, SQLite repository와 contract test가 이를 구체화한다.
- credential과 비밀은 요청 범위의 불투명 capability 뒤에만 존재한다. 어떤 shared schema, function-tool schema·결과, presentation, 로그 또는 오류에도 access token, client secret, OpenAI API key, `Authorization` 값이 들어가지 않는다.
- 티켓·카탈로그·권한·가시성의 원천은 ITSM API v2다. Assistant는 티켓을 복제하거나 로컬 권한을 확대 판단하지 않고 요청별 allowlist projection만 사용한다.
- 공통 계약은 명시적 V1이다. optional field 추가만 호환 변경이며 consumer는 알 수 없는 필드를 무시한다. 필드 제거·이름 변경·의미 변경·필수화는 새 version과 모든 consumer contract test 갱신이 필요하다.
- 외부 HTTP 응답은 기존 필드를 유지하고 선택적 `presentation`만 추가한다. 새 티켓 전용 endpoint는 만들지 않는다.

## Contracts Table

| # | Provider Unit | Consumer | Mechanism | Owner |
|---|---|---|---|---|
| C-01 | U1 `u1-ticket-read-skeleton` | U2 `u2-ticket-write` | 동기 typed Python ports + shared-schema V1 | U1 공통 계약; U2 create extension |
| C-02 | U1 `u1-ticket-read-skeleton` | U3 `u3-ticket-update` | 동기 typed Python ports + shared-schema V1 + 분리된 SQLite ownership | U1 confirmation·atomic replacement 계약; U3 update execution extension |
| C-03 | U1 `u1-ticket-read-skeleton` | U4 `u4-release-assurance` | tool/presentation registry + lifecycle shared-schema V1 | U1 계약, U4 최종 조립·검증 |
| C-04 | U2 `u2-ticket-write` | U4 `u4-release-assurance` | create plugin·ledger·verification shared-schema V1 | U2 |
| C-05 | U3 `u3-ticket-update` | U4 `u4-release-assurance` | update plugin·version·verification shared-schema V1 | U3 |
| C-06 | U4가 조립한 기존 FastAPI 애플리케이션 | External: 기존 browser client | 기존 REST/JSON chat API의 OpenAPI 3.1 하위 호환 확장 | U1 presentation envelope; U2·U3 mapper; U4 조립 |
| C-07 | External: ITSM API v2 | U1 `ItsmGateway`와 이를 소비하는 U2·U3 operations | HTTPS/JSON OpenAPI 3.1 outbound profile | ITSM 원본 계약; U1 adapter profile |

의존 DAG의 모든 직접 edge `U1→U2`, `U1→U3`, `U1→U4`, `U2→U4`, `U3→U4`가 C-01~C-05에 각각 대응한다. C-06과 C-07은 외부 경계다.

## C-01 — U1 Common Runtime to U2 Ticket Write

U2는 U1이 소유한 요청 범위 capability, 안전한 gateway 결과, 확인 repository, tool registry와 presentation mapper registry만 사용한다. U2는 U1의 공통 migration 또는 registry 구현 파일을 수정하지 않고 create-specific 타입과 plugin을 등록한다.

```yaml
schema: aidlc.shared/v1
name: U1ToU2TicketWrite
version: 1
contract_definitions:
  ItsmGatewayV1: {defined_by: ports.ItsmGatewayV1}
  CredentialRefreshPortV1: {defined_by: ports.CredentialRefreshPortV1}
  PendingMutationRepositoryV1: {defined_by: ports.PendingMutationRepositoryV1}
  TicketOperationPolicyV1: {defined_by: ports.TicketOperationPolicyV1}
compatibility:
  additive_optional_fields: allowed
  unknown_fields: ignore
  remove_rename_reinterpret_or_require: new_version

runtime_types:
  TicketRequestCapability:
    owner: U1.IdentitySession
    scope: one_http_request
    serializable: false
    loggable: false
    model_visible: false
    fields_visible_to_consumer:
      user_id: integer
      session_id: opaque_string
      conversation_id: opaque_string
    server_only_metadata:
      credential_generation: {type: non_negative_integer, monotonic_per_atomic_session_credential_commit: true, model_visible: false, loggable: false}
    delegated_credential:
      access: only_via_itsm_gateway
      expose_value: never

  SafeErrorV1:
    additional_properties: false
    fields:
      version: {const: 1}
      code:
        enum: [invalid_input, authentication_required, permission_denied, not_found, conflict, rate_limited, upstream_unavailable, ambiguous_result]
      message_key: {type: string, source: server_allowlist}
      retryable: {type: boolean}
      request_id: {type: string, optional: true}
      retry_after_seconds: {type: integer, minimum: 0, optional: true}
      field_errors: {type: array, items: SafeFieldErrorV1, optional: true}
    forbidden: [raw_detail, exception, headers, authorization, access_token, client_secret, openai_api_key]

  SafeFieldErrorV1:
    additional_properties: false
    required: [field, code, message_key]
    fields:
      field: {type: string, source: server_allowlist}
      code: {type: string, source: server_allowlist}
      message_key: {type: string, source: server_allowlist}
      allowed_values: {type: array, items: string, optional: true, source: allowlisted_catalog_projection}

  CatalogSelectorV1:
    additional_properties: false
    exactly_one_of: [id, name]
    fields:
      id: {type: [string, integer], optional: true}
      name: {type: string, min_length: 1, optional: true}

  CatalogResolutionRequestV1:
    additional_properties: false
    required: [service]
    fields:
      service: {type: CatalogSelectorV1}
      component: {type: CatalogSelectorV1, optional: true}
      model: {type: CatalogSelectorV1, optional: true}
    rule: resolve_only_one_active_exact_normalized_match_and_validate_component_service_relation

  CatalogServicesQueryV1:
    additional_properties: false
    fields:
      include_deprecated: {const: false}

  CatalogModelsQueryV1:
    additional_properties: false
    fields:
      include_retired: {const: false}

  SafeServiceCatalogPageV1:
    additional_properties: false
    required: [services]
    fields:
      services: {type: array, items: allowlisted_service_and_component_projection}
    external_text_trust: untrusted_data

  SafeModelCatalogPageV1:
    additional_properties: false
    required: [models]
    fields:
      models: {type: array, items: allowlisted_model_projection}
    external_text_trust: untrusted_data

  ResolvedCatalogV1:
    additional_properties: false
    required: [service_id]
    fields:
      service_id: {type: string}
      component_id: {type: integer, optional: true}
      model: {type: string, optional: true}

  SafeTicketDetailV1:
    owner: U1
    additional_properties: false
    public_projection:
      required: [id, title, description, service, impact_level, urgency, impact_note, status, priority, version]
      optional: [component, model, classification, is_major, requester, assignment_group, assignee, occurred_at, created_at, updated_at]
      field_contract:
        status: {type: string, enum: [received, assigned, investigating, pending, monitoring, resolved, closed, cancelled]}
        version: {type: integer, minimum: 1}
    server_only_metadata:
      etag: {type: opaque_string, expose_to_model: false}
      if_match:
        type: opaque_string
        format: quoted_decimal_version
        exact_value: '"<public_projection.version>"'
        derived_by: U1.ItsmGateway_from_validated_ETag_response_header
        expose_to_model: false
    metadata_invariants:
      - detail_read_for_update_requires_ETag
      - ETag_must_be_a_strong_quoted_decimal_equal_to_public_projection.version
      - missing_weak_or_mismatched_ETag_returns_safe_upstream_unavailable_and_forbids_PATCH
    external_text_trust: untrusted_data
    forbidden: [authorization, raw_headers, raw_problem_detail]

  CanonicalRequestBytesV1:
    model_visible: false
    serializable_to_ledger: true
    required: [serialization_version, body_bytes, sha256]
    forbidden_content: [credential, authorization, client_secret, openai_api_key]

  IdempotencyKeyRef:
    model_visible: false
    type: opaque_runtime_reference
    value_loggable: false

  SafeCreateTransportResultV1:
    additional_properties: false
    required: [ticket, idempotent_replayed]
    fields:
      ticket: {type: SafeTicketDetailV1}
      idempotent_replayed: {type: boolean}
      request_id: {type: string, optional: true}
      location: {type: string, optional: true, validated_same_origin_path: true}

  LifecycleSelectorV1:
    additional_properties: false
    at_least_one_of: [user_id, session_id, conversation_id]
    fields:
      user_id: {type: integer, optional: true}
      session_id: {type: opaque_string, optional: true}
      conversation_id: {type: opaque_string, optional: true}

  PendingTicketMutationV1:
    owner: U1.TicketOperations
    additional_properties: false
    required: [mutation_id, operation, user_id, session_id, conversation_id, normalized_payload_hash, status, expires_at]
    fields:
      mutation_id: {type: opaque_string}
      operation: {enum: [create, update]}
      user_id: {type: integer}
      session_id: {type: opaque_string}
      conversation_id: {type: opaque_string}
      normalized_payload_hash: {type: sha256}
      ticket_id: {type: [opaque_string, 'null'], optional: true}
      base_version: {type: [integer, 'null'], minimum_when_non_null: 1, optional: true}
      status: {enum: [pending, confirmed, cancelled, invalidated, expired, consumed]}
      expires_at: {type: utc_datetime}
    discriminator:
      property: operation
      mapping:
        create: PendingCreateMutationV1
        update: PendingUpdateMutationV1

  PendingCreateMutationV1:
    owner: U1.TicketOperations
    extends: PendingTicketMutationV1
    required: [ticket_id, base_version]
    refinements:
      operation: {const: create}
      ticket_id: {const: null}
      base_version: {const: null}

  PendingUpdateMutationV1:
    owner: U1.TicketOperations
    extends: PendingTicketMutationV1
    required: [ticket_id, base_version]
    refinements:
      operation: {const: update}
      ticket_id: {type: opaque_string}
      base_version: {type: integer, minimum: 1}

  ConsumedMutationEvidenceV1:
    owner: U1.TicketOperations
    additional_properties: false
    required: [mutation_id, confirmed_at]
    fields:
      mutation_id: {type: opaque_string}
      confirmed_at: {type: utc_datetime}
    authority: proof_that_the_bound_pending_mutation_was_confirmed_and_consumed_once
    forbidden: [credential, authorization, idempotency_key, canonical_request_bytes]

  CredentialRefreshReservationV1:
    owner: U2.TicketOperations
    model_visible: false
    loggable: false
    additional_properties: false
    required: [create_attempt_id, refresh_reservation_id, refresh_used_at]
    fields:
      create_attempt_id: {type: opaque_string}
      refresh_reservation_id: {type: opaque_string}
      refresh_used_at: {type: utc_datetime}
      base_credential_generation: {type: non_negative_integer, optional: true}
      refresh_state: {enum: [reserved, committed, failed], optional: true}
      committed_credential_generation: {type: non_negative_integer, optional: true}
      refresh_committed_at: {type: utc_datetime, optional: true}
    authority: proof_that_U2_durably_consumed_the_one_shot_refresh_reservation_before_invocation_and_can_reconcile_the_session_commit_without_a_second_invocation
    invariants:
      - committed_credential_generation_when_present_is_greater_than_base_credential_generation
      - reserved_is_written_before_port_invocation
      - failed_and_committed_are_terminal_for_refresh_invocation
    forbidden: [credential, authorization, idempotency_key, canonical_request_bytes]

ports:
  ItsmGatewayV1:
    owner: U1
    operations:
      list_services_once:
        input: CatalogServicesQueryV1
        output: "Result[SafeServiceCatalogPageV1, SafeErrorV1]"
        endpoint: GET_/api/v2/catalog/services
      list_models_once:
        input: CatalogModelsQueryV1
        output: "Result[SafeModelCatalogPageV1, SafeErrorV1]"
        endpoint: GET_/api/v2/catalog/models
      create_ticket_once:
        input: [TicketRequestCapability, CanonicalRequestBytesV1, IdempotencyKeyRef]
        output: "Result[SafeCreateTransportResultV1, SafeErrorV1]"
    transport_policy:
      timeout_per_attempt: ITSM_TIMEOUT_SECONDS
      http_attempts_per_call: 1
      retries_sleeps_and_backoff: forbidden
      token_refresh_decision: forbidden
      responsibility: serialize_send_parse_and_return_one_allowlisted_transport_result

  CredentialRefreshPortV1:
    owner: U1.IdentitySession
    operations:
      refresh_delegated_capability_once:
        input: [TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline]
        output: "Result[TicketRequestCapability, SafeErrorV1]"
    preconditions:
      - current_capability_and_reservation_actor_binding_match
      - reservation_was_durably_marked_used_before_this_call
      - reservation_base_credential_generation_matches_current_capability
      - remaining_deadline_is_positive
    policy:
      token_exchange_attempts_per_call: 1
      internal_retries: 0
      caller_invocations_per_create_attempt: 1
      credential_commit: atomically_replace_the_existing_server_session_delegated_credential_before_returning_success
      success_output: new_request_scoped_capability_bound_to_the_same_user_session_and_conversation_with_a_higher_server_only_credential_generation
      raw_token_or_exchange_response_crosses_port: false
    crash_semantics:
      before_credential_commit: reservation_remains_used_and_caller_must_fail_closed_without_second_refresh
      after_credential_commit_before_success_return: a_later_request_restores_the_committed_credential_from_the_existing_session_and_marks_the_reservation_committed_when_credential_generation_is_higher_than_the_recorded_base_without_refreshing_again
      reservation_reset_or_replay: forbidden
    provider_contract_tests:
      - one_port_call_per_consumed_reservation_performs_at_most_one_token_exchange
      - successful_return_occurs_only_after_atomic_session_credential_commit
      - returned_capability_preserves_actor_binding_and_exposes_no_credential
      - failure_or_crash_never_requests_a_second_exchange_for_the_same_create_attempt

  TicketOperationPolicyV1:
    owner: U1.TicketOperations_contract_with_U2_create_extension
    create:
      max_total_http_attempts: 2
      counter_scope: one_global_attempt_count_shared_by_initial_send_token_refresh_recall_and_ambiguous_recovery
      retry_requires_same_idempotency_key: true
      retry_requires_byte_identical_body: true
      prepare_order: persist_U2_TicketCreateAttempt_prepared_before_U1_pending_review
      execution_requires:
        - U1_consume_once_evidence_bound_idempotently_to_the_same_U2_attempt
        - U2_CAS_claim_with_unique_claim_id_and_claim_deadline_at
        - attempt_count_less_than_2_before_claim
      claim_effect: increment_attempt_count_when_POST_starts
      live_claim_takeover: forbidden_before_claim_deadline_at
      stale_or_ambiguous_claim: reconcile_result_before_any_further_POST
      final_retry_when_result_lookup_fails_or_remains_ambiguous: allowed_only_if_attempt_count_less_than_2_with_same_key_and_bytes
      token_expired_401_when_not_applied_is_guaranteed: retryable_no_apply_with_shared_attempt_budget
      credential_refresh: durable_U2_reservation_then_one_CredentialRefreshPortV1_call_with_no_second_invocation_before_first_POST_when_the_capability_is_expired_or_near_expiry_or_after_a_guaranteed_no_apply_401
      refresh_recovery: reserved_plus_same_generation_fails_closed_while_reserved_plus_higher_current_session_generation_is_marked_committed_without_a_second_port_call
      status_429: return_immediately_without_wait_or_retry
      ambiguous_after_second_result: terminal_ambiguous_and_no_more_POST
    catalog_resolution:
      owner: TicketOperations
      input: CatalogResolutionRequestV1
      calls:
        - list_services_once_when_service_or_component_resolution_is_needed
        - list_models_once_when_model_resolution_is_needed
      matching: unique_active_normalized_ID_or_name_match
      component_service_validation: required
      automatic_retry_per_catalog_endpoint: 0
      output: "Result[ResolvedCatalogV1, SafeErrorV1]"
      ticket_attempt_counter: catalog_calls_do_not_count_as_ticket_POST_attempts
    invariant: only_this_port_may_call_ItsmGatewayV1_more_than_once_for_one_user_operation

  PendingMutationRepositoryV1:
    owner: U1
    operations:
      put: "PendingCreateMutationV1 | PendingUpdateMutationV1 -> mutation_id"
      get: "mutation_id -> PendingTicketMutationV1 | not_found"
      confirm: "[mutation_id, user_id, session_id, conversation_id, normalized_payload_hash] -> confirmed_or_rejected"
      consume_once: "confirmed_binding -> ConsumedMutationEvidenceV1 | rejected"
      invalidate: "LifecycleSelectorV1 -> count"
    invariants:
      - every_binding_field_must_match
      - discriminator_variant_invariants_are_enforced_on_write_and_read
      - invalidation_and_consume_are_idempotent
      - credential_is_never_persisted
    contract_tests:
      - create_variant_put_get_round_trip_preserves_null_target_and_version
      - update_variant_put_get_round_trip_preserves_ticket_and_base_version
      - malformed_discriminator_or_variant_shape_is_rejected

extensions_owned_by_u2:
  TicketCreateInV1:
    required: [title, description, service_id, impact_level, urgency, impact_note, occurred_at]
    optional: [component_id, model, classification]
    additional_properties: false
    source: resolved_and_normalized_from_TicketWriteDraftV1
  TicketWritePluginV1:
    tool_name: ticket_write
    provides: [function_tool_factory, create_presentation_mapper]
    registers_via: U1.RegistryV1
```

## C-02 — U1 Common Runtime to U3 Ticket Update

U3는 U1의 상세 조회 projection과 공통 확인 repository를 소비한다. U3는 U2의 create binding·ledger·migration에 의존하지 않으며 update-specific patch/version binding, durable execution record와 plugin을 소유한다. U1은 자기 `pending_ticket_mutations` 안에서만 원자적 replacement를 수행하고 U3 storage를 쓰지 않는다.

```yaml
schema: aidlc.shared/v1
name: U1ToU3TicketUpdate
version: 1
compatibility:
  additive_optional_fields: allowed
  unknown_fields: ignore
  remove_rename_reinterpret_or_require: new_version

imports_from_u1:
  - TicketRequestCapability
  - SafeErrorV1
  - SafeTicketDetailV1
  - PendingTicketMutationV1
  - PendingUpdateMutationV1
  - PendingMutationRepositoryV1
  - RegistryV1
  - TicketPresentationV1

types:
  IfMatchVersion:
    type: opaque_string
    derived_from: SafeTicketDetailV1.server_only_metadata.if_match
    exact_wire_format: '"<decimal SafeTicketDetailV1.public_projection.version>"'
    constructed_and_validated_by: U1.ItsmGateway_detail_response_adapter
    transformation_by_u3: forbidden
    model_visible: false
    contract_tests:
      - version_3_and_ETag_quoted_3_produces_If_Match_quoted_3
      - missing_weak_non_decimal_or_version_mismatched_ETag_forbids_PATCH

  SafeUpdateTransportResultV1:
    additional_properties: false
    required: [ticket, new_version]
    fields:
      ticket: {type: SafeTicketDetailV1}
      new_version: {type: integer, minimum: 1}
      request_id: {type: string, optional: true}

  PendingUpdateExecutionV1:
    owner: U3.TicketOperations_update_extension
    model_visible: false
    additional_properties: false
    required: [mutation_id, user_id, originating_session_id, originating_conversation_id, ticket_id, base_version, serialization_version, canonical_patch_bytes, patch_bytes_hash, if_match_version, status, created_at, expires_at]
    fields:
      mutation_id: {type: opaque_string}
      user_id: {type: integer}
      originating_session_id: {type: opaque_string}
      originating_conversation_id: {type: opaque_string}
      ticket_id: {type: opaque_string}
      base_version: {type: integer, minimum: 1}
      serialization_version: {const: 1}
      canonical_patch_bytes: {type: opaque_bytes, encoding: compact_UTF8_JSON_fixed_key_order}
      patch_bytes_hash: {type: sha256}
      if_match_version: {type: IfMatchVersion}
      status: {enum: [staged, active, retired]}
      created_at: {type: utc_datetime}
      expires_at: {type: utc_datetime}
      retired_at: {type: utc_datetime, optional: true}
      refresh_reservation_id: {type: opaque_string, optional: true}
      refresh_state: {enum: [reserved, committed, failed], optional: true}
      refresh_used_at: {type: utc_datetime, optional: true}
      refresh_base_credential_generation: {type: non_negative_integer, optional: true}
      refresh_committed_credential_generation: {type: non_negative_integer, optional: true}
      refresh_committed_at: {type: utc_datetime, optional: true}
    forbidden: [credential, authorization, access_token, refresh_credential, raw_headers, raw_problem_detail]
    authority: record_alone_never_authorizes_PATCH

  UpdateCredentialRefreshReservationV1:
    owner: U3.TicketOperations_update_extension
    model_visible: false
    loggable: false
    additional_properties: false
    required: [mutation_id, refresh_reservation_id, refresh_used_at, base_credential_generation, refresh_state]
    fields:
      mutation_id: {type: opaque_string}
      refresh_reservation_id: {type: opaque_string}
      refresh_used_at: {type: utc_datetime}
      base_credential_generation: {type: non_negative_integer}
      refresh_state: {enum: [reserved, committed, failed]}
      committed_credential_generation: {type: non_negative_integer, optional: true}
      refresh_committed_at: {type: utc_datetime, optional: true}
    authority: proof_that_U3_durably_consumed_the_one_shot_update_refresh_before_invocation
    forbidden: [credential, authorization, access_token, refresh_credential, canonical_patch_bytes, if_match_version]

  UpdatePendingReplacementV1:
    owner: U1.TicketOperations
    model_visible: false
    additional_properties: false
    required: [old_mutation_id, new_mutation_id, user_id, session_id, conversation_id, operation, new_ticket_id, new_normalized_payload_hash, new_base_version, committed, affected_old_rows, inserted_new_rows]
    fields:
      old_mutation_id: {type: [opaque_string, 'null']}
      new_mutation_id: {type: opaque_string}
      user_id: {type: integer}
      session_id: {type: opaque_string}
      conversation_id: {type: opaque_string}
      operation: {const: update}
      new_ticket_id: {type: opaque_string}
      new_normalized_payload_hash: {type: sha256}
      new_base_version: {type: integer, minimum: 1}
      committed: {const: true}
      affected_old_rows: {type: integer, enum: [0, 1]}
      inserted_new_rows: {const: 1}
    invariants:
      - prepare_has_null_old_mutation_id_and_affected_old_rows_zero
      - revise_has_exact_old_mutation_id_and_affected_old_rows_one
      - actor_and_new_binding_equal_the_committed_PendingUpdateMutationV1
      - result_exists_only_after_the_U1_transaction_commits
    authority: immutable_evidence_for_U3_activate_replacement_without_cross_owner_writes
    forbidden: [credential, authorization, canonical_patch_bytes, if_match_version]

  TicketPatchInV1:
    required: []
    optional: [title, description, component_id, model, impact_level, urgency, impact_note, is_major]
    additional_properties: false
    omit_and_null_are_distinct: true
    field_contract:
      title: {type: [string, 'null'], min_length: 1, max_length: 200}
      description: {type: [string, 'null'], min_length: 1, max_length: 5000}
      component_id: {type: [integer, 'null']}
      model: {type: [string, 'null'], max_length: 50}
      impact_level: {type: [string, 'null'], non_null_enum: [extensive, significant, moderate, minor]}
      urgency: {type: [string, 'null'], non_null_enum: [critical, high, medium, low]}
      impact_note: {type: [string, 'null'], min_length: 1, max_length: 1000}
      is_major: {type: [boolean, 'null']}
    semantics:
      omitted_field: leave_unchanged
      explicit_null: clear_value_as_allowed_by_authoritative_contract
      empty_or_no_actual_diff: reject_locally_without_PATCH
    forbidden: [service_id, status, assignment_group_id, assignee_id, transition]

ports:
  ItsmGatewayV1:
    owner: U1
    operations:
      read_ticket_once:
        input: [TicketRequestCapability, ticket_id]
        output: "Result[SafeTicketDetailV1, SafeErrorV1]"
      update_ticket_once:
        input: [TicketRequestCapability, ticket_id, TicketPatchInV1, IfMatchVersion]
        output: "Result[SafeUpdateTransportResultV1, SafeErrorV1]"
    transport_policy:
      timeout_per_attempt: ITSM_TIMEOUT_SECONDS
      http_attempts_per_call: 1
      retries_sleeps_and_backoff: forbidden
      token_refresh_decision: forbidden
      responsibility: serialize_send_parse_and_return_one_allowlisted_transport_result

  UpdateCredentialRefreshPortV1:
    owner: U1.IdentitySession
    operations:
      refresh_update_capability_once:
        input: [TicketRequestCapability, UpdateCredentialRefreshReservationV1, remaining_deadline]
        output: "Result[TicketRequestCapability, SafeErrorV1]"
    preconditions:
      - reservation_mutation_and_actor_binding_match_the_active_U3_execution_and_consumed_U1_evidence
      - reservation_was_durably_marked_reserved_before_this_call
      - reservation_base_credential_generation_matches_current_capability
      - remaining_deadline_is_positive
    policy:
      token_exchange_attempts_per_call: 1
      internal_retries: 0
      caller_invocations_per_update_execution: 1
      allowed_entry: first_PATCH_returned_token_expired_401_with_authoritative_no_apply_guarantee
      credential_commit: atomically_replace_the_existing_server_session_delegated_credential_before_returning_success
      success_output: new_request_scoped_capability_bound_to_the_same_user_session_and_conversation_with_a_higher_server_only_credential_generation
      raw_token_or_exchange_response_crosses_port: false
    crash_semantics:
      before_credential_commit: reservation_remains_used_and_U3_fails_closed_without_second_refresh
      after_credential_commit_before_success_return: later_request_compares_session_credential_generation_and_marks_the_reservation_committed_without_refreshing_again
      reservation_reset_or_second_port_invocation: forbidden
    provider_contract_tests:
      - one_port_call_per_update_reservation_performs_at_most_one_token_exchange
      - successful_return_occurs_only_after_atomic_session_credential_commit
      - returned_capability_preserves_actor_binding_and_exposes_no_credential
      - failure_or_crash_never_requests_a_second_exchange_for_the_same_mutation

  TicketOperationPolicyV1:
    owner: U1.TicketOperations_contract_with_U3_update_extension
    read_for_update:
      max_total_http_attempts: 2
      retry_delay_seconds: 0.25
      retry_only_on: [timeout, transport_error, 500, 502, 503, 504]
      token_refresh_recall_counts_toward_attempt_limit: true
    patch:
      automatic_retries: 0
      status_429: return_immediately_without_wait_or_retry
      status_412_or_428: return_conflict_then_read_latest
      ambiguous_result: never_resend_PATCH_and_read_latest
      safe_401_refresh_recall: allowed_once_only_when_authoritative_contract_guarantees_not_applied
    invariant: only_this_port_may_orchestrate_multiple_gateway_calls_for_one_user_operation

  PendingMutationRepositoryV1:
    operations:
      replace_update_pending:
        owner: U1
        input: [TicketRequestCapability, expected_old_mutation_id_or_null, PendingUpdateMutationV1]
        output: "Result[UpdatePendingReplacementV1, SafeErrorV1]"
        transaction: verify_expected_old_then_invalidate_exact_old_and_insert_new_atomically_inside_ticket_tools_state_v1
        prepare_semantics: expected_old_null_requires_no_other_pending_update_in_the_same_actor_scope
        revise_semantics: expected_old_must_match_same_user_session_conversation_operation_and_pending_status
        failure_semantics: validation_or_insert_failure_changes_neither_old_nor_new_row
        forbidden: [write_U3_storage, invalidate_by_broad_selector]
    consume_binding:
      match_all: [user_id, session_id, conversation_id, operation, ticket_id, normalized_payload_hash, base_version]
    invalidate_when_changed:
      - user
      - session
      - conversation
      - ticket_id
      - normalized_patch
      - base_version

  PendingUpdateExecutionRepositoryV1:
    owner: U3
    storage: ticket_tools_update_v1.pending_update_executions
    operations:
      stage: "PendingUpdateExecutionV1(status=staged) -> mutation_id"
      get: "mutation_id -> PendingUpdateExecutionV1 | not_found"
      promote_active: "[mutation_id, expected_status=staged, exact_binding] -> active_or_rejected"
      activate_replacement: "[new_mutation_id, expected_status=staged, expected_old_mutation_id_or_null, exact_actor_binding] -> active_or_rejected"
      retire: "[mutation_id, expected_status] -> retired_or_current"
      cleanup: "[now, lifecycle_selector_optional] -> count"
      reserve_refresh_once: "[mutation_id, expected_status=active, base_credential_generation] -> UpdateCredentialRefreshReservationV1 | rejected"
      reconcile_refresh_after_restart: "[mutation_id, current_session_credential_generation] -> committed_or_failed_without_invocation"
    invariants:
      - canonical_patch_hash_is_recomputed_on_write_and_before_PATCH
      - staged_and_record_possession_are_not_execution_authority
      - active_requires_exact_matching_U1_pending_mutation
      - activate_replacement_atomically_retires_the_exact_old_execution_when_present_and_promotes_the_new_staged_execution
      - at_most_one_active_execution_per_user_session_conversation_scope
      - terminal_or_missing_U1_pending_makes_the_record_non_authorizing
      - transitions_and_cleanup_are_idempotent
      - refresh_reservation_is_consumed_at_most_once_and_never_reset
      - credential_is_never_persisted

extensions_owned_by_u3:
  TicketUpdatePluginV1:
    tool_name: ticket_update
    provides: [function_tool_factory, update_presentation_mapper]
    registers_via: U1.RegistryV1
  success_evidence:
    required: [applied_changes, new_version]
  publication_order:
    - persist_PendingUpdateExecutionV1_as_staged
    - call_U1_replace_update_pending
    - atomically_retire_the_exact_old_U3_execution_when_present_and_promote_the_new_row_active_by_expected_state_CAS
  crash_recovery:
    after_stage_before_U1_commit: retire_or_delete_non_authorizing_orphan
    after_U1_commit_before_active: promote_only_after_exact_mutation_actor_ticket_patch_hash_and_base_version_match
    mismatch: fail_closed_and_retire_orphan
```

## C-03 — U1 Registries and Lifecycle to U4 Final Assembly

U4는 U1의 registry와 lifecycle port를 통해 세 독립 plugin을 조립한다. 공통 registry 파일을 U2·U3가 수정하지 않으며 최종 Agent의 tool 이름 집합은 정확히 세 개다.

```yaml
schema: aidlc.shared/v1
name: U1ToU4FinalAssembly
version: 1

contract_definitions:
  RegistryV1: {defined_by: registry}
  CanonicalTicketQueryV1: {defined_by: canonical_ticket_query}
  TicketCursorRepositoryV1: {defined_by: cursor_repository}
  PresentationHistoryRepositoryV1: {defined_by: presentation_history_repository}
  AssistantMessageCorrelationV1:
    additional_properties: false
    required: [conversation_id, assistant_sequence, assistant_text_sha256]
    fields:
      conversation_id: {type: opaque_string}
      assistant_sequence: {type: integer, minimum: 0}
      assistant_text_sha256: {type: sha256}

registry:
  contract_type: RegistryV1
  owner: U1
  mutation_model: register_plugin_without_editing_common_registry
  duplicate_tool_name: fail_closed
  unknown_contract_version: fail_closed
  tool_names_at_final_assembly:
    exact_set: [ticket_read, ticket_write, ticket_update]
  plugin_contract:
    required: [contract_version, tool_name, function_tool_factory, presentation_mappers]
    contract_version: {const: 1}
    presentation_mapper_key: allowlisted_kind

runner_context:
  required: [current_user, ticket_request_capability, ticket_operations, current_turn_evidence]
  constructed_by: ApplicationLifecycle
  source_of_identity: server_session_only
  current_turn_evidence:
    type: CurrentTurnEvidenceV1
    source: raw_current_http_chat_message_captured_before_Runner
    model_argument_authority: none
  forbidden_model_inputs: [access_token, refresh_credential, client_secret, openai_api_key, authorization_header]

canonical_ticket_query:
  contract_type: CanonicalTicketQueryV1
  owner: U1.TicketOperations
  model_visible: false
  required: [query_serialization_version, canonical_normalized_query_json, normalized_query_hash]
  canonical_fields_in_order: [q, status, priority, service_id, component_id, model, assignment_group_id, assignee, requester, classification, is_major, created_from, created_to, updated_from, sort, limit]
  normalization:
    omitted_optional_fields: omitted
    repeated_values: stable_contract_order_after_validation
    timestamps: UTC_RFC3339
    sort_and_limit_defaults: materialized
    json: UTF8_no_insignificant_whitespace_fixed_key_order
    hash: sha256_of_exact_canonical_normalized_query_json_bytes
  reconstruction_rule: repository_returns_the_exact_validated_query_object_represented_by_the_stored_canonical_JSON

cursor_repository:
  contract_type: TicketCursorRepositoryV1
  owner: U1.TicketOperations
  storage:
    migration_owner: U1
    namespace: ticket_tools_state_v1
    database: existing_server_session_SQLite_database
    table: ticket_cursor_bindings
  model_visible_value: continuation_ref_only
  binding:
    required: [continuation_ref, user_id, session_id, conversation_id, query_serialization_version, canonical_normalized_query_json, normalized_query_hash, upstream_cursor, created_at, expires_at]
    canonical_normalized_query_json: validated_filters_sort_and_limit_needed_to_reconstruct_the_exact_next_request
    forbidden: [credential, authorization, unvalidated_query]
  operations:
    issue: "[capability, query_serialization_version, canonical_normalized_query_json, normalized_query_hash, upstream_cursor] -> continuation_ref"
    resolve_once: "[capability, continuation_ref] -> [CanonicalTicketQueryV1, upstream_cursor] or SafeErrorV1"
    invalidate: "LifecycleSelectorV1 -> count"
  invariants:
    - continuation_ref_is_unpredictable_but_not_authority
    - every_binding_field_matches_current_capability
    - upstream_cursor_is_never_model_visible
    - changed_filter_or_sort_requires_new_first_page
    - issue_recomputes_hash_and_rejects_noncanonical_or_mismatched_query_material
    - resolve_recomputes_hash_before_exact_query_reconstruction
    - resolve_and_invalidation_are_idempotent
  contract_tests:
    - issue_then_resolve_round_trip_preserves_serialization_version_canonical_query_and_upstream_cursor
    - changed_or_tampered_query_material_or_hash_is_rejected
  retention_and_cleanup:
    active_until_earliest_of: [session_expiry, user_switch, conversation_clear, logout, upstream_invalid_cursor]
    expired_or_invalidated_rows: delete_idempotently_on_access_and_startup_cleanup

presentation_history_repository:
  contract_type: PresentationHistoryRepositoryV1
  owner: U1.AgentConversation
  storage:
    migration_owner: U1
    namespace: ticket_tools_history_v1
    database: existing_agent_history_SQLite_database
    table: ticket_message_presentations
  concurrency: one_application_lock_per_conversation
  correlation:
    type: AssistantMessageCorrelationV1
    fields: [conversation_id, assistant_sequence, assistant_text_sha256]
    generated_from: persisted_SDK_session_item_after_Runner_completion
  row:
    required: [conversation_id, assistant_sequence, assistant_text_sha256, presentation_version, canonical_presentation_json, created_at]
    unique_key: [conversation_id, assistant_sequence]
    forbidden: [credential, authorization, raw_tool_trace, raw_problem_detail]
  operations:
    commit_for_persisted_message:
      precondition: exact_correlated_assistant_message_exists_under_conversation_lock
      transaction: verify_correlation_and_insert_or_replace_one_companion_row_atomically
      response_rule: expose_presentation_only_after_commit_readback_succeeds
      failure_rule: return_existing_text_reply_without_presentation_and_never_claim_structured_success
    load_for_history:
      behavior: left_join_SDK_assistant_items_by_sequence_and_text_hash
      missing_invalid_or_unknown_version: omit_presentation_and_use_text_fallback
    clear_conversation:
      idempotent: true
      orphan_rule: rows_without_a_matching_SDK_message_are_never_returned_and_are_cleanup_eligible
  compatibility:
    existing_rows_without_metadata: valid_text_only_history
    process_restart: reconstruct_by_persisted_correlation_not_memory
  retention_and_cleanup:
    retention: exactly_the_matching_conversation_history_lifetime
    delete_on: [user_switch, logout, conversation_clear]
    orphan_rows: delete_idempotently_on_history_load_and_startup_cleanup

common_storage_allocation:
  owner: U1
  logical_contract: ticket_tools_common_v1
  physical_namespaces:
    ticket_tools_state_v1:
      database: existing_server_session_SQLite_database
      tables: [pending_ticket_mutations, ticket_cursor_bindings]
    ticket_tools_history_v1:
      database: existing_agent_history_SQLite_database
      tables: [ticket_message_presentations]
  downstream_rule: U2_and_U3_must_not_edit_either_U1_migration_namespace
  classification:
    ticket_cursor_bindings: technical_continuation_record_not_ITSM_domain_entity
    ticket_message_presentations: technical_history_metadata_record_not_ITSM_domain_entity

downstream_storage_allocations:
  ticket_tools_create_v1:
    owner: U2
    database: existing_server_session_SQLite_database
    tables: [ticket_create_attempts]
  ticket_tools_update_v1:
    owner: U3
    database: existing_server_session_SQLite_database
    tables: [pending_update_executions]
    migration_order: after_U1_ticket_tools_state_v1_and_before_U3_plugin_activation
    retention_and_cleanup:
      staged: non_authorizing_and_cleanup_on_access_or_startup_when_unmatched_or_expired
      active: non_authorizing_immediately_when_paired_U1_pending_is_terminal_or_missing
      terminal: retire_idempotently_then_delete_after_the_existing_session_state_cleanup_window
  isolation: U2_and_U3_never_edit_each_others_or_U1_migration_namespaces

lifecycle_port:
  owner: U1
  operations:
    invalidate_pending_mutations:
      selectors: [user_id, session_id, conversation_id]
      idempotent: true
    preserve_create_attempt_ledger:
      on: [user_switch, logout, conversation_clear, session_expiry]
      minimum_retention_hours: 24
    retire_update_executions:
      owner: U3
      on: [user_switch, logout, conversation_clear, session_expiry, paired_pending_cancelled, paired_pending_invalidated, paired_pending_expired, paired_pending_consumed]
      idempotent: true
    invalidate_ticket_cursors:
      on: [user_switch, logout, conversation_clear, session_expiry]
      idempotent: true
    clear_presentation_history:
      on: [user_switch, logout, conversation_clear]
      idempotent: true
  ordering:
    chat: [restore_current_session, capture_current_turn_evidence, create_request_capability, acquire_conversation_lock, run_agent, correlate_persisted_assistant_message, map_presentation, commit_presentation_metadata, release_lock, return_response]
    user_switch: [prepare_new_identity, invalidate_pending, invalidate_cursors, clear_presentation_history, clear_old_SDK_history, commit_new_session]
    logout: [invalidate_pending, invalidate_cursors, clear_presentation_history, clear_SDK_history, commit_session_delete]
    conversation_clear: [invalidate_pending, invalidate_cursors, clear_presentation_history, clear_SDK_history]

verification_owned_by_u4:
  required_contract_tests:
    - exact_three_tool_names
    - duplicate_registration_fails_closed
    - capability_is_not_serializable_or_model_visible
    - lifecycle_order_is_atomic_and_idempotent
    - create_ledger_survives_revocable_state_cleanup
    - cursor_filter_identity_and_lifecycle_binding
    - cursor_issue_resolve_exact_query_round_trip_and_hash_tamper_rejection
    - pending_create_and_update_variant_repository_round_trip
    - update_pending_atomic_replacement_preserves_old_on_failure
    - update_execution_staged_active_retired_round_trip_and_server_only_field_non_exposure
    - update_execution_activation_crash_recovery_and_tamper_rejection
    - update_execution_lifecycle_and_orphan_cleanup
    - concurrent_update_confirm_and_revise_has_one_authorized_winner
    - presentation_history_restart_restore_and_text_fallback
    - presentation_correlation_rejects_sequence_or_hash_mismatch
```

### C-03A — Model-to-Function-Tool Contract

세 도구는 아래 V1 입력·결과만 모델에 노출한다. `pending_ref`는 비밀이 아닌 불투명 상관 ID이며 권한 증명이 아니다. 서버는 repository binding과 현재 요청 범위 capability를 모두 검증하므로 다른 사용자·세션·대화에서 이 값을 재사용할 수 없다.

등록·수정 review는 사용자에게 `확인`, `수정`, `취소`를 명시적으로 안내한다. `confirm` 실행은 서버가 보존한 **현재 raw 사용자 turn**을 NFKC 정규화하고 양끝 공백과 대소문자를 정리한 결과가 review에서 제시한 독립 명령 `확인` 또는 `confirm`과 정확히 일치할 때만 허용한다. tool argument가 confirmation boolean이나 사용자 문장을 주장하는 방식은 인정하지 않는다. 추가 문구·변경값·모호한 긍정은 실행하지 않고 `needs_explicit_confirmation`을 반환한다. 수정값이 포함된 turn은 `revise`, 취소 명령은 `cancel` 경로만 사용할 수 있다.

```yaml
schema: aidlc.shared/v1
name: AgentFunctionToolsV1
version: 1
contract_definitions:
  AgentFunctionToolsV1: {defined_by: tools_and_types_in_this_block}
model_visible_secret_fields: []

tools:
  ticket_read:
    plugin: TicketReadPluginV1
    owner: U1
    input: TicketReadToolInputV1
    result: TicketReadToolResultV1
  ticket_write:
    plugin: TicketWritePluginV1
    owner: U2
    input: TicketWriteToolInputV1
    result: TicketMutationToolResultV1
  ticket_update:
    plugin: TicketUpdatePluginV1
    owner: U3
    input: TicketUpdateToolInputV1
    result: TicketMutationToolResultV1

plugins:
  TicketReadPluginV1:
    provides: [function_tool_factory, read_presentation_mapper]
    registers_via: RegistryV1
  TicketWritePluginV1:
    provides: [function_tool_factory, create_presentation_mapper]
    registers_via: RegistryV1
  TicketUpdatePluginV1:
    provides: [function_tool_factory, update_presentation_mapper]
    registers_via: RegistryV1

types:
  TicketReadToolInputV1:
    additional_properties: false
    optional:
      ticket_id: opaque_string
      q: {type: string, max_length: 200}
      status: {type: array, items: [received, assigned, investigating, pending, monitoring, resolved, closed, cancelled], repeat_query_parameter: true}
      priority: {type: array, items: [P1, P2, P3, P4], repeat_query_parameter: true}
      service_id: string
      component_id: integer
      model: string
      assignment_group_id: integer
      assignee: string
      requester: string
      classification: {enum: [standard, restricted]}
      is_major: boolean
      created_from: timezone_datetime
      created_to: timezone_datetime
      updated_from: timezone_datetime
      sort: {enum: [-created_at, -updated_at, priority], default: -created_at}
      limit: {type: integer, minimum: 1, maximum: 100, default: 20}
      continuation_ref: opaque_non_secret_reference
    mode_rule:
      ticket_id_present: detail_and_all_list_fields_forbidden
      continuation_ref_present: all_ticket_id_filter_sort_and_limit_fields_forbidden_and_server_binding_restored
      ticket_id_and_continuation_ref_absent: first_list_or_search_page
      raw_upstream_cursor: never_model_visible_or_accepted

  TicketReadToolResultV1:
    additional_properties: false
    required: [version, state, mode, untrusted_data]
    fields:
      version: {const: 1}
      state: {enum: [succeeded, empty, failed]}
      mode: {enum: [list, detail]}
      untrusted_data: {const: true}
      items: {type: array, items: SafeTicketSummaryV1, optional: true}
      detail: {type: SafeTicketDetailV1, optional: true}
      page: {type: SafePageV1, optional: true}
      error: {type: SafeErrorV1, optional: true}
    invariants:
      - list_success_has_items_and_page_only
      - detail_success_has_detail_only
      - empty_is_not_failure
      - not_found_does_not_distinguish_missing_from_invisible
      - external_text_is_data_never_instruction

  SafeTicketSummaryV1:
    additional_properties: false
    required: [id, title, status, priority, service, created_at, updated_at]
    fields:
      id: {type: string}
      title: {type: string, trust: itsm_untrusted}
      status: {type: string, enum: [received, assigned, investigating, pending, monitoring, resolved, closed, cancelled], source: server_allowlist}
      priority: {type: string, enum: [P1, P2, P3, P4]}
      service: {type: string, trust: itsm_untrusted}
      created_at: {type: utc_datetime}
      updated_at: {type: utc_datetime}
    forbidden: [description, authorization, raw_headers, raw_problem_detail]

  SafePageV1:
    additional_properties: false
    required: [limit, has_more]
    fields:
      limit: {type: integer, minimum: 1, maximum: 100}
      has_more: {type: boolean}
      continuation_ref: {type: opaque_non_secret_reference, optional: true}
    forbidden: [upstream_cursor]

  OccurrenceTimeInputV1:
    additional_properties: false
    one_of:
      - {kind: timestamp, requires: [value]}
      - {kind: now, forbids: [value]}
    fields:
      kind: {enum: [timestamp, now]}
      value: {type: timezone_datetime, optional: true}
    normalization:
      timestamp: convert_to_UTC
      now: capture_server_clock_once_during_prepare_and_freeze_in_review_and_canonical_body

  TicketWriteDraftV1:
    additional_properties: false
    required: [title, description, service, impact_level, urgency, impact_note, occurred_at]
    optional: [component, model, classification]
    fields:
      title: {type: string, min_length: 1, max_length: 200}
      description: {type: string, min_length: 1, max_length: 5000}
      service: {type: CatalogSelectorV1}
      component: {type: CatalogSelectorV1, optional: true}
      model: {type: CatalogSelectorV1, optional: true}
      impact_level: {enum: [extensive, significant, moderate, minor]}
      urgency: {enum: [critical, high, medium, low]}
      impact_note: {type: string, min_length: 1, max_length: 1000}
      occurred_at: {type: OccurrenceTimeInputV1}
      classification: {enum: [standard, restricted], default: standard, optional: true}
    resolution_output: TicketCreateInV1

  SafeReviewFieldV1:
    additional_properties: false
    required: [key, label_key, before, after]
    fields:
      key: {type: string, source: server_allowlist}
      label_key: {type: string, source: server_allowlist}
      before: {type: [string, number, boolean, 'null'], trust: itsm_untrusted_or_server_value}
      after: {type: [string, number, boolean, 'null'], trust: user_value_after_validation}

  SafeMutationReviewV1:
    additional_properties: false
    required: [operation, normalized_payload_hash, fields, choices]
    fields:
      operation: {enum: [create, update]}
      ticket_id: {type: string, optional: true}
      base_version: {type: integer, optional: true}
      normalized_payload_hash: {type: sha256}
      fields: {type: array, items: SafeReviewFieldV1}
      choices: {type: array, exact_items: [확인, 수정, 취소], source: server_allowlist}

  SafeMutationResultV1:
    additional_properties: false
    required: [operation, ticket_id]
    fields:
      operation: {enum: [create, update]}
      ticket_id: {type: string}
      new_version: {type: integer, minimum: 1, optional: true}
      applied_changes: {type: array, items: SafeReviewFieldV1, optional: true}
      idempotent_replayed: {type: boolean, optional: true}
      request_id: {type: string, optional: true}
    success_rules:
      create: ticket_id_and_created_or_idempotent_replayed_evidence_required
      update: applied_changes_and_new_version_required

  TicketWriteToolInputV1:
    additional_properties: false
    required: [action]
    fields:
      action: {enum: [prepare, confirm, revise, cancel]}
      draft: {type: TicketWriteDraftV1, optional: true}
      pending_ref: {type: opaque_non_secret_reference, optional: true}
    action_rules:
      prepare: {requires: [draft], forbids: [pending_ref]}
      revise: {requires: [pending_ref, draft], meaning: full_replacement_draft_and_new_review}
      confirm: {requires: [pending_ref], forbids: [draft], requires_server_current_turn_decision: explicit_confirm}
      cancel: {requires: [pending_ref], forbids: [draft], requires_server_current_turn_decision: explicit_cancel}

  TicketUpdateToolInputV1:
    additional_properties: false
    required: [action, ticket_id]
    fields:
      action: {enum: [prepare, confirm, revise, cancel]}
      ticket_id: {type: opaque_string}
      patch: {type: TicketPatchInV1, optional: true}
      pending_ref: {type: opaque_non_secret_reference, optional: true}
    action_rules:
      prepare: {requires: [patch], forbids: [pending_ref]}
      revise: {requires: [pending_ref, patch], meaning: full_replacement_patch_and_new_review}
      confirm: {requires: [pending_ref], forbids: [patch], requires_server_current_turn_decision: explicit_confirm}
      cancel: {requires: [pending_ref], forbids: [patch], requires_server_current_turn_decision: explicit_cancel}

  CurrentTurnEvidenceV1:
    model_visible: false
    source: raw_current_http_chat_message
    scope: current_HTTP_chat_request_only
    required: [turn_id, user_id, session_id, conversation_id, raw_message_sha256, decision]
    forbidden: [credential, authorization]
    normalization: [unicode_nfkc, trim_outer_whitespace, casefold]
    decisions:
      explicit_confirm: {exact_values: [확인, confirm]}
      explicit_cancel: {exact_values: [취소, cancel]}
      revise_or_ambiguous: all_other_values

  TicketMutationToolResultV1:
    additional_properties: false
    required: [version, operation, state]
    fields:
      version: {const: 1}
      operation: {enum: [create, update]}
      state: {enum: [review_required, needs_explicit_confirmation, revised, cancelled, succeeded, invalidated, conflict, ambiguous, failed]}
      pending_ref: {type: opaque_non_secret_reference, optional: true}
      review: {type: SafeMutationReviewV1, optional: true}
      data: {type: SafeMutationResultV1, optional: true, untrusted_external_text: true}
      error: {type: SafeErrorV1, optional: true}
    state_rules:
      review_required: {requires: [pending_ref, review], transport_mutation_calls: 0}
      needs_explicit_confirmation: {requires: [pending_ref, review], transport_mutation_calls: 0}
      revised: {requires: [pending_ref, review], old_pending_ref_invalidated: true, transport_mutation_calls: 0}
      cancelled: {pending_invalidated: true, transport_mutation_calls: 0}
      succeeded: {requires: [data], success_evidence_required: true}
      ambiguous: {reported_as_success: false}

confirmation_bridge:
  create_prepare_or_revise:
    - validate_and_normalize_business_payload
    - serialize_exact_canonical_request_bytes_and_hash
    - persist_U2_TicketCreateAttempt_as_prepared_with_attempt_count_0_and_one_unpredictable_idempotency_key
    - only_after_ledger_commit_publish_U1_pending_create_review
    - return_full_review_and_pending_ref
  create_confirm:
    - obtain_CurrentTurnEvidenceV1_from_runner_context_not_tool_arguments
    - verify_server_current_turn_is_explicit_confirm
    - verify_pending_ref_binding_for_user_session_conversation_operation_and_payload
    - consume_U1_pending_once_and_receive_ConsumedMutationEvidenceV1
    - idempotently_bind_mutation_id_and_confirmed_at_to_the_same_U2_attempt
    - monotonically_extend_retained_until_to_at_least_confirmed_at_plus_24_hours
    - acquire_U2_CAS_claim_only_when_evidence_is_bound_and_attempt_count_is_less_than_2
    - increment_global_attempt_count_when_POST_starts
    - only_then_call_POST_with_the_ledger_stored_key_and_exact_bytes
  create_crash_before_evidence_binding:
    - preserve_the_existing_U2_attempt_key_and_bytes
    - publish_a_new_U1_pending_review_for_the_same_attempt
    - require_new_explicit_confirmation
    - never_POST_from_the_unbound_consumption
  update_prepare_or_revise:
    - validate_and_normalize_patch_and_base_version
    - persist_U3_PendingUpdateExecutionV1_as_staged_with_canonical_patch_and_validated_IfMatchVersion
    - call_U1_replace_update_pending_with_expected_old_mutation_for_revise_or_null_for_prepare
    - promote_the_exact_U3_execution_row_to_active_by_expected_state_CAS
    - return_full_review_and_pending_ref
  update_publication_failure:
    - U1_replacement_rejection_preserves_the_old_pending_and_leaves_the_new_staged_row_non_authorizing
    - cleanup_or_retire_the_new_staged_row_idempotently
    - never_PATCH
  update_activation_crash:
    - compare_U1_and_U3_mutation_actor_ticket_patch_hash_and_base_version
    - promote_to_active_only_on_exact_match
    - otherwise_fail_closed_and_retire_the_orphan
  update_confirm:
    - obtain_CurrentTurnEvidenceV1_from_runner_context_not_tool_arguments
    - verify_server_current_turn_is_explicit_confirm
    - verify_pending_ref_binding_for_user_session_conversation_operation_payload_target_and_version
    - load_active_or_exactly_recoverable_U3_execution_and_recompute_canonical_patch_hash
    - atomically_mark_confirmed_then_consume_once
    - only_then_call_PATCH_with_stored_canonical_patch_and_validated_IfMatchVersion
    - if_and_only_if_first_PATCH_returns_authoritative_no_apply_token_expired_then_durably_reserve_U3_refresh_once
    - call_U1_UpdateCredentialRefreshPortV1_once_and_never_reset_or_reinvoke_the_reservation
    - after_success_call_the_second_and_final_PATCH_with_identical_patch_and_IfMatchVersion
  cancel:
    - verify_binding
    - invalidate_pending
    - never_call_POST_or_PATCH
```

## C-04 — U2 Ticket Write to U4 Release Assurance

U2가 U4에 제공하는 것은 create plugin, durable attempt ledger contract, presentation mapper와 자동화 검증 evidence다. 성공은 티켓 ID가 실제 응답 또는 `Idempotent-Replayed` 응답으로 확인된 경우에만 표현한다.

```yaml
schema: aidlc.shared/v1
name: U2ToU4TicketWrite
version: 1
contract_definitions:
  TicketCreateAttemptV1: {defined_by: ledger}

plugin:
  contract_version: 1
  tool_name: ticket_write
  input_schema: TicketWriteToolInputV1
  result_schema: TicketMutationToolResultV1
  confirmation_required_before_transport: true
  presentation_kinds: [ticket_input, ticket_review, ticket_success, ticket_auth_error, ticket_rate_limited, ticket_ambiguous, ticket_unavailable]

ledger:
  name: TicketCreateAttemptV1
  owner: U2
  durable: true
  minimum_retention_hours: 24
  ledger_first_prepare: required_before_U1_pending_review_is_published
  write_before_first_http_attempt: true
  storage:
    migration_owner: U2
    namespace: ticket_tools_create_v1
    database: existing_server_session_SQLite_database
    table: ticket_create_attempts
    must_not_edit: [ticket_tools_state_v1, ticket_tools_history_v1]
  fields:
    required:
      - create_attempt_id
      - user_id
      - originating_session_id
      - originating_conversation_id
      - normalized_payload_hash
      - canonical_request_bytes
      - serialization_version
      - request_bytes_hash
      - idempotency_key
      - attempt_count
      - status
      - created_at
      - retained_until
    nullable_until_confirmation_or_claim: [confirmed_mutation_id, confirmed_at, claim_id, claim_deadline_at]
    optional: [last_outcome, result_ticket_id, refresh_reservation_id, refresh_used_at, refresh_state, refresh_base_credential_generation, refresh_committed_credential_generation, refresh_committed_at]
    forbidden: [credential, authorization, client_secret, openai_api_key]
  actor_binding:
    user_id: immutable
    originating_session_id: immutable_historical_identifier_not_live_reference
    originating_conversation_id: immutable_historical_identifier_not_live_reference
    lifecycle_cleanup: preserve_attempt_row_and_revoke_only_U1_pending_confirmation
  confirmation_evidence:
    source: U1.PendingMutationRepositoryV1.consume_once
    required_fields: [confirmed_mutation_id, confirmed_at]
    bind_operation: idempotent_compare_and_set_on_same_create_attempt
    authorization_effect: evidence_alone_does_not_authorize_POST
    crash_before_bind: reuse_same_attempt_key_and_bytes_but_publish_new_review_and_require_new_confirmation
    retention_effect: monotonically_extend_retained_until_to_at_least_confirmed_at_plus_24_hours
  status: [prepared, in_flight, retryable_after_reconcile, retryable_no_apply, completed, terminal_failure, ambiguous]
  claim_contract:
    owner: U2
    mechanism: compare_and_set
    required_before_POST: [confirmed_mutation_id, confirmed_at, attempt_count_less_than_2]
    writes: [unique_claim_id, claim_deadline_at, status_in_flight]
    increments_attempt_count: when_POST_starts
    active_claim_takeover_before_deadline: forbidden
    stale_claim: reconcile_result_before_any_new_claim
  retry_invariants:
    max_total_attempts: 2
    one_global_attempt_count_for_all_retryable_states: true
    same_idempotency_key: required
    byte_identical_body: required
    new_key_for_same_confirmed_intent: forbidden
    status_429_wait_or_retry: forbidden
    retryable_no_apply:
      entry: token_expired_401_only_when_authoritative_contract_guarantees_no_apply
      credential_refresh: allowed_once_through_CredentialRefreshPortV1_after_durable_reservation_use
      separate_retry_budget: forbidden
    retryable_after_reconcile:
      entry:
        - result_lookup_confirms_not_created
        - result_lookup_fails_or_cannot_determine_existence_and_attempt_count_is_less_than_2
      next_POST: requires_new_CAS_claim_with_same_key_and_bytes
    second_ambiguous_result: terminal_ambiguous
    any_state_when_attempt_count_is_2: no_further_POST

reconciliation:
  runs_before_retry_after_stale_claim_or_ambiguous_result: true
  ticket_confirmed: mark_completed_without_new_POST
  ticket_confirmed_absent: mark_retryable_after_reconcile_when_attempt_count_less_than_2
  lookup_failed_or_ambiguous: mark_retryable_after_reconcile_when_attempt_count_less_than_2
  after_budget_exhausted_without_confirmed_ticket: mark_terminal_ambiguous

success_contract:
  result_ticket_id: required
  evidence_any_of: [created_response, idempotent_replayed_response]
  ambiguous_is_success: false

verification_manifest:
  transport: httpx.MockTransport
  model: FakeModel
  real_network_calls: 0
  required_cases: [validation, catalog_id_or_name_resolution, explicit_now_freezing, ledger_first_review_publication, confirmation_from_server_current_turn, consume_evidence_binding, crash_before_evidence_binding_requires_reconfirmation, cancellation, claim_identity_and_deadline, active_claim_non_takeover, stale_claim_reconciliation, retryable_after_reconcile, retryable_no_apply, proactive_expiry_refresh_before_first_POST, durable_refresh_reservation, refresh_port_atomic_commit, refresh_generation_recovery_after_commit, refresh_crash_without_second_invocation, byte_identical_retry, shared_total_attempt_ceiling, idempotent_replay, second_ambiguous_result_is_terminal, lifecycle_preserves_historical_actor_binding, retention, secret_canary]
```

## C-05 — U3 Ticket Update to U4 Release Assurance

U3는 update plugin과 optimistic-lock evidence를 제공한다. PATCH 전송 결과가 불명확하거나 version이 충돌하면 자동 PATCH 재전송 없이 최신 상세를 조회하고 필요한 경우 새 확인으로 돌아간다.

```yaml
schema: aidlc.shared/v1
name: U3ToU4TicketUpdate
version: 1

plugin:
  contract_version: 1
  tool_name: ticket_update
  input_schema: TicketUpdateToolInputV1
  result_schema: TicketMutationToolResultV1
  confirmation_required_before_transport: true
  presentation_kinds: [ticket_input, ticket_review, ticket_success, ticket_auth_error, ticket_conflict, ticket_rate_limited, ticket_ambiguous, ticket_unavailable]

optimistic_lock:
  detail_read_before_review: required
  confirmed_base_version: required
  patch_header: If-Match
  no_op_patch_request: forbidden
  status_412_or_428:
    patch_retries: 0
    next_steps: [read_latest_detail, compute_diff, require_new_confirmation_if_still_needed]
  ambiguous_transport_result:
    patch_retries: 0
    next_steps: [read_latest_detail, compare_expected_changes, require_new_confirmation_if_unresolved]

success_contract:
  required: [ticket_id, applied_changes, new_version]
  version_must_advance: true
  permission_decision_owner: ITSM_API_v2

execution_store:
  contract_type: PendingUpdateExecutionV1
  owner: U3
  namespace: ticket_tools_update_v1
  table: pending_update_executions
  database: existing_server_session_SQLite_database
  authority_requires_all:
    - exact_matching_active_execution_row
    - exact_matching_U1_pending_update_binding
    - current_turn_explicit_confirmation
    - U1_consume_once_evidence
  cleanup: idempotent_on_access_startup_and_lifecycle

publication_contract:
  U1_operation: PendingMutationRepositoryV1.replace_update_pending
  order: [stage_U3_execution, atomically_replace_U1_pending, atomically_retire_exact_old_U3_execution_and_promote_new_active]
  old_review_preserved_when: validation_or_U1_replacement_fails
  crash_after_U1_commit: exact_binding_recovery_only
  broad_selector_invalidation: forbidden

update_refresh_contract:
  U1_port: UpdateCredentialRefreshPortV1.refresh_update_capability_once
  U3_evidence: UpdateCredentialRefreshReservationV1_embedded_in_PendingUpdateExecutionV1
  entry: first_PATCH_token_expired_401_only_when_authoritative_contract_guarantees_no_apply
  durable_order: reserve_once_before_port_call
  invocation_limit: one_per_update_execution
  recovery_after_session_commit: compare_server_only_credential_generation_and_commit_without_second_port_call
  second_PATCH: identical_patch_and_IfMatchVersion_and_final_attempt
  reservation_reset: forbidden

verification_manifest:
  transport: httpx.MockTransport
  model: FakeModel
  real_network_calls: 0
  required_cases: [allowed_fields, forbidden_fields, omit_vs_null, no_op, confirmation_from_server_current_turn, confirmation_binding, exact_quoted_if_match_from_validated_etag_and_version, invalid_etag_forbids_patch, conflict, ambiguous_result, total_patch_attempt_ceiling, durable_update_refresh_reservation, refresh_port_atomic_commit, refresh_generation_recovery_without_second_invocation, permission_delegation, execution_store_round_trip, server_only_field_non_exposure, atomic_replacement_rollback, exact_old_row_invalidation, single_active_execution_per_actor_scope, concurrent_confirm_revise, staged_orphan_cleanup, activation_crash_recovery, lifecycle_terminal_cleanup, response_loss_locator_isolation, tamper_rejection, secret_canary]
```

## C-06 — Existing Chat API to Browser

이 계약은 기존 endpoint와 필수 필드·상태 의미를 유지한다. `presentation`은 선택적이며 구형 client와 구형 history row는 이를 무시하거나 일반 텍스트로 fallback할 수 있다. 저장 이력은 같은 metadata를 복원하되 렌더링 시 `announce=false`로 처리한다.

```yaml
openapi: 3.1.0
info:
  title: ITSM Assistant Existing Chat Surface
  version: 1.1.0
  description: Existing v1-compatible surface with optional TicketPresentationV1 metadata.
paths:
  /api/agent/chat:
    post:
      operationId: agentChat
      requestBody:
        required: true
        content:
          application/json:
            schema: {$ref: '#/components/schemas/AgentChatIn'}
      responses:
        '200':
          description: Existing reply and session-derived context, plus optional presentation.
          content:
            application/json:
              schema: {$ref: '#/components/schemas/AgentChatOut'}
        '401': {description: Existing session authentication failure semantics unchanged.}
        '422': {description: Existing input validation semantics unchanged.}
        '5XX': {description: Existing safe application error envelope; no provider secrets or raw exceptions.}
  /api/agent/messages:
    get:
      operationId: agentMessages
      responses:
        '200':
          description: Existing conversation history with optional presentation on assistant messages.
          content:
            application/json:
              schema: {$ref: '#/components/schemas/AgentHistoryOut'}
    delete:
      operationId: clearAgentMessages
      responses:
        '204': {description: Pending mutation invalidated and conversation history cleared.}

components:
  schemas:
    AgentChatIn:
      type: object
      additionalProperties: false
      required: [message]
      properties:
        message: {type: string, minLength: 1, maxLength: 4000}
    AgentContextOut:
      type: object
      additionalProperties: false
      required: [user_id, username, role]
      properties:
        user_id: {type: integer}
        username: {type: string}
        role: {type: string}
    AgentChatOut:
      type: object
      additionalProperties: false
      required: [reply, context]
      properties:
        reply: {type: string, description: Existing text fallback remains required.}
        context: {$ref: '#/components/schemas/AgentContextOut'}
        presentation: {$ref: '#/components/schemas/TicketPresentationV1'}
    AgentHistoryOut:
      type: object
      additionalProperties: false
      required: [messages]
      properties:
        messages:
          type: array
          items: {$ref: '#/components/schemas/AgentMessageOut'}
    AgentMessageOut:
      type: object
      additionalProperties: false
      required: [role, text]
      properties:
        role: {type: string, enum: [user, assistant]}
        text: {type: string}
        presentation: {$ref: '#/components/schemas/TicketPresentationV1'}
    TicketPresentationV1:
      type: object
      additionalProperties: false
      required: [version, kind, blocks]
      properties:
        version: {type: integer, const: 1}
        kind:
          type: string
          enum: [ticket_progress, ticket_list, ticket_detail, ticket_input, ticket_review, ticket_success, ticket_unavailable, ticket_auth_error, ticket_conflict, ticket_rate_limited, ticket_ambiguous]
        blocks:
          type: array
          items:
            oneOf:
              - {$ref: '#/components/schemas/ParagraphBlockV1'}
              - {$ref: '#/components/schemas/FieldsBlockV1'}
              - {$ref: '#/components/schemas/ItemsBlockV1'}
              - {$ref: '#/components/schemas/ActionsBlockV1'}
    TextValueV1:
      type: object
      additionalProperties: false
      required: [text, origin]
      properties:
        text: {type: string}
        origin: {type: string, enum: [server_allowlist, itsm_untrusted]}
    FieldV1:
      type: object
      additionalProperties: false
      required: [key, label, value]
      properties:
        key: {type: string}
        label: {type: string, description: Server allowlisted label only.}
        value: {$ref: '#/components/schemas/TextValueV1'}
    ParagraphBlockV1:
      type: object
      additionalProperties: false
      required: [type, text]
      properties:
        type: {const: paragraph}
        text: {$ref: '#/components/schemas/TextValueV1'}
    FieldsBlockV1:
      type: object
      additionalProperties: false
      required: [type, fields]
      properties:
        type: {const: fields}
        fields: {type: array, items: {$ref: '#/components/schemas/FieldV1'}}
    ItemsBlockV1:
      type: object
      additionalProperties: false
      required: [type, items]
      properties:
        type: {const: items}
        items:
          type: array
          items: {type: array, items: {$ref: '#/components/schemas/FieldV1'}}
    ActionsBlockV1:
      type: object
      additionalProperties: false
      required: [type, actions]
      properties:
        type: {const: actions}
        actions:
          type: array
          items:
            type: object
            additionalProperties: false
            required: [action, label]
            properties:
              action: {type: string, enum: [provide_input, confirm, revise, cancel, retry_later, start_over]}
              label: {type: string, description: Server allowlisted label only.}

x-rendering-contract:
  kind_block_type_and_labels: server_allowlist_only
  business_values: insert_as_text_nodes_never_html
  unknown_version_kind_or_block: render_existing_reply_or_text_fallback
  live_semantics: derived_from_local_PRESENTATION_MAP_not_payload_text
  restored_history_announce: false
x-history-presentation-contract:
  repository: U1.PresentationHistoryRepositoryV1
  correlation: [conversation_id, assistant_sequence, assistant_text_sha256]
  write_before_chat_response: required_for_presentation_field
  rows_without_metadata: valid_text_only_fallback
  restart_restore: required
  clear_order: [clear_presentation_companion_rows, clear_SDK_session_items]
```

## C-07 — ITSM API v2 Outbound Profile

`docs/itsm/openapi.json`과 `docs/itsm/integration-guide.md`가 전체 원본 계약이다. 아래는 이번 기능이 소비하는 operation과 Assistant 측 추가 안전 정책을 고정한 좁은 profile이다. 티켓 operation은 항상 현재 서버 세션 사용자의 위임 token을 사용하며 ITSM이 권한과 가시성을 판단한다.

```yaml
openapi: 3.1.0
info:
  title: ITSM API v2 - Assistant Ticket Tool Consumption Profile
  version: 2.0.0
  x-authoritative-sources:
    - docs/itsm/openapi.json
    - docs/itsm/integration-guide.md
paths:
  /api/v2/auth/token:
    post:
      operationId: exchangeDelegatedToken
      security: []
      x-consumer: U1.IdentitySession
      requestBody:
        required: true
        content:
          application/json:
            schema: {$ref: '#/components/schemas/TokenExchangeIn'}
      x-policy:
        grant_type: token_exchange
        subject: current_server_session_user_only
        expose_token_beyond_server_capability: false
  /api/v2/catalog/services:
    get:
      operationId: listCatalogServices
      security:
        - serviceBearer: []
        - delegatedBearer: []
      x-consumer: U2.catalog_resolution
      x-token-policy: service_or_delegated_token_per_existing_gateway_contract
  /api/v2/catalog/models:
    get:
      operationId: listCatalogModels
      security:
        - serviceBearer: []
        - delegatedBearer: []
      x-consumer: U2.catalog_resolution
      x-token-policy: service_or_delegated_token_per_existing_gateway_contract
  /api/v2/tickets:
    get:
      operationId: listTickets
      security:
        - delegatedBearer: []
      parameters:
        - {name: q, in: query, schema: {type: string, maxLength: 200}}
        - {name: status, in: query, schema: {type: array, items: {type: string, enum: [received, assigned, investigating, pending, monitoring, resolved, closed, cancelled]}}, explode: true}
        - {name: priority, in: query, schema: {type: array, items: {type: string, enum: [P1, P2, P3, P4]}}, explode: true}
        - {name: service_id, in: query, schema: {type: string}}
        - {name: component_id, in: query, schema: {type: integer}}
        - {name: model, in: query, schema: {type: string}}
        - {name: assignment_group_id, in: query, schema: {type: integer}}
        - {name: assignee, in: query, schema: {type: string}}
        - {name: requester, in: query, schema: {type: string}}
        - {name: classification, in: query, schema: {type: string, enum: [standard, restricted]}}
        - {name: is_major, in: query, schema: {type: boolean}}
        - {name: created_from, in: query, schema: {type: string, format: date-time}}
        - {name: created_to, in: query, schema: {type: string, format: date-time}}
        - {name: updated_from, in: query, schema: {type: string, format: date-time}}
        - {name: sort, in: query, schema: {type: string, enum: [-created_at, -updated_at, priority], default: -created_at}}
        - {name: limit, in: query, schema: {type: integer, minimum: 1, maximum: 100, default: 20}}
        - {name: cursor, in: query, schema: {type: string}}
      responses:
        '200': {description: TicketPage; project only allowlisted summary fields and page cursor.}
        '404': {description: Not expected for list; do not infer hidden data.}
        '429': {description: Return safe rate_limited result immediately with validated Retry-After.}
    post:
      operationId: createTicket
      security:
        - delegatedBearer: []
      parameters:
        - {name: Idempotency-Key, in: header, required: true, schema: {type: string}}
      requestBody:
        required: true
        content:
          application/json:
            schema: {$ref: '#/components/schemas/TicketCreateIn'}
      responses:
        '201': {description: TicketOut; Location and optional Idempotent-Replayed are allowlisted.}
        '422': {description: Safe validation/catalog/idempotency mapping only.}
        '429': {description: No automatic wait or retry.}
  /api/v2/tickets/{ticket_id}:
    parameters:
      - {name: ticket_id, in: path, required: true, schema: {type: string}}
    get:
      operationId: readTicket
      security:
        - delegatedBearer: []
      responses:
        '200':
          description: TicketOut; retain a strong quoted-decimal ETag matching body version in server context.
          headers:
            ETag:
              description: Strong entity tag whose quoted decimal value equals TicketOut.version.
              schema: {type: string, pattern: '^"[1-9][0-9]*"$'}
        '404': {description: Missing and not-visible are the same safe not_found result.}
        '429': {description: No automatic wait or retry.}
    patch:
      operationId: updateTicket
      security:
        - delegatedBearer: []
      parameters:
        - {name: If-Match, in: header, required: true, schema: {type: string}}
      requestBody:
        required: true
        content:
          application/json:
            schema: {$ref: '#/components/schemas/TicketPatchIn'}
      responses:
        '200': {description: TicketOut with applied values and incremented version.}
        '412': {description: version_conflict; never overwrite or automatically retry PATCH.}
        '428': {description: precondition_required; never automatically retry PATCH.}
        '429': {description: No automatic wait or retry.}

components:
  securitySchemes:
    delegatedBearer:
      type: http
      scheme: bearer
      bearerFormat: opaque
      description: Current server-session user's delegated token; required for every ticket operation.
      x-token-kind: delegated_user
    serviceBearer:
      type: http
      scheme: bearer
      bearerFormat: opaque
      description: Existing server-only service token; allowed only for catalog/directory operations, never ticket operations.
      x-token-kind: service
  schemas:
    TokenExchangeIn:
      type: object
      additionalProperties: false
      required: [grant_type, client_id, client_secret, subject]
      properties:
        grant_type: {type: string, const: token_exchange}
        client_id: {type: string, writeOnly: true}
        client_secret: {type: string, writeOnly: true}
        subject: {type: string, description: Derived from the current server session only.}
      x-model-visible: false
    TicketCreateIn:
      type: object
      additionalProperties: false
      required: [title, description, service_id, impact_level, urgency, impact_note, occurred_at]
      properties:
        title: {type: string, minLength: 1, maxLength: 200}
        description: {type: string, minLength: 1, maxLength: 5000}
        service_id: {type: string, minLength: 1, maxLength: 50}
        component_id: {type: [integer, 'null']}
        model: {type: [string, 'null']}
        impact_level: {type: string, enum: [extensive, significant, moderate, minor]}
        urgency: {type: string, enum: [critical, high, medium, low]}
        impact_note: {type: string, minLength: 1, maxLength: 1000}
        occurred_at: {type: string, format: date-time, description: Timezone required.}
        classification: {type: string, enum: [standard, restricted], default: standard}
    TicketPatchIn:
      type: object
      additionalProperties: false
      properties:
        title: {type: [string, 'null'], minLength: 1, maxLength: 200}
        description: {type: [string, 'null'], minLength: 1, maxLength: 5000}
        component_id: {type: [integer, 'null']}
        model: {type: [string, 'null'], maxLength: 50}
        impact_level: {type: [string, 'null'], enum: [extensive, significant, moderate, minor, null]}
        urgency: {type: [string, 'null'], enum: [critical, high, medium, low, null]}
        impact_note: {type: [string, 'null'], minLength: 1, maxLength: 1000}
        is_major: {type: [boolean, 'null']}
      x-patch-semantics:
        omitted_field: leave_unchanged
        explicit_null: clear_value_as_allowed_by_authoritative_contract
        empty_or_no_actual_diff: reject_locally_without_PATCH

x-assistant-transport-policy:
  timeout_per_attempt: ITSM_TIMEOUT_SECONDS
  read:
    max_total_attempts: 2
    retry_delay_seconds: 0.25
    retry_only_on: [timeout, connection_or_transport_error, 500, 502, 503, 504]
    token_refresh_recall_counts_toward_attempt_limit: true
    maximum_elapsed: 2 * ITSM_TIMEOUT_SECONDS + 0.25
  create:
    max_total_attempts: 2
    ledger_first_prepare_before_review: true
    confirmation_evidence_and_CAS_claim_required_before_each_POST: true
    global_attempt_count_incremented_when_POST_starts: true
    retry_requires_same_idempotency_key_and_byte_identical_body: true
    result_reconciliation_precedes_retry: true
    final_retry_after_lookup_failure_or_ambiguity: allowed_only_when_attempt_count_less_than_2
    second_ambiguous_result: terminal_ambiguous
    ambiguous_result_is_never_reported_as_success: true
  update:
    automatic_patch_retries: 0
    ambiguous_result_requires_latest_read_and_possible_new_confirmation: true
  all_operations:
    status_429: return_immediately_without_sleep_or_retry
    returned_headers_allowlist: [ETag, X-Request-ID, Retry-After, Idempotent-Replayed, Location]
    raw_problem_detail_exception_and_headers: never_cross_gateway
```

## Cross-Contract Error, Timeout, and Retry Rules

| Operation | Gateway behaviour | Policy owner | Total HTTP attempt ceiling | Retry condition | Non-retry behaviour |
|---|---|---|---:|---|---|
| Ticket read/list | 호출당 정확히 1회, 시도별 `ITSM_TIMEOUT_SECONDS` | `TicketOperationPolicyV1` | 최초 포함 최대 2회 | 첫 timeout·transport 또는 500/502/503/504 뒤 250ms | 429 즉시 반환; 404는 부재/비가시성 구분 금지 |
| Ticket create | U2 증거 결합·CAS claim 뒤 호출당 정확히 1회, ledger의 동일 bytes 전송 | `TicketOperationPolicyV1` + U2 `TicketCreateAttemptV1` | 최초 포함 최대 2회 | 결과 조정 뒤 `attempt_count < 2`일 때 저장된 동일 key·동일 canonical bytes만; 조회 실패·모호성도 마지막 1회 허용 | 두 번째 불명확 결과는 terminal `ambiguous`; 429 즉시 반환 |
| Ticket update | 호출당 정확히 1회 | `TicketOperationPolicyV1` | PATCH 자동 재시도 0회 | 권한 있는 미적용 보장 401을 제외하고 없음 | 412/428·불명확 결과는 최신 상세 조회 후 필요 시 새 확인 |

`ItsmGateway`의 공개 메서드 한 번은 HTTP 시도 정확히 한 번이며 자체 retry·sleep·token refresh 판단을 하지 않는다. `TicketOperations`의 `TicketOperationPolicyV1`만 operation별 재호출과 사용자 다음 행동을 결정한다. 등록은 U2 ledger의 한 전역 `attempt_count`를 사용하며 모든 POST CAS claim이 count < 2를 요구하고 POST 시작 시 증가시킨다. token refresh 뒤의 `retryable_no_apply`, 결과 조정 뒤의 `retryable_after_reconcile`, 조회 실패·모호성에서 허용된 마지막 재시도도 이 예산을 공유한다. tool wrapper와 presentation mapper는 독자적으로 재시도하거나 원본 오류를 해석하지 않는다.

## Contract Ownership and Change Rules

- U1은 `TicketRequestCapability`, `SafeErrorV1`, 공통 `PendingTicketMutationV1`과 명시적 `PendingCreateMutationV1`·`PendingUpdateMutationV1` variant, repository·invalidation, `ItsmGatewayV1`, tool registry와 `TicketPresentationV1` envelope를 소유한다.
- U1의 논리 공통 저장 계약 `ticket_tools_common_v1`은 물리적으로 Server Session DB의 `ticket_tools_state_v1`과 Agents SDK history DB의 `ticket_tools_history_v1` migration namespace로 분리된다. U1만 두 namespace를 수정한다.
- U2는 `TicketCreateInV1`, create binding·plugin·presentation mapper, ledger-first `TicketCreateAttemptV1`, confirmation evidence 결합, claim identity·deadline, 조정·재시도 상태와 `ticket_tools_create_v1` migration, create contract tests를 소유한다. U1의 두 migration namespace나 U3 파일을 수정하지 않으며 cross-owner transaction port를 추가하지 않는다.
- U3는 `TicketPatchInV1`, update binding·plugin·presentation mapper, version/`If-Match` 처리, `PendingUpdateExecutionV1`, `ticket_tools_update_v1` migration과 update contract tests를 소유한다. U1의 두 migration namespace나 U2 파일을 수정하지 않는다. U1은 자기 confirmation table 안의 `replace_update_pending` transaction만 소유하며 U3 table을 쓰지 않는다.
- U4는 계약을 재정의하지 않는다. U1~U3 plugin의 최종 조립, 기존 browser 계약, lifecycle, 전체 contract/regression test와 README 일관성을 검증한다.
- C-07의 원본 schema와 HTTP 의미는 ITSM 문서가 소유한다. U1 adapter는 원본을 복사해 별도 진실 원천을 만들지 않고 필요한 profile과 안전 projection만 유지한다.
- V1에 optional field를 추가할 때 provider는 default/fallback을 정의하고 consumer는 unknown field를 무시한다. 필수 field 추가, field 제거·rename·타입 또는 의미 변경, enum 기존 값의 의미 변경은 breaking change다.
- Breaking change는 새 version, 모든 직접 consumer의 contract test 갱신, C-06이면 구형 browser fallback 검증, C-07이면 ITSM v2 원본 계약 변경 확인이 모두 끝난 뒤에만 허용한다.
- error code, retry 상한, 확인 binding, credential 가시성, 정확한 tool 이름 집합은 안전 불변식이므로 같은 version 안에서 완화할 수 없다.

## Contract Verification Matrix

| Contract | Provider test | Consumer test | Final U4 assertion |
|---|---|---|---|
| C-01 | U1 fake capability·create/update variant repository round-trip·`consume_once` evidence·single-attempt gateway·`CredentialRefreshPortV1` atomic credential-commit contract suite | U2 ledger-first create plugin, durable refresh reservation, one-call consumer against U1 fakes | 증거 결합·CAS claim 없는 POST 0회, refresh/exchange≤1, crash 후 second refresh 0, 모든 복구 원인이 공유하는 총 POST≤2, 등록 확인·멱등·비밀 canary |
| C-02 | U1 detail/version·update variant round-trip·atomic exact-old replacement rollback·single-attempt gateway·`UpdateCredentialRefreshPortV1` atomic credential-commit contract suite | U3 staged-first execution store, single-active replacement, durable refresh reservation과 update plugin against U1 fakes | 이전 review 보존, exact binding activation, refresh invocation≤1, crash 후 second refresh 0, `If-Match`·충돌·불명확 결과·허용 밖 PATCH 재전송 0회 |
| C-03 | registry·lifecycle·cursor issue/resolve·presentation-history ordering tests | U4 assembly fixture | tool 이름 정확히 3개, cursor exact-query binding과 tamper 거부, restart history 복원과 fallback |
| C-04 | U2 ledger-first·confirmation evidence·claim deadline·reconciliation 상태 전이·durable refresh reservation·plugin·mapper tests | U4 manifest consumer | 동일 key/bytes, refresh invocation≤1, crash 후 second refresh 0, 전역 attempt count≤2, 두 번째 불명확 결과 terminal, lifecycle 뒤 역사적 binding과 최소 24시간 보존 |
| C-05 | U3 plugin·mapper·optimistic-lock·execution-store round-trip·single-active locator·durable refresh reservation·crash/lifecycle cleanup·response-loss·tamper tests | U4 manifest consumer | server-only field 노출 0건, replacement failure의 이전 review 보존, concurrent winner 1개, refresh≤1, response-loss duplicate pending 0개, 허용 밖 PATCH 재전송 0회, version 증가 |
| C-06 | FastAPI response-model과 message-correlation repository tests | browser schema/fallback/accessibility tests | 기존 API·restart history·화면 회귀 0건 |
| C-07 | MockTransport request/response contract tests | U2/U3 operation policy tests | 실제 ITSM 호출 0건, 위임 token 사용 100% |

## Open Questions

| Contract | Question | Blocks |
|---|---|---|
| None | 미해결 계약 질문 없음 | None |

