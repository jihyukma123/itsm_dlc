# U3 Ticket Update — Infrastructure Design Questions

## Context

U3는 기존 FastAPI 프로세스 안에서 동작하는 library Unit이며, 승인된 기능·NFR·계약 설계는 새 서비스, queue, cache, distributed lock, database, cloud resource, CI provider 또는 배포 환경을 추가하지 않기로 이미 확정했다. 따라서 이 단계에서 새로 결정할 infrastructure 선택은 없다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U3를 위해 새 cloud resource, container, IaC stack, environment, CI workflow 또는 별도 deployment pipeline을 만들지 않는다. 기존 FastAPI 프로세스, application-lifetime `httpx.AsyncClient`, Server Session SQLite와 저장소 밖 승격 경로를 그대로 사용한다.
- 이 library Unit의 infrastructure 산출물은 기존 승격 경로가 실행할 U3 검증 순서를 정의한 `cicd-pipeline.md`와 `traceability.json`으로 제한한다.
- U3는 기존 Server Session SQLite에 `ticket_tools_update_v1.pending_update_executions` migration과 actor scope당 active row를 최대 하나로 제한하는 partial unique index만 추가한다. U1·U2 namespace를 수정하거나 credential, Authorization, raw problem detail을 저장하지 않는다.
- startup은 U1 `ticket_tools_state_v1` 확인 → U3 migration과 schema fingerprint 검증 → orphan·terminal row cleanup 및 activation-crash recovery → U3 plugin registration 순서를 차단 조건으로 적용한다. 반복 실행은 idempotent해야 하고 중간 실패는 transaction rollback 후 U3 activation을 중단한다.
- merge 또는 승격 전에는 dependency pin 확인, 기존 전체 pytest, FakeModel/MockTransport 기반 U3 contract·security·restart·concurrency 테스트, 실제 OpenAI·ITSM network 0건, secret·patch·header canary 노출 0건, 변경 application code line coverage 80% 이상을 모두 통과해야 한다.
- 수정 안전성은 exact-old U1 replacement, U3 staged-first publication, old-retire/new-active 단일 transaction, atomic confirm+consume, canonical patch와 `If-Match` 재검증, actor-scoped response-loss locator, one-shot durable refresh reservation을 deterministic counter와 SQLite snapshot으로 입증한다.
- Detail read는 최초 포함 최대 2회와 정확한 retryable outcome·250ms delay·operation deadline을 지키고, PATCH는 기본 1회이며 authoritative no-apply `token_expired` 401에서만 동일 bytes/version으로 최종 1회를 허용한다. Gateway, wrapper, reconciliation은 독자 retry를 하지 않는다.
- Network 차단은 특정 CI provider 방화벽을 가정하지 않고 pytest process의 default-deny fixture와 deliberate bypass probe로 증명한다. 실제 ITSM/OpenAI smoke는 별도 운영 승인과 명시적 credential이 있는 수동 절차로만 수행한다.
- 배포 전략, 환경 승격, production 승인과 rollback 실행은 기존 저장소 밖 절차를 유지한다. U3 rollback은 애플리케이션 버전을 되돌리되 additive update schema와 안전 복구 evidence를 삭제·downgrade하지 않는 방식으로 제한한다.
- 현재 single-process 배포에서는 U1 per-conversation serialization과 SQLite transaction/CAS를 사용한다. 배포가 multi-process 또는 multi-host로 바뀌면 shared lock 또는 동등한 database arbitration을 먼저 설계하고, 그 전에는 U3를 해당 형태로 승격하지 않는다.
- U4는 generated fixture 기반 수정 시나리오에서 기존 ITSM UI와 Assistant를 동일 actor·환경·network·warm-cache 조건으로 각각 유효 3회 측정하고, Assistant median이 더 짧으며 외부 화면 전환이 0회임을 release evidence로 집계한다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
