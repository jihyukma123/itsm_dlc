# U3 Ticket Update 기능 설계 질문

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`

승인된 상위 산출물이 수정 허용 필드, omit/null 의미, 최신 version·ETag, 현재 turn의 명시적 확인, `If-Match`, 충돌·불명확 결과 복구, lifecycle 무효화와 표시 계약을 이미 구현 가능한 수준으로 확정했다. U3 기능 설계에서 추가로 판단받아야 할 미해결 항목은 없다.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U3는 U1의 요청 범위 capability, `read_for_update` 상세 projection, 한 번만 호출하는 update gateway, `PendingUpdateMutationV1` repository, tool registry와 presentation mapper registry를 사용한다. U1 pending mutation의 원자적 `replace_update_pending(expected_old, replacement)` 계약을 준수하고, U2 create ledger나 U1 공통 migration·registry 구현은 변경하지 않는다.
- `ticket_update`의 `prepare`와 `revise`는 `title`, `description`, `component_id`, `model`, `impact_level`, `urgency`, `impact_note`, `is_major`만 받는다. 생략은 유지, 명시적 `null`은 계약상 clear로 구분하고, 금지 필드·빈 patch·실제 차이가 없는 patch는 PATCH 없이 안전하게 거부한다.
- review 생성 전 현재 사용자 위임 capability로 최신 상세를 읽는다. U1이 public `version`과 정확히 일치하는 strong quoted-decimal ETag에서 만든 server-only `IfMatchVersion`만 사용하며, ETag가 없거나 weak·비정수·불일치이면 review와 PATCH를 만들지 않고 안전 오류로 종료한다.
- review에는 대상 티켓, 변경 필드별 이전 값·새 값, base version과 `확인`·`수정`·`취소` 선택을 표시한다. U1 pending update는 사용자·세션·대화·operation·ticket ID·정규화 patch hash·base version에 결합하고 공통 15분 만료 및 lifecycle 무효화 규칙을 따른다.
- `revise`는 새 patch의 검증, 최신 상세 재조회와 실제 diff 계산이 성공한 뒤에만 정확한 이전 pending을 원자적으로 새 pending으로 교체하고 새 review를 게시한다. 잘못된 수정 요청이나 stale expected-old binding은 기존의 유효한 review를 파괴하지 않는다.
- U3는 `ticket_tools_update_v1.pending_update_executions` 실행 저장소를 소유한다. `PendingUpdateExecutionV1`은 mutation·사용자·세션·대화·ticket·base version·serialization version·canonical patch bytes/hash·server-only `IfMatchVersion`·상태와 생성/만료/폐기 시각을 보존하며, 상태는 `staged → active → retired`로만 전이한다.
- review 게시 순서는 U3 execution을 `staged`로 저장하고, U1 pending을 exact-old 조건으로 교체한 뒤, U3 execution을 `active`로 승격하는 순서다. 중간 실패는 권한을 남기지 않도록 롤백·폐기하고, 시작·접근·lifecycle 경계에서 만료·고아 execution을 멱등 정리한다.
- `confirm`은 서버가 보존한 현재 raw 사용자 turn이 독립 명령 `확인` 또는 `confirm`과 정확히 일치하고, U1의 active pending과 U3의 active execution이 mutation·사용자·세션·대화·ticket·patch hash·base version에서 정확히 일치할 때만 U1의 confirm·`consume_once`를 거친다. tool argument, 과거 turn, quoted text, 추가 문구는 실행 권한이 아니다.
- PATCH는 확인된 server-only `IfMatchVersion`을 그대로 `If-Match`에 넣어 정확히 한 번만 호출한다. gateway와 tool wrapper는 retry·sleep·독자적 token refresh를 하지 않으며, 권한과 major 선언 가능 여부는 ITSM API가 판정한다.
- 401은 authoritative 계약이 미적용을 보장하는 경우에만 기존 한 번의 credential refresh budget으로 같은 확인·version·patch를 한 번 계속할 수 있다. 그 밖의 401, 412, 428, timeout·transport와 결과 불명확에서는 PATCH를 자동 재전송하지 않는다.
- 412·428 또는 불명확 결과 뒤에는 최신 상세와 version을 다시 읽는다. 모든 기대 변경과 version 증가가 권위 있는 상세에서 확인될 때만 성공을 표시하고, 미적용·부분 적용·다른 값·판정 불가이면 기존 확인을 폐기한 뒤 남은 실제 diff와 새 base version으로 새 review·명시적 확인을 요구한다.
- 성공은 ticket ID, 실제 적용된 변경 목록, 증가한 새 version이 모두 있을 때만 성립한다. 충돌·불명확·오류를 성공으로 표시하지 않고 credential, Authorization, raw header/problem/exception을 model·result·presentation·로그에 노출하지 않는다.
- 사용자 전환, 로그아웃, 대화 초기화, session 만료 또는 target·patch·version 변경은 update pending authority를 폐기한다. 외부 업무·오류 텍스트는 구조화된 비신뢰 data로 유지하고 기존 text fallback·history correlation·접근성 흐름을 보존한다.
- U3는 `ticket_update` plugin, update presentation mapper, update execution store/migration, patch/version binding과 C-05 검증 증거를 소유한다. U4는 migration order, restart durability, cleanup, tamper/mismatch와 exact-old 경쟁 조건을 검증한다. 설계 추적은 AC3.1.1~AC3.1.6, AC4.1.2~AC4.1.6의 update 경로, AC5.1.2와 AC5.1.4의 update 경로를 포함한다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
