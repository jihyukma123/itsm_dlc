# Contract Design 질문

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-dependency.md`
- `inception/domain-design/components.md`
- `inception/requirements-analysis/requirements.md`
- `docs/itsm/integration-guide.md`
- `docs/itsm/openapi.json`

## Q1. 외부에 노출되는 API 계약

이번 기능이 외부 소비자에게 제공할 HTTP 계약 범위를 어떻게 고정할까요?

- A. 기존 chat API를 그대로 유지하고 선택적 `TicketPresentationV1` metadata만 하위 호환으로 추가한다. 새 티켓 전용 endpoint는 만들지 않으며 ITSM v2는 outbound provider 계약으로만 다룬다. (Recommended)
- B. 기존 chat API와 함께 Assistant 전용 티켓 REST endpoint를 새로 만든다.
- C. 기존 reply 텍스트만 유지하고 구조화된 presentation metadata는 추가하지 않는다.
- D. ITSM API v2를 browser가 직접 호출하게 한다.
- E. 외부 API 계약을 구현 단계에서 결정한다.
- X. Other (please specify)

[Answer]: A. 기존 chat API를 그대로 유지하고 선택적 `TicketPresentationV1` metadata만 하위 호환으로 추가한다. 새 티켓 전용 endpoint는 만들지 않으며 ITSM v2는 outbound provider 계약으로만 다룬다.

## Q2. Unit 사이 연동 방식

U1이 U2·U3에 제공하고 U4가 조립할 내부 계약은 어떤 메커니즘을 사용할까요?

- A. 동기 typed Python port/interface와 versioned shared schema를 사용하고, credential은 직렬화하지 않는 요청 범위 capability로만 전달한다. 새 내부 HTTP·event bus·gRPC는 만들지 않는다. (Recommended)
- B. Unit 사이에 내부 REST API를 만든다.
- C. SQLite table을 각 Unit이 직접 읽고 쓰게 한다.
- D. 비동기 event/message 계약을 추가한다.
- E. 타입 없는 dictionary와 예외 전파로 연결한다.
- X. Other (please specify)

[Answer]: A. 동기 typed Python port/interface와 versioned shared schema를 사용하고, credential은 직렬화하지 않는 요청 범위 capability로만 전달한다. 새 내부 HTTP·event bus·gRPC는 만들지 않는다.

## Q3. 계약 소유권

병렬 구현 충돌을 막기 위해 계약 소유권을 어떻게 나눌까요?

- A. U1이 capability·safe result/error·confirmation repository·tool/presentation registry의 공통 계약을 소유하고, U2는 create DTO·ledger·write extension, U3는 patch DTO·version binding·update extension, U4는 최종 조립·contract test를 소유한다. (Recommended)
- B. U2가 모든 mutation 계약을 소유하고 U3가 이를 확장한다.
- C. U4가 모든 계약을 마지막에 정의한다.
- D. U2와 U3가 공통 계약 파일을 공동 소유한다.
- E. 계약 소유권을 파일별 구현자가 그때 결정한다.
- X. Other (please specify)

[Answer]: A. U1이 capability·safe result/error·confirmation repository·tool/presentation registry의 공통 계약을 소유하고, U2는 create DTO·ledger·write extension, U3는 patch DTO·version binding·update extension, U4는 최종 조립·contract test를 소유한다.

## Q4. Versioning과 breaking-change 정책

공통 schema와 presentation 계약의 변경을 어떻게 관리할까요?

- A. `V1` 계약을 명시하고 additive optional field만 호환 변경으로 허용한다. consumer는 unknown field를 무시하며, 제거·rename·의미 변경은 새 version과 모든 consumer contract test 갱신을 요구한다. ITSM outbound 계약은 문서화된 v2에 고정한다. (Recommended)
- B. version 없이 항상 최신 구조만 사용한다.
- C. 모든 변경마다 새 major version을 만든다.
- D. Python type만 믿고 별도 호환 정책을 두지 않는다.
- E. browser presentation만 versioning하고 내부 계약은 하지 않는다.
- X. Other (please specify)

[Answer]: A. `V1` 계약을 명시하고 additive optional field만 호환 변경으로 허용한다. consumer는 unknown field를 무시하며, 제거·rename·의미 변경은 새 version과 모든 consumer contract test 갱신을 요구한다. ITSM outbound 계약은 문서화된 v2에 고정한다.

## Q5. 오류·timeout·retry 계약

Unit 경계에서 실패 의미와 재시도 책임을 어떻게 고정할까요?

- A. `ItsmGateway`는 allowlist transport 결과만 반환하고 `TicketOperations`가 operation별 정책을 소유한다. 조회는 최대 2회·250ms, 등록은 동일 key·bytes로 최대 2회, 수정은 자동 retry 0회이며 429는 모두 즉시 반환한다. (Recommended)
- B. Gateway가 모든 operation에 같은 3회 exponential retry를 적용한다.
- C. 각 tool wrapper가 독자적으로 재시도한다.
- D. 원본 httpx 예외와 problem detail을 호출자에게 전달한다.
- E. timeout과 retry는 구현자가 endpoint별로 정한다.
- X. Other (please specify)

[Answer]: A. `ItsmGateway`는 allowlist transport 결과만 반환하고 `TicketOperations`가 operation별 정책을 소유한다. 조회는 최대 2회·250ms, 등록은 동일 key·bytes로 최대 2회, 수정은 자동 retry 0회이며 429는 모두 즉시 반환한다.

## Q6. 등록 결과 조회가 실패하거나 계속 불명확한 경우

첫 POST 뒤 결과 조정 조회 자체가 실패하거나 티켓 존재 여부를 확정하지 못했을 때, 남은 한 번의 POST 예산을 어떻게 처리할까요?

- A. 전역 `attempt_count < 2`일 때만 같은 `Idempotency-Key`와 byte-identical body로 마지막 CAS claim·POST를 허용하고, 두 번째 결과도 불명확하면 terminal `ambiguous`로 종료한다. 승인된 AC2.1.5와 24시간 멱등 계약을 함께 충족한다. (Recommended)
- B. 결과 조회가 티켓 미생성을 확정한 경우에만 두 번째 POST를 허용하고, 조회 실패·모호성에서는 fail closed로 추가 POST를 금지한다. 현재 Domain Design 문구를 그대로 유지한다.
- C. 조회 실패·모호성에서는 자동 재시도하지 않고, 사용자가 명시적으로 다시 요청할 때만 같은 key·bytes와 남은 전역 예산으로 마지막 POST를 허용한다.
- D. 결과 조정 조회 없이 첫 불명확 응답 직후 항상 같은 key·bytes로 한 번 재시도한다.
- E. Contract Design에서는 결정하지 않고 구현 단계로 미룬다.
- X. Other (please specify)

[Answer]: A. 전역 `attempt_count < 2`일 때만 같은 `Idempotency-Key`와 byte-identical body로 마지막 CAS claim·POST를 허용하고, 두 번째 결과도 불명확하면 terminal `ambiguous`로 종료한다. 승인된 AC2.1.5와 24시간 멱등 계약을 함께 충족한다.

## Q7. U3 update 실행 자료와 review 교체 계약

U3가 restart 뒤 canonical patch와 검증된 `IfMatchVersion`을 복원하고, 유효한 이전 review를 잃지 않으면서 revise를 게시하려면 계약을 어떻게 확장할까요?

- A. U3가 Server Session SQLite의 별도 `ticket_tools_update_v1.pending_update_executions`를 소유하고, U1은 `PendingMutationRepositoryV1`에 같은 actor scope의 이전 update pending을 새 pending으로 원자적으로 교체하는 `replace_update_pending` operation을 추가한다. U3는 staged-first → U1 replacement → active 승격 순서를 사용하고 U4가 restart·lifecycle·rollback을 검증한다. (Recommended)
- B. U1의 `pending_ticket_mutations`에 canonical patch와 `IfMatchVersion`을 직접 추가해 U1이 update 실행 자료까지 소유한다.
- C. durable 실행 자료를 두지 않고 대화·process memory에서 confirm까지 유지한다.
- D. revise에서 이전 review를 먼저 폐기한 뒤 새 pending을 일반 `put`으로 게시하며, 실패하면 사용자가 처음부터 다시 시작한다.
- E. U3 update를 이번 전달에서 보류한다.
- X. Other (please specify)

[Answer]: A. U3가 Server Session SQLite의 별도 `ticket_tools_update_v1.pending_update_executions`를 소유하고, U1은 `PendingMutationRepositoryV1`에 같은 actor scope의 이전 update pending을 새 pending으로 원자적으로 교체하는 `replace_update_pending` operation을 추가한다. U3는 staged-first → U1 replacement → active 승격 순서를 사용하고 U4가 restart·lifecycle·rollback을 검증한다.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- 외부 HTTP 표면은 기존 chat API를 유지하고, 하위 호환 가능한 선택적 `TicketPresentationV1` metadata만 추가합니다. 새 티켓 전용 endpoint는 만들지 않으며 ITSM API v2는 outbound provider 계약으로 취급합니다.
- Unit 간 연결은 동기 typed Python port/interface와 versioned shared schema를 사용합니다. 사용자 위임 credential은 직렬화하지 않는 요청 범위 capability로만 전달하고 새 내부 HTTP·event bus·gRPC는 도입하지 않습니다.
- U1은 capability, 안전한 result/error, confirmation repository, tool/presentation registry의 공통 계약을 소유합니다. U2는 create DTO·ledger·write extension, U3는 patch DTO·version binding·update extension, U4는 최종 조립과 contract test를 소유합니다.
- 공통 schema와 presentation은 명시적 `V1` 계약을 사용합니다. 선택적 필드 추가만 호환 변경이며 consumer는 알 수 없는 필드를 무시합니다. 제거·이름 변경·의미 변경에는 새 version과 모든 consumer contract test 갱신이 필요하고, ITSM outbound 계약은 문서화된 v2에 고정합니다.
- `ItsmGateway`는 allowlist된 transport 결과만 반환하고 `TicketOperations`가 작업별 timeout/retry 정책을 소유합니다. 조회는 최대 2회·250ms, 등록은 동일 idempotency key와 동일 bytes로 최대 2회, 수정은 자동 retry 0회이며 429는 모두 즉시 반환합니다.
- 등록 결과 조정 조회가 실패하거나 티켓 존재 여부를 확정하지 못해도 전역 `attempt_count < 2`일 때만 같은 idempotency key와 byte-identical body로 마지막 CAS claim·POST를 허용합니다. 두 번째 결과도 불명확하면 추가 POST가 금지된 terminal `ambiguous`로 종료합니다.
- U3의 `TicketOperations` extension은 Server Session SQLite의 별도 `ticket_tools_update_v1.pending_update_executions`를 소유합니다. 이 record는 mutation·actor·ticket·base version·canonical patch bytes/hash·serialization version·U1이 검증한 server-only `IfMatchVersion`·상태·만료 시각을 저장하며 credential은 저장하지 않습니다.
- `PendingMutationRepositoryV1`에는 U1 소유 `replace_update_pending`을 추가합니다. 이 operation은 optional expected-old mutation과 새 `PendingUpdateMutationV1`을 받아 같은 actor scope·update operation·pending 상태를 검증하고, 한 U1 transaction에서 정확히 이전 row만 invalidated로 바꾼 뒤 새 row를 게시합니다. 검증·insert 실패는 두 row 모두 바꾸지 않습니다.
- U3 revise publication은 실행 record를 `staged`로 먼저 저장하고, U1의 원자적 replacement가 성공한 뒤 exact expected-state CAS로 `active` 승격합니다. U1 commit 뒤 U3 승격 전 crash는 mutation·actor·ticket·patch hash·base version이 모두 맞을 때만 복구하며, 그 외 staged row는 실행 권한 없이 정리합니다.
- U1 pending이 cancelled·invalidated·expired·consumed가 되면 연결된 U3 record도 즉시 실행 권한을 잃습니다. U3는 access/startup cleanup으로 unmatched·expired staged record를 제거하고 terminal pending의 active record를 idempotent하게 retired 처리합니다.
- U4 검증에는 U3 record round-trip, server-only field 비노출, replacement rollback, exact-old-row invalidation, concurrent confirm/revise, staged orphan cleanup, activation crash recovery, lifecycle terminal cleanup과 tamper rejection을 추가합니다.
- 선택 사이에 모순이나 추가 확인이 필요한 모호성은 없습니다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
