# U1 Ticket Read Walking Skeleton 기능 설계 질문

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`

승인된 상위 산출물이 조회 흐름, cursor 결합, 오류·재시도, 위임 인증, 표시 계약과 공통 confirmation 저장소의 구조를 이미 확정했다. 아래 질문은 `PendingTicketMutationV1`의 `expires_at`과 같은 대화 안의 동시 보류 상태가 아직 정하지 않은 수명주기 규칙이라서 묻는다.

## Q1. [제품·보안 책임자] 보류 중인 등록·수정 확인의 동시성 및 만료

같은 사용자·세션·대화에서 등록 또는 수정 확인이 여러 개 준비될 때, 오래된 확인을 얼마나 유지할까요?

- A. 작업 종류별 최신 1개만 유지하고, 새 요약이 만들어지면 같은 종류의 이전 확인을 무효화한다. 각 확인은 15분 또는 사용자·세션·대화·대상·본문·version 변경 중 먼저 발생한 시점에 만료한다. (Recommended)
- B. 여러 확인을 `pending_ref`별로 동시에 유지하고, 각각 15분 또는 기존 lifecycle 무효화 조건까지 사용할 수 있게 한다.
- C. 등록·수정을 합쳐 대화당 최신 확인 1개만 유지하고, 새 요약이 만들어지면 다른 종류의 확인도 함께 무효화한다.
- X. Other (please specify)

[Answer]: A. 작업 종류별 최신 1개만 유지하고, 새 요약이 만들어지면 같은 종류의 이전 확인을 무효화한다. 각 확인은 15분 또는 사용자·세션·대화·대상·본문·version 변경 중 먼저 발생한 시점에 만료한다.

## Q2. [제품·보안 책임자] 서버 세션 만료 기준

현재 서버 세션은 별도 만료 시각을 저장하지 않습니다. 만료 후 권한과 보류 상태를 확실히 폐기하려면 세션 수명과 갱신 규칙을 확정해야 합니다.

- A. 생성 시점부터 8시간인 절대 만료를 적용하고 활동이나 위임 토큰 갱신으로 연장하지 않는다. 기존 row는 `created_at + 8시간`으로 backfill하여 이미 지난 세션은 다음 요청에서 즉시 정리한다. (Recommended)
- B. 마지막 인증된 요청부터 8시간인 유휴 만료를 적용하고 보호 API 사용 때마다 만료 시각을 연장한다.
- C. 서버 세션 만료를 현재 위임 토큰 만료와 같게 두고, 토큰이 갱신될 때 세션도 연장한다.
- X. Other (please specify)

[Answer]: A. 생성 시점부터 8시간인 절대 만료를 적용하고 활동이나 위임 토큰 갱신으로 연장하지 않는다. 기존 row는 `created_at + 8시간`으로 backfill하여 이미 지난 세션은 다음 요청에서 즉시 정리한다.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- 승인된 상위 설계대로 U1은 `ticket_read` 목록·검색·상세 walking skeleton과 공통 capability, gateway, 안전 오류, cursor, confirmation 저장소, tool·presentation 확장 계약을 제공한다.
- 같은 사용자·세션·대화에서는 등록과 수정 작업 종류별로 최신 확인 하나만 유지한다.
- 같은 종류의 새 요약이 만들어지면 이전 확인을 무효화한다.
- 각 확인은 15분 또는 사용자·세션·대화·대상·본문·version 변경 중 먼저 발생한 시점에 만료한다.
- 서버 세션은 생성 시점부터 8시간인 절대 만료를 적용하며 활동이나 위임 토큰 갱신으로 연장하지 않는다.
- 기존 세션 row는 `created_at + 8시간`으로 만료 시각을 backfill하고, 이미 지난 row는 다음 보호 요청에서 안전 상태 정리 후 폐기한다.
- 갱신된 상위 계약에 맞춰 U1의 confirmation 저장소는 `confirm`과 `consume_once`를 분리하고, `consume_once`는 `mutation_id`와 `confirmed_at`만 담은 `ConsumedMutationEvidenceV1`을 한 번 반환한다.
- `ConsumedMutationEvidenceV1`은 U2가 동일 create attempt에 확인 증거를 결합하는 입력일 뿐 POST 실행 권한 자체는 아니며, U2의 durable ledger와 CAS claim은 U1 범위 밖에 둔다.
- 갱신된 C-02에 맞춰 U1 confirmation 저장소는 update prepare·revise에서 예상한 이전 mutation만 같은 작업 종류 안에서 원자적으로 교체하고, U3의 staged execution 저장소나 transaction을 직접 소유하지 않는다.
- U1의 `CredentialRefreshPortV1`은 U2가 durable하게 소비한 일회성 refresh reservation과 남은 deadline을 입력으로 받아 token exchange를 최대 한 번 수행하고, 새 credential을 기존 서버 세션에 원자적으로 반영한 뒤 같은 사용자·세션·대화에 결합된 capability만 반환한다.
- refresh 도중 실패하거나 commit 뒤 응답 전에 중단되어도 같은 create attempt에서 두 번째 token exchange를 허용하지 않는다.
- U1의 공통 저장 계약은 Server Session SQLite의 `ticket_tools_state_v1`과 Agents SDK history SQLite의 `ticket_tools_history_v1`로 분리하며, U2·U3는 이 namespace를 수정하지 않는다.
- 사용자 전환·로그아웃·대화 초기화·세션 만료에서는 U1의 revocable pending/cursor/presentation/history 상태를 정리하되 U2의 durable create-attempt ledger는 보존한다.
- Runner와 세션 만료 정리는 같은 conversation lock을 사용하고, Runner 직후 응답·presentation을 결정하기 전에 persisted session expiry를 다시 검사한다.
- 기존 산출물은 갱신된 상위 계약에 맞게 수정하고, `components.md` 출처 누락과 session cleanup 표의 모호한 `expires_at` 표기를 각각 보완한다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
