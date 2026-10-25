# U2 Ticket Write — NFR Design Questions

## Context

확인된 NFR 요구사항은 현재 Functional Design과 승인된 C-01/C-04 계약이 서로 다른 persistence·transaction 흐름을 규정하므로, 하나의 authoritative 흐름으로 다시 정렬되기 전에는 NFR Design과 Code Generation을 진행하지 않도록 요구한다. 앞 단계에서 확인한 선호 방향은 기존 `ticket_create_attempts`와 U1 공개 confirmation port만 사용하는 ledger-first 방식이다.

## Questions

### Q1. 상위 설계를 어떤 방식으로 정렬할까요?

이 선택은 지금 NFR Design을 멈추고 어느 상위 단계를 다시 열지 결정한다.

A. Functional Design을 다시 열어 ledger-first/public-port-only 흐름으로 정렬한다 (Recommended) — 별도 pre-confirm table과 cross-owner transaction port를 제거하고, 기존 `ticket_create_attempts`, U1 공개 confirmation port, CAS execution claim으로 entity·rules·workflow·state/storage를 다시 설계·검토한다.
B. Contract Design을 다시 열어 현재 Functional Design 흐름을 승인한다 — `prepared_create_payloads` table과 U1 transaction-participant API를 정식 공유 계약·migration·consumer test 범위에 추가한다.
X. Other (please specify)

[Answer]: A. Functional Design을 다시 열어 ledger-first/public-port-only 흐름으로 정렬한다 (Recommended)

## Assumptions & Open Questions

- Q1이 정해질 때까지 NFR Design 산출물은 생성하지 않는다.
- 두 흐름을 혼합하거나 후속 구현자가 임의로 선택하는 방안은 허용하지 않는다.

## Consolidated Summary Confirmation

기능 설계 재정렬이 완료된 현재 상태를 기준으로, 아래 결정을 NFR Design에 반영한다.

- U2의 authoritative 흐름은 기존 `ticket_tools_create_v1.ticket_create_attempts`를 review 전에 저장하는 ledger-first 방식이다.
- U1 confirmation은 공개 `put`·`get`·`confirm`·`consume_once`·`invalidate` port만 사용하며 cross-owner transaction port를 추가하지 않는다.
- Reconciliation은 별도 recovery identity를 만들지 않고 기존 send `claim_id`를 owner와 outcome fence로 유지한다.
- Credential refresh는 one-shot durable reservation과 credential generation evidence를 사용하며, 같은 process의 경쟁 caller는 `reserved` 상태를 변경하지 않는다.
- 이미 사용된 refresh 뒤의 authoritative no-apply 401은 추가 refresh·claim·POST 없이 terminal authentication failure로 끝나야 한다. 현재 상위 기능 설계의 durable transition 표현 불일치는 NFR Design에서 숨기지 않고 구현 선행조건으로 명시한다.
- 새 service, queue, distributed lock, cache, database는 추가하지 않고 기존 Python/FastAPI/httpx/SQLite/pytest 경계를 유지한다.
- 검증은 FakeModel·MockTransport·fake clock·deterministic barrier와 changed-code line coverage 80% 기준을 사용한다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
