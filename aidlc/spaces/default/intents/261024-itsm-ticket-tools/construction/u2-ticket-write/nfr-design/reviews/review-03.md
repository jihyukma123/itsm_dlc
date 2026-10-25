## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T14:37:49Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/security-design.md > SEC-U2-09 and SEC-U2-10; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/logical-components.md > LC-U2-08 Refresh Reservation Coordinator | 설계는 U2가 “U1 credential refresh port”를 호출하고 refresh 성공 credential을 U1 session에 commit한 뒤 restart에서 재사용한다고 가정하지만, 승인된 `contract-summary.md`에는 그런 공개 port나 결과 shape가 없다. 공개된 `TicketRequestCapability`는 한 HTTP request 범위이고 credential 값은 gateway를 통해서만 접근할 수 있으며, `ItsmGatewayV1`은 token-refresh 판단을 금지한다. 따라서 U2가 refresh를 요청하는 입력, commit 성공을 확인하는 방법, crash 뒤 새 capability를 재구성하는 방법이 모두 미정이라 public-port-only 경계를 지키면서 SEC-U2-09/10을 구현할 수 없다. | U1 소유의 versioned refresh operation을 승인된 계약에 정의해 입력, one-shot 호출 ownership, credential commit의 원자성·idempotency, 성공 증거와 새 `TicketRequestCapability` 획득 방식을 명시하거나, 이미 승인된 공개 계약만으로 같은 동작을 구현하도록 SEC-U2-09/10과 LC-U2-08을 재설계하라. 해당 provider/consumer contract test도 추가하라. | Resolved (reviewer) |
| R-02 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/logical-components.md > Logical Component Inventory and Dependency Direction | LC-U2-01의 Allowed dependencies에는 LC-U2-09가 없지만 Dependency Direction은 Tool Adapter가 Create Result and Presentation Mapper를 직접 호출한다고 정의한다. Inventory와 호출 그래프가 달라 mapper 호출 책임과 테스트 대역 경계가 불명확하다. | LC-U2-01의 allowed dependency에 LC-U2-09를 추가하거나 mapper 호출을 LC-U2-02 또는 U1 조립 경계가 소유하도록 그래프와 component contract를 하나로 정렬하라. | Resolved (reviewer) |
| R-03 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > `CredentialRefreshReservationV1` and `CredentialRefreshPortV1` preconditions; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/security-design.md > SEC-U2-09 and SEC-U2-10 | Refresh port는 current capability와 reservation의 actor binding이 일치해야 한다고 요구하지만 `CredentialRefreshReservationV1`에는 `create_attempt_id`, reservation ID, used time만 있고 user/session/conversation binding이나 U1이 검증할 수 있는 attestation이 없다. U1 provider는 U2 ledger를 읽는 dependency도 승인받지 않았으므로 해당 precondition을 구현할 수 없고, 다른 actor의 capability와 탈취·오결합된 reservation을 구별할 수 없다. | Reservation type에 U1이 current capability와 직접 비교할 immutable user/session/conversation binding 또는 검증 가능한 server attestation을 추가하고, U2 CAS가 그 값을 ledger actor binding에서 생성하도록 정의하라. U1이 U2 repository를 역호출하지 않고 mismatch를 거부하는 provider/consumer test를 명시하라. | New |
| R-04 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/nfr-design/security-design.md > SEC-U1-03 and Credential refresh seam; aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > `CredentialRefreshPortV1`; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/security-design.md > Authentication, Authorization, and Confirmation | U1 provider design은 operation을 `refresh(capability_ref, one_shot_budget_token, remaining_deadline)`로 정의하지만 승인 계약과 U2 consumer는 `refresh_delegated_capability_once(TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline)`를 사용한다. 이름과 입력 타입이 달라 provider와 consumer가 동일 interface를 구현한다는 보장이 없다. | U1 provider design의 operation 이름과 입력 타입을 C-01의 정확한 signature로 정렬하고 U1 provider test와 U2 consumer test가 같은 contract fixture를 사용하도록 명시하라. | New |
| R-05 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/logical-components.md > LC-U2-08 Refresh Reservation Coordinator | 설계는 `refresh_reservation_id`를 actor binding을 검증하는 server-authenticated opaque envelope로 간주하고 `process-start epoch` 변화로 실제 restart를 판별하지만, envelope에 들어갈 actor·epoch claim, 인증 방식과 key 소유·검증 절차, reservation 생성 process를 비교할 durable 근거를 정의하지 않는다. 전달된 C-01 구조에도 actor 또는 creator-process 필드는 없고 U1은 U2 repository를 역호출하지 않으므로, 구현자는 U1의 actor-binding precondition과 live loser 무간섭 대 restart recovery를 안전하게 구현할 수 없다. 잘못 추측하면 다른 actor의 refresh 또는 live owner의 조기 terminalization이 가능하다. | 새 V1 필드를 추가하지 않는 방향을 유지하려면 opaque envelope의 canonical claims에 actor binding과 reservation 생성 process epoch를 명시하고, stdlib 기반 인증 방식·key 소유/회전·U1 검증 절차·생성 및 CAS 순서를 정의하라. 또한 같은 process의 active reservation registry와 restart 후 비어 있는 registry를 durable envelope와 대조하는 정확한 알고리즘 및 race tests를 적어라. 이 방식이 C-01에서 허용되지 않으면 Contract Design을 다시 열어 검증 가능한 binding을 추가하라. | New |
| R-06 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/security-design.md > Claim and Recovery State Design > Ambiguous reconciliation ownership and Reconciliation outcome | `last_outcome`의 정의되지 않은 내부 phase를 `started`로 바꿔 single owner를 확보하지만, 그 CAS 직후 process가 중단된 경우의 재개 규칙이 없다. 새 owner·deadline을 금지하고 `started` 상태의 경쟁 caller도 배제하므로 attempt가 영구히 조정 불가 상태로 남을 수 있다. 반대로 누구나 `started`를 재개하게 하면 documented lookup이 생기는 순간 둘 이상의 caller가 같은 외부 조회를 수행할 수 있다. | 현재 lookup-unavailable 경로는 ownership과 `retryable_after_reconcile` 또는 terminal `ambiguous` 전이를 하나의 no-I/O CAS로 끝내도록 명시하라. 향후 외부 lookup을 허용하려면 기존 claim ID만으로 crash-safe하게 재개 가능한 명시적 `last_outcome` schema, phase 전이, idempotency 및 동시 재개 규칙을 정의하고 crash-after-start barrier test를 추가하라. | New |
| R-07 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-design/traceability.json > coverage entries NFR1.1, NFR1.3, NFR3.7 | 세 `OK` target이 실제 control ID와 맞지 않는다. Secret containment는 SEC-U2-13인데 NFR1.1은 SEC-U2-12를 가리키고, allowlisted error mapping도 SEC-U2-13인데 NFR1.3은 SEC-U2-11/12를 가리키며, authoritative ticket-ID completion은 SEC-U2-12인데 NFR3.7은 SEC-U2-11을 가리킨다. | NFR1.1과 NFR1.3을 SEC-U2-13 및 해당 boundary matrix로, NFR3.7을 SEC-U2-12로 수정하고 모든 target ID가 실제 section 의미와 일치하는지 다시 검사하라. | New |

> R-03 Not re-checked this round

> R-04 Not re-checked this round

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `jq` traceability shape and ID-set check | PASS | JSON은 유효하고 upstream ID와 coverage ID 집합, status와 non-empty target 형식이 일치한다. |
| `git diff --check` on the three review artifacts | PASS | 공백 오류나 patch 형식 오류는 없다. |
| Artifact-to-contract cross-reference inspection | FAIL | Refresh envelope와 process epoch의 검증 가능한 표현이 C-01에 없고, 세 traceability target이 실제 SEC control 의미와 불일치한다. |

### Summary

Ledger-first, existing-claim fencing, one-shot refresh 방향은 일관되지만, refresh reservation의 actor/restart 증명과 reconciliation owner crash 복구가 아직 구현 가능한 계약으로 닫히지 않았다. 특히 refresh 경계는 권한 검증을 추측에 맡기므로 현재 상태로는 구현 준비가 되지 않았다.
