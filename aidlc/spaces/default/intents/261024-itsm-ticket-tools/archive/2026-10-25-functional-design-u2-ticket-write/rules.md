# U2 Ticket Write — Business Rules

## Sources

- `inception/units-generation/unit-of-work.md` — U2 responsibilities, ownership, and verification boundary
- `inception/units-generation/unit-of-work-story-map.md` — acceptance criteria assigned to U2
- `inception/user-stories/stories.md` — US2.1 and shared US4.1/US5.1 behaviour
- `inception/requirements-analysis/requirements.md` — FR3, FR5, FR6.3, and applicable NFRs
- `inception/domain-design/components.md` — `TicketOperations`, `ItsmGateway`, session, registry, and presentation boundaries
- `inception/contract-design/contract-summary.md` — C-01, C-03A, C-04, C-06, and C-07 V1 contracts
- `construction/u1-ticket-read-skeleton/functional-design/functional-design-questions.md` — confirmed confirmation lifetime and latest-per-operation policy

## Authoritative Rule Set

The YAML block is the source of truth. Each rule is deterministic and testable without live network access.

```yaml
schema_version: 1
unit: u2-ticket-write
rules:
  - id: BR2.1
    statement: A create draft accepts only the documented ticket-create fields and field constraints.
    category: validation
    applies_to: [TicketWriteDraftV1, prepare, revise]
    trigger: A create draft is submitted.
    logic: IF every supplied key is allowlisted, required strings are present, lengths are within contract limits, and impact_level, urgency, and classification use allowed values THEN continue; ELSE reject before confirmation or outbound access.
    violation_behaviour: Return invalid_input with allowlisted field_errors, preserve the user's draft for correction, and make zero POST attempts.
    source: [FR3.1, FR3.2, NFR1]

  - id: BR2.2
    statement: Service, component, and model selectors resolve to exactly one active catalog match and component belongs to service.
    category: validation
    applies_to: [catalog_resolution, NormalizedTicketCreateV1]
    trigger: A supplied catalog selector is normalized.
    logic: IF each supplied selector has exactly one active normalized match and any component belongs to the resolved service THEN use the server-resolved identities; ELSE reject without guessing or substitution.
    violation_behaviour: Return invalid_input for the affected selector, preserve the draft, and make zero POST attempts.
    source: [FR3.2, FR3.3, NFR1]

  - id: BR2.3
    statement: occurred_at is either explicitly timezone-qualified or the explicit now variant, which is captured once and frozen in UTC.
    category: validation
    applies_to: [TicketWriteDraftV1, NormalizedTicketCreateV1]
    trigger: occurred_at is normalized during prepare or revise.
    logic: IF an explicit offset or Z timestamp is valid THEN canonicalize it to UTC RFC3339; ELSE IF the explicit now variant is present THEN capture server time once and canonicalize it; ELSE reject it.
    violation_behaviour: Return invalid_input and never infer a client timezone or recapture now during confirmation or replay.
    source: [FR3.2, NFR2]

  - id: BR2.4
    statement: Normalization and serialization produce one deterministic logical body, canonical byte sequence, and SHA-256 hash.
    category: constraint
    applies_to: [NormalizedTicketCreateV1, CanonicalRequestBytesV1]
    trigger: A valid draft is prepared or revised.
    logic: Materialize the standard classification default, omit absent optionals, apply serialization version 1 and declared field order, encode compact UTF-8 JSON once, and hash the resulting bytes.
    violation_behaviour: Stop before confirmation if canonical bytes or their hash cannot be produced deterministically.
    source: [FR3.2, FR6.3, NFR2]

  - id: BR2.5
    statement: Invalid create input preserves safe user-entered values for correction without exposing raw upstream details.
    category: policy
    applies_to: [validation_result, presentation]
    trigger: Draft or catalog validation fails.
    logic: Return only server-owned field messages and the safe draft fields needed to revise; never return credentials, raw headers, exceptions, or unrestricted problem details.
    violation_behaviour: Fall back to the generic safe invalid-input presentation when a value cannot be safely echoed.
    source: [FR3.2, FR6.1, FR6.2, NFR1]

  - id: BR3.1
    statement: Prepare and revise persist the authoritative reviewed bytes, publish a matching complete create review, and perform no ticket POST.
    category: policy
    applies_to: [prepare, revise, SafeMutationReviewV1]
    trigger: A draft finishes validation and normalization.
    logic: Persist PreparedCreatePayloadV1 first, then publish the U1 pending create mutation with the same mutation identity, actor bindings, expiry, and payload hash; return every canonical body field plus the choices 확인, 수정, 취소 while execution remains forbidden.
    violation_behaviour: If either record or a complete review cannot be produced, do not publish executable pending confirmation, retire any orphan payload, and do not send.
    source: [FR3.3, FR3.4, NFR1]

  - id: BR3.2
    statement: A newly prepared or revised create review invalidates the previous pending create review in the same actor scope.
    category: constraint
    applies_to: [PendingCreateMutationV1]
    trigger: A valid create review is persisted.
    logic: Within the user, session, conversation, and create-operation scope, persist the new prepared payload first, then atomically replace the earlier U1 pending mutation with the new mutation identity and normalized payload hash; retire superseded payloads without granting them execution authority.
    violation_behaviour: If replacement is not atomic, return a safe failure and leave execution forbidden.
    source: [FR3.3, FR3.4, NFR2]

  - id: BR3.3
    statement: Pending create confirmation is valid for at most 15 minutes and only for its exact user, session, conversation, operation, and payload hash.
    category: authorization
    applies_to: [PendingCreateMutationV1, lifecycle]
    trigger: Confirmation is considered or a relevant lifecycle event occurs.
    logic: IF current server time is before expiry and all U1 pending and U2 prepared-payload bindings match THEN confirmation may proceed; logout, user switch, conversation clear, session expiry, cancellation, or replacement invalidates the pending mutation and retires its prepared payload.
    violation_behaviour: Consume or invalidate pending state as applicable, make zero POST attempts, and require a fresh review.
    source: [FR3.4, FR5.1, FR5.4, NFR1]

  - id: BR3.4
    statement: Only a current raw user turn equal to 확인 or confirm after allowed trimming and case normalization authorizes create execution.
    category: authorization
    applies_to: [confirmation_classifier, Runner]
    trigger: A turn arrives while a create review is pending.
    logic: IF the raw current turn is exactly one allowed token and BR3.3 passes THEN enter confirmation consumption; quoted, embedded, historical, model-generated, or externally supplied text never authorizes execution.
    violation_behaviour: Make zero POST attempts and treat the turn as revise, cancel, or ordinary conversation according to explicit intent.
    source: [FR3.4, FR5.1, NFR1]

  - id: BR3.5
    statement: CreateConfirmationHandoffV1 consumes a valid U1 pending create mutation and materializes its U2 durable attempt in one owned atomic operation.
    category: constraint
    applies_to: [PendingCreateMutationV1, TicketCreateAttemptV1]
    trigger: Exact confirmation passes every binding and freshness check.
    logic: In one write transaction, the U1 repository participant revalidates and consumes its row while the U2 participants rehash the same-mutation PreparedCreatePayloadV1, insert exactly one prepared attempt with a new immutable key and the stored canonical bytes, and retire the pre-confirm payload.
    violation_behaviour: Roll back every state transition and make zero POST attempts; an exact duplicate may return only the existing same-binding attempt and may never mint a second key, while every mismatch is rejected.
    source: [FR3.4, FR6.3, NFR2]

  - id: BR3.6
    statement: Cancel, mutation-bearing text, or any lifecycle invalidation executes no ticket POST.
    category: authorization
    applies_to: [cancel, revise, lifecycle]
    trigger: The current turn is 취소, asks to modify fields, or a binding lifecycle event occurs.
    logic: Invalidate the affected U1 pending state, retire its U2 prepared payload, and return the applicable safe next step; never interpret field changes as confirmation.
    violation_behaviour: Fail closed with execution disabled and require a new complete review.
    source: [FR3.4, FR5.4, NFR1]

  - id: BR4.1
    statement: The durable create-attempt row exists before the first ticket POST.
    category: constraint
    applies_to: [TicketCreateAttemptV1, create_execution]
    trigger: A valid create confirmation is consumed.
    logic: Persist canonical request bytes, serialization version, hash, unpredictable idempotency key, bindings, retention boundary, and attempt_count zero before network I/O.
    violation_behaviour: Make zero POST attempts when the ledger cannot be committed.
    source: [FR6.3, NFR2]

  - id: BR4.2
    statement: One create attempt entity uses one unpredictable idempotency key and one byte-identical request body for its entire lifetime.
    category: constraint
    applies_to: [TicketCreateAttemptV1, gateway_create]
    trigger: Any initial, refreshed, restarted, or reconciliation POST is considered.
    logic: Recompute and compare the stored byte hash, then send the exact stored bytes with the original key; no field, default, timestamp, encoding, or serialization may be regenerated.
    violation_behaviour: Fail closed as terminal_failure without sending if the bytes, hash, or key are absent or inconsistent.
    source: [FR6.3, NFR1, NFR2]

  - id: BR4.3
    statement: A confirmed create has a maximum of two total ticket POST attempts across refresh recall, restart, and reconciliation.
    category: constraint
    applies_to: [TicketCreateAttemptV1, create_execution]
    trigger: Another ticket POST is considered.
    logic: IF attempt_count is less than 2 and policy permits the specific follow-up THEN another attempt may start; ELSE no further automatic POST is allowed.
    violation_behaviour: Preserve an ambiguous or terminal failure outcome and instruct safe manual reconciliation without claiming success.
    source: [FR5.3, FR6.2, FR6.3, NFR7]

  - id: BR4.4
    statement: Every ticket POST is counted and marked in flight durably before network I/O.
    category: constraint
    applies_to: [TicketCreateAttemptV1, process_restart]
    trigger: TicketOperations authorizes a gateway call.
    logic: Atomically increment attempt_count and commit status in_flight before calling the gateway; an in_flight record observed after restart is classified as ambiguous rather than unsent.
    violation_behaviour: Do not call the gateway unless the pre-send transition commits.
    source: [FR6.3, NFR2]

  - id: BR4.5
    statement: Status 429 causes no automatic sleep and no automatic retry.
    category: policy
    applies_to: [create_execution, gateway_outcome]
    trigger: A ticket POST returns 429.
    logic: Return rate_limited immediately, include only a validated non-negative Retry-After seconds value when present, and do not spend the remaining attempt automatically.
    violation_behaviour: Make no further gateway call for that confirmation.
    source: [FR6.2, NFR7]

  - id: BR4.6
    statement: Reusing an idempotency key with different request bytes is forbidden.
    category: authorization
    applies_to: [TicketCreateAttemptV1, gateway_create]
    trigger: Stored state is loaded or a follow-up send is prepared.
    logic: IF the stored key is associated with the same serialization version, byte sequence, and hash THEN continue under policy; ELSE stop before network I/O.
    violation_behaviour: Mark terminal_failure with a safe internal-consistency outcome and never send the conflicting body.
    source: [FR6.3, NFR1, NFR2]

  - id: BR4.7
    statement: Create success requires a ticket ID and authoritative created or Idempotent-Replayed evidence.
    category: policy
    applies_to: [CreateCompletionEvidenceV1, SafeMutationResultV1, TicketMutationToolResultV1, TicketCreateAttemptV1]
    trigger: A create response is mapped.
    logic: IF a valid created response or a valid Idempotent-Replayed response contains the ticket ID THEN mark completed, map internal evidence into shared SafeMutationResultV1 with operation create and ticket_id plus optional idempotent_replayed and request_id, and return it in TicketMutationToolResultV1.data; every other response remains non-success.
    violation_behaviour: Map malformed or unsupported success-like responses to upstream_unavailable or ambiguous without inventing a ticket ID.
    source: [FR3.5, FR6.2, FR6.3, NFR1]

  - id: BR4.8
    statement: An ambiguous outcome is never reported as success and reconciliation never exceeds the shared attempt cap.
    category: policy
    applies_to: [timeout, transport_failure, server_failure, process_restart]
    trigger: A sent request has no authoritative safe terminal response.
    logic: Persist ambiguous; IF one attempt remains and the approved reconciliation policy runs THEN repeat once with identical key and bytes, otherwise stop and present manual reconciliation guidance.
    violation_behaviour: Never mint a new key, never claim failure means not-created, and never claim success without BR4.7 evidence.
    source: [FR6.2, FR6.3, NFR1, NFR7]

  - id: BR4.9
    statement: Durable create-attempt state is retained for at least 24 hours across logout, user switch, conversation clear, session expiry, and process restart.
    category: constraint
    applies_to: [TicketCreateAttemptV1, cleanup]
    trigger: Cleanup or lifecycle isolation runs.
    logic: Revocable session and confirmation state may be removed, but no create-attempt row is deleted before retained_until and unresolved state is preserved for reconciliation.
    violation_behaviour: Skip deletion and emit only safe operational diagnostics.
    source: [FR5.4, FR6.3, NFR2]

  - id: BR4.10
    statement: One gateway create invocation performs exactly one HTTP attempt and owns no retry, sleep, refresh, or reconciliation policy.
    category: constraint
    applies_to: [ItsmGatewayV1.create_ticket]
    trigger: The gateway method is invoked.
    logic: Serialize the already-supplied immutable bytes into one request, send once, parse once, and return one typed allowlisted outcome.
    violation_behaviour: Treat hidden re-invocation as a contract violation.
    source: [FR6.2, FR6.3, NFR2]

  - id: BR5.1
    statement: Only the current server-session delegated credential authorizes the ticket POST.
    category: authorization
    applies_to: [TicketOperations, ItsmGatewayV1]
    trigger: A ticket POST is prepared.
    logic: Obtain capability from the current server session at the outbound boundary; ignore model, browser, persisted payload, and external text claims about identity or authority.
    violation_behaviour: Stop before POST and return authentication_required or permission_denied as appropriate.
    source: [FR5.1, FR5.2, NFR1]

  - id: BR5.2
    statement: Create results, errors, logs, and persistence expose only safe allowlisted data.
    category: authorization
    applies_to: [tool_result, presentation, logging, persistence]
    trigger: Data crosses an internal trust boundary or is recorded.
    logic: Exclude credentials, idempotency keys, canonical bytes, raw headers, raw exceptions, unrestricted upstream bodies, and raw problem detail; expose only SafeErrorV1 or the exact shared SafeMutationResultV1 fields in TicketMutationToolResultV1.
    violation_behaviour: Redact and fall back to upstream_unavailable when safe mapping is impossible.
    source: [FR6.1, FR6.2, NFR1]

  - id: BR5.3
    statement: All ITSM-origin text remains escaped untrusted data and never changes control flow.
    category: authorization
    applies_to: [catalog_labels, error_mapping, presentation, model_context]
    trigger: External text is read, stored, displayed, or reintroduced to the model.
    logic: Treat the text only as data; instruction-like content cannot authorize confirmation, select credentials, change tools, or alter retry and reconciliation policy.
    violation_behaviour: Preserve control state and omit unsafe text if it cannot be escaped safely.
    source: [FR6.1, NFR1]

  - id: BR5.4
    statement: Every create interaction has an accessible text presentation independent of rich rendering.
    category: policy
    applies_to: [ticket_input, ticket_review, ticket_success, ticket_auth_error, ticket_rate_limited, ticket_ambiguous, ticket_unavailable]
    trigger: The presentation layer renders a create state.
    logic: Provide plain text with field labels, status, explicit choices or next action, and no color-only meaning; rich cards may enhance but never replace it.
    violation_behaviour: Fall back to text-only rendering.
    source: [FR7.1, FR7.2, NFR5]

  - id: BR5.5
    statement: U2 registers ticket_write and its create presentation mappers through RegistryV1 without editing the U1 common registry implementation.
    category: constraint
    applies_to: [TicketWritePluginV1, composition_root]
    trigger: Application composition loads U2.
    logic: Contribute contract version 1, tool name ticket_write, its FunctionTool factory, and create mapper keys through the documented registry API.
    violation_behaviour: Fail startup validation on duplicate, missing, or unknown registrations.
    source: [FR7.3, NFR2]

  - id: BR5.6
    statement: U2 functional behaviour is deterministically testable with injected clock, randomness, gateway outcomes, and blocked real network.
    category: constraint
    applies_to: [unit_tests, integration_tests, contract_tests]
    trigger: Automated tests execute.
    logic: Inject explicit now, CSPRNG output, catalog and gateway fakes, process-restart state, and lifecycle events; fail any test that attempts undeclared network access.
    violation_behaviour: Treat nondeterministic or live-network-dependent behaviour as a failed quality gate.
    source: [NFR2, NFR8, NFR9]
```

## Rule Summary

| Area | Rules | Outcome |
|---|---|---|
| Input and normalization | BR2.1–BR2.5 | Only a complete, catalog-valid, timezone-safe, deterministic body reaches review |
| Human confirmation | BR3.1–BR3.6 | Review is revocable, actor-bound, short-lived, and executable only by an exact current-turn token |
| Idempotency and ambiguity | BR4.1–BR4.10 | The ledger precedes network I/O; one key and byte sequence survive at most two counted attempts |
| Trust and presentation | BR5.1–BR5.6 | Delegated authorization, allowlisted output, untrusted external text, accessible rendering, additive registration, and deterministic tests are enforced |

## Rule Precedence

Authorization and no-send rules take precedence over retry or reconciliation rules. Attempt-count and immutable-byte checks take precedence over any refresh or recovery opportunity. No rule permits a success claim without BR4.7 evidence.
