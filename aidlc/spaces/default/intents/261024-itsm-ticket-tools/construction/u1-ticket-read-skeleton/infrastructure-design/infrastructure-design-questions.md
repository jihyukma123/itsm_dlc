# U1 Ticket Read Skeleton — Infrastructure Design Questions

## Context

U1은 기존 FastAPI 프로세스에 포함되는 library이고, 팀은 이번 기능을 위해 새 CI/CD나 배포 인프라를 만들지 않고 기존 배포 경로를 유지하기로 이미 확정했다. NFR 설계도 새 compute, network, cache, queue, database 또는 cloud resource가 필요하지 않다고 결론냈다. 따라서 이 단계에서 새로 결정할 infrastructure 선택은 없다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U1을 위해 새 cloud resource, container, IaC stack, environment, CI workflow 또는 별도 deployment pipeline을 만들지 않는다. 기존 FastAPI 배포와 두 SQLite database, application-lifetime httpx client를 그대로 사용한다.
- 이 library Unit의 infrastructure 산출물은 기존 promotion 경로가 실행할 검증 순서를 정의한 `cicd-pipeline.md`와 `traceability.json`으로 제한한다.
- merge 또는 승격 전에는 pinned dependency 설치, 기존 전체 pytest, FakeModel/MockTransport 기반 U1 contract·security·concurrency 테스트, 실제 OpenAI·ITSM network 0건, secret canary 0건, 변경 application code line coverage 80% 이상을 모두 통과해야 한다.
- 기존 session database migration rehearsal에서 모든 기존 인증·사용자·권한·위임 credential column과 복원 의미가 유지되고 `session_expires_at`만 additive하게 추가되며 legacy backfill·exact-expiry cleanup이 통과해야 한다.
- conversation lock은 shared contract대로 Runner 호출 전에 획득해 persisted assistant correlation과 presentation commit/readback 이후에 해제해야 하며, 동시 Runner fixture가 metadata mismatch 0건을 검증해야 한다.
- 변경 작업 확인은 `confirm`과 `consume_once`를 분리된 CAS 단계로 검증한다. 소비 성공 시 반환되는 `ConsumedMutationEvidenceV1`은 정확히 `{mutation_id, confirmed_at}` 두 필드의 일회성 증거이며, 이 증거만으로 transport 호출을 허가하지 않는다.
- U1 lifecycle cleanup은 U2의 `ticket_tools_create_v1` ledger row, idempotency key, canonical request bytes를 삭제하거나 다시 쓰지 않아야 한다. U1 consume 뒤 U2 bind 전에 crash가 나면 같은 attempt/key/bytes를 보존하고 새 pending review와 재확인을 요구하며, bind되지 않은 POST는 0건이어야 한다.
- credential이 호출 전 이미 만료됐거나 임박 만료인 경우에도 같은 one-shot refresh budget을 사용해 첫 ticket HTTP 시도 전에 갱신한다. 갱신 실패 시 ticket HTTP 호출은 0건이며, HTTP 401 뒤 갱신도 같은 단일 budget의 두 번째 trigger로 처리한다.
- 실제 ITSM/OpenAI smoke는 기본 자동화에 넣지 않는다. 별도 운영 승인과 명시적 credential이 있는 수동 절차만 허용하며, 자동화 실패를 실제 외부 호출로 우회하지 않는다.
- 배포 전략, rollback, 환경 승격과 production 승인은 기존 저장소 밖의 배포 절차를 그대로 따른다. 이 기능은 그 절차를 추측하거나 새 공급자·AWS resource를 선언하지 않는다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
