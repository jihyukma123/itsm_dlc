# U3 Ticket Update 비즈니스 규칙

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`
- `construction/u3-ticket-update/functional-design/functional-design-questions.md`

## Source of Truth

```yaml
rules:
  - id: BR3.1
    statement: 수정 입력은 계약이 허용한 여덟 필드만 받을 수 있다.
    category: validation
    applies_to: TicketPatch
    trigger: ticket_update prepare 또는 revise
    logic: IF 입력에 허용 목록 밖 필드가 있으면 THEN 전체 요청을 거부하고 PATCH를 호출하지 않는다.
    violation_behaviour: public state는 failed, SafeErrorV1 code는 invalid_input으로 반환하고 허용 필드를 안내한다.
    source: FR4.1, AC3.1.1

  - id: BR3.2
    statement: 생략한 필드와 명시적 null을 서로 다른 수정 의도로 보존한다.
    category: constraint
    applies_to: TicketPatch
    trigger: patch 정규화
    logic: IF 필드가 omitted이면 유지하고 IF null이면 권위 계약이 허용하는 clear 값으로 보존한다.
    violation_behaviour: public state는 failed, SafeErrorV1 code는 invalid_input으로 반환하고 의미를 추측하지 않는다.
    source: FR4.2, AC3.1.1

  - id: BR3.3
    statement: 빈 patch와 현재 값에 대한 no-op patch는 실행하지 않는다.
    category: validation
    applies_to: TicketPatch
    trigger: 최신 상세와 patch 비교 완료
    logic: IF 실제 diff가 비어 있으면 THEN pending review를 만들지 않고 PATCH 호출 수를 0으로 유지한다.
    violation_behaviour: public state는 failed, SafeErrorV1 code는 invalid_input으로 반환하고 변경할 값이 없다는 다음 행동을 안내한다.
    source: FR4.5, AC3.1.6

  - id: BR3.4
    statement: review는 최신 상세와 검증된 strong ETag에 기반해야 한다.
    category: constraint
    applies_to: UpdateBaseSnapshot
    trigger: prepare 또는 revise의 review 생성 전
    logic: IF strong quoted-decimal ETag가 없거나 body version과 다르면 THEN snapshot과 review를 만들지 않는다.
    violation_behaviour: upstream_unavailable을 반환하고 PATCH를 금지한다.
    source: FR4.2, AC3.1.2

  - id: BR3.5
    statement: 수정 확인은 사용자, 세션, 대화, operation, 티켓, patch hash와 base version 전체 및 같은 mutation의 active durable 실행 record에 결합한다.
    category: authorization
    applies_to: PendingUpdateMutation
    trigger: review 게시와 confirm
    logic: IF mutation ID, user ID, originating session ID, originating conversation ID, ticket ID, normalized payload hash/patch bytes hash 또는 base version 중 어느 값이라도 현재 capability, U1 pending 또는 U3 active PendingUpdateExecution과 다르면 THEN confirmation을 거부한다.
    violation_behaviour: 기존 pending을 실행하지 않고 새 prepare 또는 review를 요구한다.
    source: FR4.3, FR5.4, AC3.1.3

  - id: BR3.6
    statement: 현재 raw 사용자 turn의 독립 확인 명령만 수정 실행 권한이 된다.
    category: authorization
    applies_to: CurrentTurnEvidence
    trigger: confirm action
    logic: IF 정규화된 전체 turn이 확인 또는 confirm과 정확히 같지 않으면 THEN consume과 PATCH를 금지한다.
    violation_behaviour: needs_explicit_confirmation과 동일 review를 반환한다.
    source: FR4.3, AC3.1.3

  - id: BR3.7
    statement: pending update의 확인과 consume_once는 한 U1 repository transaction으로 최대 한 번만 완료된다.
    category: constraint
    applies_to: PendingUpdateMutation
    trigger: 명시적 확인 검증 성공
    logic: IF full binding 검증, confirmed 표시와 consume_once가 한 U1 repository transaction에서 성공해 ConsumedMutationEvidenceV1을 반환하고 같은 mutation_id의 active PendingUpdateExecution에서 actor·hash·ticket·base version이 일치하면 THEN 저장된 canonical patch bytes와 IfMatchVersion으로 PATCH 실행을 진행하고 ELSE 실행하지 않는다. confirmed는 transaction 내부 중간 상태일 뿐 commit 뒤 관찰 가능하게 남지 않으며 staged row는 exact binding crash recovery로 active 승격을 완료한 뒤에만 재검증 대상이 된다.
    violation_behaviour: invalidated 또는 안전한 실패 결과를 반환한다.
    source: FR4.3, NFR3, AC3.1.3

  - id: BR3.8
    statement: 각 gateway 호출은 확인된 server-only IfMatchVersion으로 PATCH HTTP 시도를 정확히 한 번만 수행한다.
    category: constraint
    applies_to: update execution
    trigger: consume_once 성공
    logic: IF 실행하면 THEN PATCH /api/v2/tickets/{id}에 If-Match를 넣어 최초 gateway 호출을 한 번 수행하고 gateway 내부 retry·sleep·token refresh는 금지한다.
    violation_behaviour: IfMatchVersion이 없으면 실행을 중단한다.
    source: FR4.4, NFR3, AC3.1.4

  - id: BR3.9
    statement: 사용자 operation의 PATCH gateway 호출은 최초 1회와 권위 계약이 미적용을 보장한 401 뒤 추가 1회를 합쳐 최대 2회다.
    category: policy
    applies_to: update authentication recovery
    trigger: 401 token_expired
    logic: IF 첫 PATCH가 401 token_expired이고 미적용 보장이 있으며 refresh budget이 남으면 THEN active execution에 refresh reservation을 durable하게 한 번 소비하고 U1 UpdateCredentialRefreshPortV1을 한 번 호출한 뒤 같은 확인, version과 patch로 gateway를 추가 한 번 호출하고 ELSE ambiguous recovery로 전환한다. Reservation은 reset하지 않고 commit-response loss는 credential generation으로 복구하며 port를 재호출하지 않는다. 401 이외의 status, timeout, transport, conflict 또는 ambiguous 결과에는 추가 PATCH 호출이 0회다.
    violation_behaviour: 갱신 실패 시 미실행과 재로그인을 안내하고 새 PATCH를 보내지 않는다.
    source: FR5.3, AC4.1.3, AC4.1.4

  - id: BR3.10
    statement: 충돌이나 결과 불명확 상태에서는 PATCH를 자동 재전송하지 않는다.
    category: policy
    applies_to: update recovery
    trigger: 412, 428, timeout, transport 오류 또는 적용 여부가 불명확한 응답
    logic: IF 해당 상태가 발생하면 THEN PATCH 시도를 종료하고 최신 상세 조회로 전환한다.
    violation_behaviour: conflict 또는 ambiguous를 성공이 아닌 상태로 유지한다.
    source: FR4.4, FR6.4, AC3.1.5, AC4.1.6

  - id: BR3.11
    statement: 충돌·불명확 결과는 최신 권위 상세로 적용 여부와 남은 diff를 판정한다.
    category: calculation
    applies_to: update reconciliation
    trigger: BR3.10의 최신 상세 조회 성공
    logic: IF 모든 기대 변경과 version 증가가 확인되면 성공 ELSE 기존 pending을 폐기하고 실제 남은 diff와 새 version으로 새 review를 요구한다.
    violation_behaviour: 최신 상세도 읽을 수 없으면 판정 불가 상태로 유지하고 자동 PATCH를 금지한다.
    source: FR6.4, AC3.1.5, AC4.1.6

  - id: BR3.12
    statement: 수정 성공은 티켓 ID, 실제 적용 변경 목록과 증가한 새 version이 모두 있을 때만 성립한다.
    category: validation
    applies_to: SafeUpdateResult
    trigger: PATCH 응답 또는 reconciliation
    logic: IF 세 성공 증거가 모두 있고 new_version이 base_version보다 크면 THEN succeeded ELSE 성공 표시를 금지한다.
    violation_behaviour: conflict, ambiguous 또는 failed 상태를 반환한다.
    source: FR4.4, NFR7, AC3.1.4

  - id: BR3.13
    statement: 권한 또는 binding 수명주기가 바뀌면 기존 update confirmation을 재사용하지 않는다.
    category: authorization
    applies_to: PendingUpdateMutation
    trigger: 사용자 전환, 로그아웃, 대화 초기화, session 만료, ticket·patch·version 변경 또는 15분 만료
    logic: IF 사건이 발생하면 THEN 관련 pending을 idempotent하게 invalidated 또는 expired로 전환한다.
    violation_behaviour: PATCH를 0회 유지하고 새 prepare를 요구한다.
    source: FR5.4, AC3.1.6, AC4.1.4, AC4.1.5

  - id: BR3.14
    statement: 비밀과 원본 외부 오류는 모델, 도구 결과, 표시와 로그에 노출하지 않는다.
    category: authorization
    applies_to: all U3 boundaries
    trigger: 입력, HTTP 호출, 오류 mapping, 결과와 presentation 생성
    logic: IF 외부 값이 경계를 통과하면 THEN allowlist 업무 data 또는 SafeErrorV1으로만 변환하고 credential, Authorization, raw header, problem detail, exception을 제거한다.
    violation_behaviour: fail closed하고 안전한 오류만 반환한다.
    source: FR1.3, FR1.5, FR6.1, NFR1, AC4.1.2, AC4.1.6

  - id: BR3.15
    statement: 실제 수정 권한과 major 선언 가능 여부는 ITSM API가 최종 판정한다.
    category: authorization
    applies_to: update execution
    trigger: PATCH 응답
    logic: IF ITSM이 permission_denied를 반환하면 THEN 로컬 예외나 권한 확대 없이 그대로 안전 mapping한다.
    violation_behaviour: permission_denied와 다음 행동을 반환한다.
    source: FR4.5, NFR2, AC3.1.4

  - id: BR3.16
    statement: U3 plugin과 presentation은 U1 registry와 기존 chat fallback 계약을 통해서만 조립한다.
    category: constraint
    applies_to: TicketUpdatePluginV1 and update presentation mapper
    trigger: 애플리케이션 조립과 결과 표시
    logic: IF U3를 등록하면 THEN tool_name은 ticket_update이고 기존 reply는 유지하며 선택적 TicketPresentationV1만 추가한다.
    violation_behaviour: 중복 이름, 알 수 없는 version 또는 kind는 fail closed하고 text fallback을 유지한다.
    source: FR1.1, FR1.2, FR7.1, FR7.3, AC5.1.4

  - id: BR3.17
    statement: U3 계약과 공격·복구 경로는 실제 OpenAI·ITSM 호출 없이 자동 검증한다.
    category: policy
    applies_to: U3 tests
    trigger: U3 구현 직후와 전체 회귀
    logic: IF 테스트하면 THEN FakeModel과 httpx.MockTransport를 사용하고 예상하지 않은 network를 차단한다.
    violation_behaviour: 외부 호출 또는 비밀 canary 노출이 있으면 테스트를 실패시킨다.
    source: FR7.4, NFR5, NFR6, AC5.1.2, AC5.1.4

  - id: BR3.18
    statement: 새 update review는 실행 record와 U1 pending을 crash-safe 순서로 게시하고 같은 operation의 이전 review를 원자적으로 교체한다.
    category: constraint
    applies_to: PendingUpdateExecution and PendingUpdateMutation
    trigger: prepare 또는 유효한 revise
    logic: IF 새 review를 게시하면 THEN 먼저 새 mutation_id의 실행 record를 staged로 저장하고, prepare는 expected_old=null, revise는 화면의 정확한 expected_old_mutation_id를 전달해 U1 replace_update_pending을 호출한 뒤, 한 U3 transaction에서 exact old active execution을 CAS-retire하고 exact binding과 expected_status=staged인 new execution을 active로 승격한다. Actor scope active partial unique index가 active row를 최대 하나로 제한한다. validation·U1 replacement 실패는 old/new U1 row를 모두 바꾸지 않고 이전 review를 유지하며, U1 commit 뒤 activation 전 crash는 같은 retire/promote transaction으로만 복구한다.
    violation_behaviour: stale expected-old, actor scope 불일치 또는 activation binding 불일치이면 fail closed하고 새 staged row를 retired 또는 orphan cleanup 처리하며 이전 review를 광범위 selector로 무효화하지 않는다.
    source: FR4.3, FR5.4, AC3.1.3, AC3.1.6

  - id: BR3.19
    statement: U3 execution storage는 소유권, migration 순서와 lifecycle cleanup 계약을 보존한다.
    category: constraint
    applies_to: PendingUpdateExecutionRepositoryV1
    trigger: U3 plugin activation, startup, repository access 또는 lifecycle event
    logic: IF U3를 활성화하면 THEN U1 ticket_tools_state_v1 뒤에 U3 ticket_tools_update_v1 migration을 적용하고, unmatched·expired staged row와 terminal 또는 missing U1 pending의 row를 비권한 상태로 멱등 retire/cleanup한다.
    violation_behaviour: migration이 준비되지 않았거나 binding을 확인할 수 없으면 plugin activation 또는 PATCH를 fail closed하고 U1·U2 namespace는 수정하지 않는다.
    source: FR4.3, FR5.4, NFR3, AC3.1.3, AC3.1.6, AC5.1.4

  - id: BR3.20
    statement: review 게시 응답 유실은 같은 actor와 ticket의 active execution을 안전하게 재발견해 사용자가 pending_ref를 복구할 수 있어야 한다.
    category: constraint
    applies_to: PendingUpdateExecutionRepositoryV1
    trigger: prepare 응답 유실 뒤 같은 actor와 ticket으로 다시 접근
    logic: IF U3 내부 exact actor/session/conversation/ticket locator가 active execution을 찾고 U1 pending의 mutation·actor·operation·ticket·patch hash·base version이 모두 일치하면 THEN 그 pending_ref를 복구하고 현재 version이 같을 때 같은 review_required를 재구성한다. version이 달라 review를 안전하게 재구성할 수 없으면 같은 pending_ref와 conflict를 반환해 revise 또는 cancel을 요구하며 PATCH는 호출하지 않는다.
    violation_behaviour: row가 없거나 staged·retired·expired이거나 U1 binding이 불일치하면 다른 row를 추측하지 않고 fail closed하며 cleanup한다.
    source: FR4.3, FR5.4, NFR3, AC3.1.3, AC3.1.6
```

## Rules Summary

| Rule | 핵심 결정 | 실패 시 행동 |
|---|---|---|
| BR3.1~BR3.3 | 허용 patch, omit/null, 실제 diff를 검증 | `failed` + `invalid_input`, PATCH 없이 입력 수정 안내 |
| BR3.4 | 최신 version과 강한 ETag를 함께 검증 | review와 PATCH 금지 |
| BR3.5~BR3.7 | 전체 binding, 현재 turn, 일회성 소비를 모두 요구 | 재확인 또는 invalidated |
| BR3.8~BR3.12 | 정확한 `If-Match`, 제한된 인증 복구, 무자동 재전송, 권위 재조정 | conflict·ambiguous를 성공으로 표시하지 않음 |
| BR3.13 | lifecycle·대상·값·version 변화에 확인 폐기 | 새 prepare 요구 |
| BR3.14~BR3.15 | 비밀 비노출과 ITSM 권한 판정 유지 | fail closed 또는 안전한 permission 오류 |
| BR3.16~BR3.17 | 기존 조립·표시 호환과 외부 호출 없는 검증 | fallback 또는 테스트 실패 |
| BR3.18 | 실행 payload를 staged 저장하고 exact-old U1 replacement 뒤 expected-state CAS로 활성화 | 이전 review 유지 또는 exact-binding recovery·orphan cleanup |
| BR3.19 | U3 migration 순서와 접근·startup·lifecycle cleanup 보존 | fail closed, 멱등 retire/cleanup |
| BR3.20 | 응답 유실 뒤 exact actor·ticket active review만 재발견 | pending_ref 복구 또는 fail closed |

## Assumptions & Open Questions

None.
