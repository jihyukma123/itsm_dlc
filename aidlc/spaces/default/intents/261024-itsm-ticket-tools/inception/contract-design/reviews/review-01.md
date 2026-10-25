## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T04:29:41Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > C-03 registry, C-04 plugin, C-05 plugin | 최종 tool 이름만 고정되어 있고 세 function tool의 실제 호출 계약이 완결되지 않았다. `ticket_read`는 input/result plugin spec이 전혀 없고, `ticket_update`의 `input_schema`는 `ticket_id`가 없는 `TicketPatchInV1`뿐이다. `ticket_write`와 `ticket_update` 모두 draft/review 이후 사용자의 명시적 확인·수정·취소가 어떤 tool argument와 서버 검증을 거쳐 `PendingMutationRepositoryV1.confirm`으로 이어지는지 정의하지 않는다. 이 상태에서는 구현자가 확인 protocol을 추측해야 하며 확인 전 POST/PATCH 금지 불변식을 일관되게 구현할 수 없다. | `ticket_read`, `ticket_write`, `ticket_update` 각각에 대해 versioned function-tool input/result schema를 추가한다. 조회에는 ID 대 목록 필터·cursor와 안전 result를, 수정에는 필수 `ticket_id`를 포함한다. 등록·수정에는 prepare/review/confirm/revise/cancel 단계와 비밀이 아닌 pending reference 또는 동등한 binding, 명시적 사용자 확인을 서버가 검증하는 조건, 각 단계의 안전 result를 정의하고 repository port와 연결한다. | New |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > C-07 ITSM API v2 Outbound Profile security | profile 최상위 `security: delegatedBearer`가 모든 operation에 상속되지만 `/api/v2/auth/token`에는 override가 없다. 따라서 token exchange 자체가 이미 발급된 위임 bearer를 요구하는 계약이 되며, 원본 계약의 client credential body 기반 무인증 token 발급과 모순된다. catalog operation도 service token 또는 delegated token을 허용한다고 적으면서 실제 OpenAPI security는 delegated bearer 하나로 고정되어 있다. | 최상위 security를 제거하고 operation별로 명시한다. `/api/v2/auth/token`은 `security: []`, catalog는 기존 gateway가 허용하는 bearer 종류를 표현하고, ticket GET/POST/PATCH만 현재 서버 세션 사용자의 delegated bearer를 요구하도록 고정한다. token 종류의 의미를 OpenAPI extension 또는 별도 named scheme으로 명확히 한다. | New |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > C-07 components.schemas.TicketPatchIn | authoritative `docs/itsm/openapi.json`의 `TicketPatchIn`은 여덟 필드 모두 명시적 `null`을 허용하지만 profile은 `title`, `description`, `impact_level`, `urgency`, `impact_note`, `is_major`를 non-null로 축소했다. 이는 FR4.2의 omit/null 구분과 충돌하며 유효한 clear 요청을 client에서 거부하거나 다른 PATCH body를 만들게 한다. | C-07의 여덟 PATCH 필드를 원본 OpenAPI와 동일하게 nullable로 정의하고, omit은 변경 없음, explicit null은 clear 요청이라는 의미를 C-02의 `TicketPatchInV1`과 함께 고정한다. no-op 판정은 schema nullability가 아니라 실제 현재 값과의 diff에서 수행한다. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| Ruby YAML parser and local `$ref` resolver | PASS: 7 fenced YAML blocks parsed; all local OpenAPI schema references resolved | 문법과 local reference 구조는 유효하다. |
| DAG boundary cross-check | PASS: C-01~C-05 map the five direct edges; C-06 and C-07 cover browser and ITSM external boundaries | 경계 목록 자체에는 누락이나 순환이 없다. |
| Function-tool contract inspection | FAIL: no `TicketReadPlugin` spec; `ticket_update` resolves only to `TicketPatchInV1`, which lacks `ticket_id`; no mutation command/confirmation input contract exists | 첫 번째 Major finding을 확인한다. |
| OpenAPI security inheritance inspection | FAIL: profile global security is `delegatedBearer`; `/api/v2/auth/token` has no operation override | 두 번째 Major finding을 확인한다. |
| ITSM source/profile patch nullability comparison | FAIL: mismatches for `title`, `description`, `impact_level`, `urgency`, `impact_note`, `is_major` | 세 번째 Major finding을 확인한다. |

### Summary

모든 DAG와 외부 경계는 문서에 등장하고 YAML 구조도 유효하지만, 핵심 function-tool protocol과 ITSM 인증·PATCH schema가 아직 구현자가 그대로 따를 수 있는 계약이 아니다. 세 Major gap을 수정해야 명시적 확인, 위임 인증, omit/null 무결성을 안전하게 구현할 수 있다.
