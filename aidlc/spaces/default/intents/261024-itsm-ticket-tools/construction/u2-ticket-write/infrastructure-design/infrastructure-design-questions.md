# U2 Ticket Write — Infrastructure Design Questions

## Context

U2는 기존 FastAPI 프로세스에 포함되는 library Unit이고, 승인된 기능·NFR·계약 설계는 새 service, queue, cache, distributed lock, database, cloud resource, CI provider 또는 배포 환경을 추가하지 않기로 이미 확정했다. 따라서 이 단계에서 새로 결정할 infrastructure 선택은 없다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U2를 위해 새 cloud resource, container, IaC stack, environment, CI workflow 또는 별도 deployment pipeline을 만들지 않는다. 기존 FastAPI 프로세스, application-lifetime `httpx.AsyncClient`, Server Session SQLite와 저장소 밖 승격 경로를 그대로 사용한다.
- 이 library Unit의 infrastructure 산출물은 기존 승격 경로가 실행할 검증 순서를 정의한 `cicd-pipeline.md`와 `traceability.json`으로 제한한다.
- U2는 기존 Server Session SQLite에 승인된 `ticket_tools_create_v1.ticket_create_attempts` migration만 추가한다. U1 소유 `ticket_tools_state_v1`·`ticket_tools_history_v1`을 수정하지 않고, credential을 ledger에 저장하지 않으며, confirmed row는 `confirmed_at + 24h` 이전에 삭제하지 않는다.
- merge 또는 승격 전에는 dependency pin 확인, 기존 전체 pytest, FakeModel/MockTransport 기반 U2 contract·security·restart·concurrency 테스트, 실제 OpenAI·ITSM network 0건, secret/key/canonical-body canary 노출 0건, 변경 application code line coverage 80% 이상을 모두 통과해야 한다.
- 등록 안전성은 ledger-first publication, U1 `consume_once` evidence binding, send/recovery claim CAS, durable one-shot refresh reservation, 동일 key·동일 bytes, 전체 POST 최대 2회, authoritative ticket ID 없는 성공 0건을 deterministic counter와 SQLite row snapshot으로 입증한다.
- Network 차단은 특정 CI provider의 방화벽을 가정하지 않고 pytest process의 default-deny fixture와 deliberate bypass probe로 증명한다. 실제 ITSM/OpenAI smoke는 별도 운영 승인과 명시적 credential이 있는 수동 절차로만 수행한다.
- 현재 single-process 배포에서는 U1 per-conversation lock과 SQLite CAS를 유지한다. 배포가 multi-process로 바뀌면 shared lock 또는 transactional arbitration을 먼저 재설계하고, 그 전에는 U2를 해당 형태로 승격하지 않는다.
- 배포 전략, 환경 승격, production 승인과 rollback 실행은 기존 저장소 밖 절차를 유지한다. U2 rollback은 애플리케이션 버전을 되돌리되 additive ledger schema와 최소 보존 row를 삭제·downgrade하지 않는 방식으로 제한한다.
- U1 provider와 U2 consumer가 C-01의 정확한 `refresh_delegated_capability_once(TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline)` signature와 동일 contract fixture를 사용한다는 증거가 나오기 전에는 U2 code generation·merge·승격을 차단한다.
- 장기 안정 refresh-envelope key source, 설정 이름, 소유 component, signer/verifier interface, restart 지속성, `kid` rotation·폐기·검증 가능 기간은 승인된 상위 계약에 아직 없다. 이를 기존 primitive로 가정하지 않고, Contract/기술 결정을 보완해 승인하기 전에는 refresh 경로 구현과 승격을 차단한다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
