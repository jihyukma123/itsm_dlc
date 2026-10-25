## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T06:45:26Z
**Iteration:** 2
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/rules.md > Authoritative Rule Set | 모든 규칙 ID가 센서와 단계 계약이 인식하는 `BR{group}.{seq}` 형식이 아닌 `BR-U1-001` 형식이며, 각 규칙에 필수인 category, trigger, IF-THEN logic, violation behaviour, FR 또는 NFR source가 없다. 뒤의 요약도 규칙 요약표가 아니라 두 개의 결정표뿐이어서 개발자가 위반 처리와 출처를 규칙별로 일관되게 구현할 수 없다. | 규칙 ID를 `BR1.1` 같은 안정 형식으로 바꾸고 각 YAML 항목에 category, applies-to, trigger, IF-THEN logic, violation behaviour, FR 또는 NFR source를 채운 뒤 모든 규칙을 보여 주는 짧은 요약표를 추가한다. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/traceability.json > coverage and reverse | `OK` 행의 target이 유효한 BR ID만 가리키지 않고 workflow와 entity prose 및 인식 불가능한 `BR-U1-*`를 섞는다. `reverse`는 upstream 없는 규칙을 설명해야 하지만 FD workflow를 넣었고 각 행에 status와 target도 없다. 따라서 23개 acceptance criterion의 기계적 커버리지와 orphan 규칙 판정이 성립하지 않는다. | 수정된 `BRx.y`만 각 `OK.target`에 명시하고, `reverse`에는 upstream ID가 없는 규칙만 `id`, `status`, `target` 형식으로 남기며 나머지 workflow 역매핑은 제거한다. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/entities.md > value_objects and PendingTicketMutation | source-of-truth 타입이 승인된 V1 계약과 충돌한다. `SafeTicketSummaryV1`은 필수 `created_at`을 빼고 계약에 없는 `assignee`를 넣었으며, `SafeErrorV1`은 `message_key`와 `field_errors` 대신 `safe_message`, `field`, `next_action`을 선언한다. `PendingTicketMutation`은 필수 `status`를 속성에서 누락하고 계약에 없는 `active`와 `superseded` 상태를 도입한다. 이대로면 U2, U3와 tool result consumer가 서로 다른 schema를 구현한다. | C-01과 C-03A의 exact V1 필드, required와 additional-properties 규칙, status enum에 entities YAML을 맞춘다. 새 검토가 이전 것을 대체하는 결정은 기존 `invalidated` 상태와 무효화 사유로 표현하거나 shared contract를 먼저 versioned change로 갱신한다. | Resolved (reviewer) |
| R-04 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/functional-spec.md > Safe Output Semantics | 표가 `invalid_input`, `ticket_not_found`, `rate_limited`, `authentication_required`, `temporarily_unavailable`, `continuation_invalid`, `contract_failure`를 결과 state로 정의하지만 C-03A의 `TicketReadToolResultV1.state`는 `succeeded`, `empty`, `failed`만 허용한다. 일부 명칭은 `SafeErrorV1.code`와도 다르다. 구현자는 계약 위반 wire result를 만들거나 이 명세를 무시해야 한다. | 표를 top-level result state와 nested safe error code로 분리하고, state는 승인된 세 값만 사용하며 error code는 C-01의 정확한 enum 이름으로 매핑한다. continuation과 contract failure가 필요하면 기존 code로 명확히 매핑하거나 versioned contract change를 선행한다. | Resolved (reviewer) |
| R-05 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/functional-spec.md > Workflow FD-U1-06 — Tool and Presentation Assembly | presentation 저장 흐름이 shared contract의 동시성 및 응답 원자성을 빠뜨렸다. C-03은 대화별 단일 lock 아래 persisted assistant message 상관관계를 검증하고 metadata를 commit한 뒤 readback 성공 시에만 presentation을 노출하도록 요구하지만, 현재 순서는 단순 저장과 조회만 말한다. 동시 chat이나 저장 실패에서 잘못된 sequence 결합 또는 응답에는 보였지만 재시작 후 사라지는 metadata가 생길 수 있다. | FD-U1-06에 대화 lock 획득, Runner 완료 후 persisted message 상관관계 생성, 동일 lock 안의 검증과 원자적 insert-or-replace, commit readback 성공 후 노출, 실패 시 text-only fallback, lock 해제 순서를 명시한다. | Resolved (reviewer) |
| R-06 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/functional-spec.md > document views | 이 파일은 workflow와 state machine은 제공하지만, 필수 파생 뷰인 entities YAML 기반 ER Mermaid와 rules YAML 기반 전체 규칙 요약을 포함하지 않는다. ER 그림은 entities.md에만 있고 규칙 요약은 없다. | entities.md의 source-of-truth와 일치하는 ER Mermaid 및 텍스트 대체, rules.md의 모든 수정된 BR을 요약하는 파생 표를 functional-spec.md에 추가한다. | Resolved (reviewer) |
| R-07 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/entities.md > TicketRequestCapability and referenced ServerSession | 만료 검사는 `persisted server-session expiry`와 `session_expires_at`을 전제로 하지만 authoritative entity model에는 이를 소유하는 `ServerSession` 정의가 없고, 상위 component 계약의 `ServerSession`에도 credential 만료 시각만 있을 뿐 서버 세션 만료 시각은 없다. `functional-spec.md`와 BR1.6/BR5.6도 어떤 절대·유휴 만료 기준으로 값을 생성·갱신·영속화하는지, 기존 row를 어떻게 처리하는지 정하지 않아 구현자는 서로 다른 세션 수명을 선택하거나 영속 값 없이 cleanup을 구현하게 된다. | U1이 소비하는 `ServerSession` 계약에 별도의 영속 `session_expires_at` 필드와 절대 또는 유휴 만료 의미, 로그인 시 산정·갱신 규칙, 기존 row의 안전한 migration/backfill 규칙을 정의한다. 그 단일 필드를 capability 생성 전 비교와 FD-U1-07 cleanup의 기준으로 연결하고 경계 시각 및 재시작 검증 시나리오를 추가한다. | Resolved (reviewer) |
| R-08 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/functional-design/entities.md > Authoritative Entity Model > ServerSession | 새 `ServerSession`은 기존 record의 additive 확장이라고 설명하면서 `additional_properties: false` 아래 `session_id`, `user_id`, `conversation_id`, `created_at`, `session_expires_at`, `itsm_token_expires_at`만 허용한다. 그러나 상위 component 계약의 기존 필드인 `display_name`, `role`, `permissions`, `delegated_credential`, `credential_expires_at`, `refresh_credential`을 누락하고 `credential_expires_at`을 `itsm_token_expires_at`으로 사실상 rename했다. 이 source-of-truth를 그대로 구현하면 로그인 권한 복원과 위임 credential refresh에 필요한 기존 데이터를 거부·삭제하거나, 반대로 상위 계약을 따르면 `additional_properties: false`를 위반한다. | `ServerSession` YAML을 기존 상위 필드를 모두 그대로 보존하는 additive schema로 수정하고 `session_expires_at`만 추가한다. `credential_expires_at` 이름과 기존 의미를 유지하며, `conversation_id`와 `created_at`도 실제 기존 저장 계약에 이미 존재함을 상위 계약으로 확인하거나 명시적 additive migration 대상으로 구분한다. migration 및 contract test에 기존 row의 인증·권한·credential·refresh 값이 byte-for-byte 보존되고 새 만료 필드만 backfill됨을 추가한다. | New |

> R-07 Reviewer note: `ServerSession.session_expires_at`이 영속 필드로 정의됐고, 생성 시 정확히 8시간인 절대 만료, refresh 비연장, `now >= session_expires_at` 경계, legacy backfill, malformed row의 즉시 만료, 재시작 시 영속 값 재사용, capability·Runner·ITSM 이전 cleanup 및 실패 시 fail-closed 검증이 명시됐다.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| required-sections | PASS | entities, rules, functional specification과 traceability의 필수 구조 및 파생 ER/rules view가 존재한다. |
| upstream-coverage / traceability | PASS: 23 upstream IDs, 37 rule IDs, orphan 0, unresolved target 0 | acceptance criterion 집합과 모든 BR target이 구조적으로 일치한다. |
| JSON parse | PASS | `traceability.json`이 유효하며 upstream ID와 coverage ID 집합이 일치한다. |
| linter / type-check | N/A | 실행 가능한 TypeScript 또는 JavaScript snippet이 없다. |
| whitespace check | PASS | 네 산출물에 `git diff --check` 오류가 없다. |

### Summary

R-07의 절대 세션 만료·경계·재시작·선행 cleanup 설계와 strict read-for-update 및 CSPRNG 검증은 구체화됐다. 그러나 이를 추가한 `ServerSession` source-of-truth가 기존 인증 저장 계약을 보존하지 않아 additive migration으로 구현할 수 없다.
