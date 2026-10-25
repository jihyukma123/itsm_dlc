## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T11:11:10Z
**Iteration:** 2
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/security-design.md > SEC-U2-09 and SEC-U2-10; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/logical-components.md > LC-U2-08 Refresh Reservation Coordinator | 설계는 U2가 “U1 credential refresh port”를 호출하고 refresh 성공 credential을 U1 session에 commit한 뒤 restart에서 재사용한다고 가정하지만, 승인된 `contract-summary.md`에는 그런 공개 port나 결과 shape가 없다. 공개된 `TicketRequestCapability`는 한 HTTP request 범위이고 credential 값은 gateway를 통해서만 접근할 수 있으며, `ItsmGatewayV1`은 token-refresh 판단을 금지한다. 따라서 U2가 refresh를 요청하는 입력, commit 성공을 확인하는 방법, crash 뒤 새 capability를 재구성하는 방법이 모두 미정이라 public-port-only 경계를 지키면서 SEC-U2-09/10을 구현할 수 없다. | U1 소유의 versioned refresh operation을 승인된 계약에 정의해 입력, one-shot 호출 ownership, credential commit의 원자성·idempotency, 성공 증거와 새 `TicketRequestCapability` 획득 방식을 명시하거나, 이미 승인된 공개 계약만으로 같은 동작을 구현하도록 SEC-U2-09/10과 LC-U2-08을 재설계하라. 해당 provider/consumer contract test도 추가하라. | Resolved (reviewer) |
| R-02 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/logical-components.md > Logical Component Inventory and Dependency Direction | LC-U2-01의 Allowed dependencies에는 LC-U2-09가 없지만 Dependency Direction은 Tool Adapter가 Create Result and Presentation Mapper를 직접 호출한다고 정의한다. Inventory와 호출 그래프가 달라 mapper 호출 책임과 테스트 대역 경계가 불명확하다. | LC-U2-01의 allowed dependency에 LC-U2-09를 추가하거나 mapper 호출을 LC-U2-02 또는 U1 조립 경계가 소유하도록 그래프와 component contract를 하나로 정렬하라. | Resolved (reviewer) |
| R-03 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > `CredentialRefreshReservationV1` and `CredentialRefreshPortV1` preconditions; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/security-design.md > SEC-U2-09 and SEC-U2-10 | Refresh port는 current capability와 reservation의 actor binding이 일치해야 한다고 요구하지만 `CredentialRefreshReservationV1`에는 `create_attempt_id`, reservation ID, used time만 있고 user/session/conversation binding이나 U1이 검증할 수 있는 attestation이 없다. U1 provider는 U2 ledger를 읽는 dependency도 승인받지 않았으므로 해당 precondition을 구현할 수 없고, 다른 actor의 capability와 탈취·오결합된 reservation을 구별할 수 없다. | Reservation type에 U1이 current capability와 직접 비교할 immutable user/session/conversation binding 또는 검증 가능한 server attestation을 추가하고, U2 CAS가 그 값을 ledger actor binding에서 생성하도록 정의하라. U1이 U2 repository를 역호출하지 않고 mismatch를 거부하는 provider/consumer test를 명시하라. | New |
| R-04 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/nfr-design/security-design.md > SEC-U1-03 and Credential refresh seam; aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > `CredentialRefreshPortV1`; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/security-design.md > Authentication, Authorization, and Confirmation | U1 provider design은 operation을 `refresh(capability_ref, one_shot_budget_token, remaining_deadline)`로 정의하지만 승인 계약과 U2 consumer는 `refresh_delegated_capability_once(TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline)`를 사용한다. 이름과 입력 타입이 달라 provider와 consumer가 동일 interface를 구현한다는 보장이 없다. | U1 provider design의 operation 이름과 입력 타입을 C-01의 정확한 signature로 정렬하고 U1 provider test와 U2 consumer test가 같은 contract fixture를 사용하도록 명시하라. | New |

> R-01 Reviewer note: C-01에 U1 소유 `CredentialRefreshPortV1.refresh_delegated_capability_once`가 추가되어 입력, one-shot exchange, atomic session commit, same-binding capability 결과와 commit 전후 crash semantics가 정의됐다. U2 SEC-U2-09/10과 LC-U2-08도 이 versioned port와 provider/consumer contract test를 직접 참조한다.

> R-02 Reviewer note: LC-U2-01의 Allowed dependencies에 LC-U2-09가 추가되어 Dependency Direction의 Tool Adapter → Presentation Mapper 호출과 일치한다.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| required-sections | PASS: security-design 11개, logical-components 11개 H2 확인 | 두 설계 문서가 문서형식 검사를 통과했다. |
| upstream-coverage | PASS: security-requirements, tech-stack-decisions, functional-spec, contract-summary 모두 참조됨 | 적용 가능한 상위 산출물이 설계에 연결됐다. |
| linter | N/A | 검토 산출물은 Markdown/JSON이며 TS/JS match 대상이 없다. |
| type-check | N/A | 검토 산출물은 Markdown/JSON이며 TS/TSX match 대상이 없다. |
| traceability | PASS: gap, orphan, missing row, invalid target 모두 0건 | 모든 상세 NFR이 설계 target에 구조적으로 연결됐다. |

### Summary

기존 두 finding은 수정됐고 U2 내부 claim·budget·success-evidence 설계와 component dependency는 정렬됐다. 그러나 새 refresh contract의 reservation으로 actor binding precondition을 검증할 수 없고 U1 provider signature도 계약과 달라 cross-unit refresh 경계는 아직 구현 가능하지 않다.
