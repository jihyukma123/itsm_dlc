# U3 Ticket Update — NFR Design Questions

## Context

이전 점검에서 발견된 저장·원자적 publication 차단 조건에 대해 사용자는 상위 계약 확장을 선택했다. 최신 C-02/C-05는 U1 `replace_update_pending` transaction, U3-owned `PendingUpdateExecutionV1` 저장소, migration 순서, lifecycle cleanup과 U4 verification을 확정했고, 갱신된 Functional Design과 NFR Requirements가 이를 반영해 검토를 통과했다.

## Questions

### Q1. U3의 저장·원자적 publication 경계를 어떻게 해결할까요?

- A. **상위 계약 확장 (Recommended)** — Contract Design과 component ownership을 다시 열어 U3-owned `PendingUpdateExecutionV1` 저장소, U1-owned atomic replacement port, lifecycle cleanup과 U4 verification을 정식 계약에 추가한다. 현재 승인된 안전·복구·기존 review 보존 의미를 유지한다.
- B. **요구사항 단순화** — 별도 durable execution과 원자적 old-review 보존 요구를 낮춰 현재 C-02 operation만으로 구현 가능한 revise/confirm 의미를 다시 정의한다. restart 또는 publication failure의 사용자 경험과 무결성 보장이 약해지므로 관련 Functional Design과 NFR을 재승인해야 한다.
- C. **U3 전달 연기** — `ticket_update`를 이번 전달에서 보류하고 U1/U2와 U4의 나머지 출시 보증만 진행한다. 정확히 세 도구라는 승인 범위와 release 계획도 함께 다시 조정해야 한다.
- X. Other (please specify)

[Answer]: A. 상위 계약 확장 (Recommended)

Resolution: 최신 C-02/C-05 및 component ownership에 해당 경계가 반영됐다. NFR Design은 이 승인된 계약을 구체적인 보안·failure-domain·migration·recovery 설계로 변환한다.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U3는 기존 FastAPI modular monolith와 server-session SQLite 안에서 동작하며 새 서비스, queue, cache, distributed lock 또는 database를 추가하지 않는다.
- `ticket_tools_update_v1.pending_update_executions`는 U3만 쓰고 U1 `ticket_tools_state_v1` 뒤/U3 plugin 활성화 전에 멱등 migration한다. 부분 실패나 schema mismatch에서는 activation과 PATCH를 fail closed한다.
- publication은 U3 staged 저장 → U1 exact-old atomic replacement → U3 exact-binding active CAS 순서다. 실패·crash·동시 confirm/revise는 정확한 affected row와 state transition으로 단일 승자를 결정하고 broad invalidation을 사용하지 않는다.
- 실행 권한은 exact active U3 row, exact U1 pending, current-turn explicit confirmation과 원자적 consume evidence의 교집합이다. Canonical patch hash와 actor·ticket·base version을 PATCH 직전에 다시 검증한다.
- PATCH gateway 호출은 기본 1회이며 authoritative no-apply 401에서만 동일 patch/version으로 추가 1회가 가능하다. 그 밖의 conflict·timeout·transport·ambiguous·429에는 자동 재전송이나 대기가 없다.
- 응답 유실은 exact actor/session/conversation/ticket locator와 U1 rebinding으로 같은 pending reference만 복구한다. Version drift나 mismatch에서는 PATCH 없이 conflict/revise/cancel로 수렴한다.
- 보안 설계는 기존 session DB file/access control을 상속하되 canonical business payload를 model·log·error·diagnostic export에서 제외하고, terminal row는 기존 session cleanup window 뒤 물리 삭제한다.
- 단일-process 범위에서는 기존 per-conversation serialization과 SQLite transaction/CAS를 사용한다. 다중-process 배포는 shared lock 또는 동등한 transaction 설계가 필요한 잔여 위험으로 유지한다.
- FakeModel, MockTransport, fake clock, deterministic barriers와 restart snapshots로 migration, crash, tamper, response loss, secret canary와 PATCH 총 시도 상한을 검증한다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
