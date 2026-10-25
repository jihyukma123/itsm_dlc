# ITSM 티켓 도구 Bolt 계획

## Sources

- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `inception/refined-mockups/mockups.md`
- `inception/domain-design/components.md`
- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-dependency.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/contract-design/contract-summary.md`
- `inception/practices-discovery/team-practices.md`
- `inception/delivery-planning/delivery-planning-questions.md`

## Delivery Strategy

Bolt는 한 작업 조각을 Construction 전 단계로 통과시켜 실행·검증 가능한 결과로 끝내는 한 번의 전달 단위다. 이 계획은 Unit당 하나의 Bolt를 직렬 실행하며, walking skeleton—핵심 통합 지점을 관통하는 가장 작은 실행 가능 end-to-end 조각—인 U1을 먼저 완성한다.

| 순서 | Bolt | 포함 Unit | 선행 조건 | Walking skeleton | 완료 체크포인트 |
|---:|---|---|---|---|---|
| 1 | B1 Read Skeleton | U1 `u1-ticket-read-skeleton` | 없음 | 예 | 사람 승인 |
| 2 | B2 Ticket Write | U2 `u2-ticket-write` | B1 완료·승인 | 아니요 | 사람 승인 |
| 3 | B3 Ticket Update | U3 `u3-ticket-update` | B1 완료·승인, 계획상 B2 완료·승인 | 아니요 | 사람 승인 |
| 4 | B4 Release Assurance | U4 `u4-release-assurance` | B1~B3 완료·승인 | 아니요 | 사람 승인 |

U2와 U3 사이에 기술적 DAG edge는 없지만, 팀이 확정한 공통 안전 경계 → 조회 → 등록 → 수정 순서와 단일 주요 능력 흐름을 지키기 위해 B2 뒤 B3를 계획한다. runtime은 기록된 `unit-major`·`serial` 설정을 사용한다.

## Cross-Bolt Contract Closure

Contract Design에서 승인과 함께 수용된 R-12~R-18은 구현 면제가 아니다. 아래 결정과 검증 가능한 계약 변경이 완료되지 않으면 해당 Bolt의 애플리케이션 코드 구현을 시작하지 않는다.

| 선행조건 | 닫아야 할 위험 | 결정 시점 | 완료 증거 |
|---|---|---|---|
| CP-01 | R-16: U3 durable update-execution 저장소와 migration 소유권이 상위 Unit·컴포넌트 경계와 충돌 | B1 공통 persistence 경계를 고정하기 전 | `unit-of-work.md`, `components.md`, C-02/C-05 중 하나의 일관된 소유권과 migration 책임; 관련 schema test 계획 |
| CP-02 | R-17: `retire_update_executions` 호출 순서와 실패 의미가 없음 | B2 lifecycle 구현 전, 늦어도 B3 설계 시작 전 | cancel·revise·expire·session cleanup별 선행/후행 순서, transaction 경계, retry/compensation, 부분 실패 상태를 포함한 상태 전이·테스트 |
| CP-03 | R-18: breaking provider/schema 변경이 C-02 V1로 남음 | B1이 C-02 소비 인터페이스를 구현하기 전 | 미배포 V1 전체 동시 재기준화 또는 새 version/cutover 중 한 선택과 모든 consumer·producer 전환 계획 |
| CP-04 | R-12~R-15: create reconciliation·lookup·ledger 종결·claim 원자성 공백 | B2 POST 경로 구현 전 | 아래 B2 Definition of Done과 계약 테스트가 동일한 단일 정책을 증명 |

CP-01~CP-03의 선택이 기존 승인 산출물을 바꾸면 영향받는 상위 산출물과 Contract Design을 먼저 갱신한다. 선택되지 않은 대안은 구현자가 임의로 가정하지 않는다.

## B1 — Read Skeleton

- **Included Unit:** U1 `u1-ticket-read-skeleton`
- **Stories:** US1.1, US1.2, US4.1의 공통 session/capability/error 기반, US5.1의 read 계약·network 차단
- **Definition of Done:**
  - CP-01과 CP-03을 닫아 공통 persistence 및 C-02 소비 경계가 상위 Unit·컴포넌트 소유권과 일치한다.
  - 기존 서버 세션에서 현재 사용자를 고정한 요청 범위 capability를 만든다.
  - 기존 Agent·Runner에 `ticket_read` function tool을 연결한다.
  - 사용자 위임 token으로 ITSM API v2 목록·검색·상세를 호출하고 allowlist 결과만 반환한다.
  - raw cursor 대신 user/session/conversation/query-bound continuation reference를 사용한다.
  - 공통 pending-mutation repository, tool/presentation registry, history companion 계약을 완성한다.
  - 첫 체크포인트 전에 coverage 실행 의존성과 재현 가능한 설정을 추가해 승인된 검증 명령을 실행 가능하게 한다.
  - FakeModel·MockTransport 통합 경로와 관련 기존 session/chat/UI 회귀 subset이 통과한다.
  - credential·원본 오류·악의적 외부 text가 모델 입력, 결과, 로그, HTTP 오류에 노출되지 않는다.
- **Confidence hypothesis:** 서버 세션 → function tool → 사용자 위임 HTTP → 안전한 결과 → 기존 대화 표시의 전체 경로가 새 서비스 없이 동작하면, U2·U3가 같은 보안·transport·registry 경계를 안전하게 확장할 수 있다.
- **Expected demo:** 생성형 fixture로 목록 검색, continuation, ID 상세와 비가시성 비구분 404를 실행하고, FakeModel tool loop와 MockTransport 요청에서 delegated bearer 사용 및 실제 network 0건을 보인다.
- **Checkpoint evidence:** 승인된 Construction verification command, U1 소유 계층 테스트, read 통합·회귀 subset 결과.

## B2 — Ticket Write

- **Included Unit:** U2 `u2-ticket-write`
- **Stories:** US2.1, US4.1의 create 인증·confirmation·lifecycle, US5.1의 create 계약·공격 경로
- **Definition of Done:**
  - CP-02와 CP-04를 닫아 create/update 공통 lifecycle 순서와 U2의 단일 재시도·원장 정책을 구현 전에 고정한다.
  - 등록 허용 필드, catalog 관계, timezone 있는 발생 시각과 명시적 “지금”을 검증한다.
  - 현재 raw 사용자 turn이 독립된 `확인` 또는 `confirm`일 때만 POST를 허용한다.
  - canonical bytes·serialization version·hash·예측 불가능한 Idempotency-Key를 U1 pending review 게시 전에 durable ledger의 `prepared` 상태로 저장한다.
  - U1 `consume_once`의 mutation ID·확인 시각을 같은 create attempt에 idempotent하게 결합하고, 증거 결합과 U2 CAS claim 없이는 POST를 0회로 유지한다.
  - CAS claim의 `claim_id`, `claim_deadline_at`, `status=in_flight`, `attempt_count + 1`을 하나의 SQLite transaction에서 함께 commit한 뒤에만 POST를 시작한다.
  - cancel은 이전 attempt를 terminal `cancelled`, revise는 terminal `superseded`로 CAS 전환하고 둘 다 최소 retention 동안 보존한다. revise는 새 bytes·key·attempt와 새 review를 만든다.
  - ITSM v2에 idempotency-key 결과 조회 operation이 없으면 조회 가능 분기를 구현하지 않는다. 첫 결과가 불명확하면 같은 key·byte-identical body와 남은 전역 예산으로 마지막 재시도하고, 두 번째 결과도 불명확하면 terminal `ambiguous`로 종료한다.
  - 계약·코드 근거가 실제 결과 조회 operation을 제공할 때만 typed port·endpoint·입출력·오류 의미를 먼저 추가하고 조회 우선 경로를 활성화한다.
  - `retryable_after_reconcile`과 `retryable_no_apply`를 포함한 모든 원인이 하나의 `attempt_count`를 공유하며 실제 POST는 최초 포함 최대 2회다.
  - `ticket_write` plugin과 create presentation mapper를 U1 registry에 등록한다.
  - create 소유 계층 테스트와 관련 통합·회귀 subset이 통과하며 실제 OpenAI·ITSM 호출은 0건이다.
- **Confidence hypothesis:** 명시적 확인과 durable idempotency evidence가 process/session lifecycle을 넘어 유지되면, 중복 티켓 없이 안전한 등록을 제공할 수 있다.
- **Expected demo:** ledger-first prepare → review → 독립 확인 → evidence 결합·원자적 CAS claim → POST 성공, 동일 key 재생, 조회 operation 부재에서의 마지막 same-key/same-bytes 재시도와 terminal `ambiguous`, active claim 비탈취, crash 지점 복구, cancel·revise 원장 종결을 FakeModel·MockTransport와 fake clock으로 보인다.
- **Checkpoint evidence:** 승인된 Construction verification command, U2 계층·등록 통합·관련 lifecycle 회귀 subset 결과.

## B3 — Ticket Update

- **Included Unit:** U3 `u3-ticket-update`
- **Stories:** US3.1, US4.1의 update 인증·충돌·confirmation·lifecycle, US5.1의 update 계약·공격 경로
- **Definition of Done:**
  - CP-01~CP-03의 결정을 U3 구현에 적용하고, 저장소·migration·C-02 version·retirement lifecycle이 갱신된 상위 계약과 일치한다.
  - 계약상 허용된 여덟 필드만 처리하고 omitted/null/no-op을 구분한다.
  - 최신 상세의 강한 quoted-decimal ETag가 public version과 일치할 때만 server-only `If-Match`를 만든다.
  - 변경 전후와 base version을 검토로 제시하고 독립 확인 전 PATCH를 호출하지 않는다.
  - 412·428 또는 ambiguous 결과에서 PATCH를 자동 재전송하지 않고 최신 상세와 새 확인으로 복구한다.
  - cancel·revise·expire·session cleanup에서 update execution retirement의 순서, transaction 경계, 실패 후 상태와 재시도/compensation을 계약대로 구현한다.
  - `ticket_update` plugin과 update presentation mapper를 U1 registry에 등록한다.
  - update 소유 계층 테스트와 관련 통합·회귀 subset이 통과하며 실제 OpenAI·ITSM 호출은 0건이다.
- **Confidence hypothesis:** 확인된 version과 실제 wire `If-Match`가 일치하고 충돌 시 자동 덮어쓰기가 없으면, 사용자의 변경을 최신 ITSM 상태를 훼손하지 않고 적용할 수 있다.
- **Expected demo:** 허용 patch 성공과 version 증가, no-op 차단, invalid ETag 차단, 412 충돌 뒤 최신 상세와 재확인 흐름을 보인다.
- **Checkpoint evidence:** 승인된 Construction verification command, U3 계층·수정 통합·관련 lifecycle 회귀 subset 결과.

## B4 — Release Assurance

- **Included Unit:** U4 `u4-release-assurance`
- **Stories:** US4.1 전체 cross-tool 회귀, US5.1 전체 출시·문서·성과 검증
- **Definition of Done:**
  - 기존 Agent에 `ticket_read`, `ticket_write`, `ticket_update` 정확히 세 도구만 노출한다.
  - 기존 사용자 전환, 로그인·로그아웃, session, 대화 이력, 화면/API, model·reasoning·tracing 설정 회귀가 0건이다.
  - 전체 기존·신규 pytest가 통과하고 변경 application code line coverage가 80% 이상이다.
  - 자동화 중 실제 OpenAI·ITSM network 호출과 비밀 canary 노출이 0건이다.
  - README에 기능, 설정, 실행, 테스트·coverage, 보안 경계와 명시적 실제 API smoke 절차를 반영한다.
  - NFR8 측정 절차와 기록 형식이 재현 가능하다.
  - CP-01~CP-04의 소유권, lifecycle, version/cutover 및 create safety 결정이 실제 조립 경로와 통합 계약 테스트에서 함께 통과한다.
- **Confidence hypothesis:** 세 도구의 계약·lifecycle·보안·회귀 증거가 하나의 전체 검증에서 동시에 통과하면 기존 배포 경로에 안전하게 인계할 수 있다.
- **Expected demo:** 최종 tool registry, 재시작 뒤 presentation history 복원, 사용자 전환 cleanup, full suite·coverage·network 차단·README 명령의 결과를 제시한다.
- **Checkpoint evidence:** 승인된 Construction verification command의 전체 결과와 README 재현 확인.

## Dependency and Traceability Check

- DAG `U1 → U2`, `U1 → U3`, `U1/U2/U3 → U4`를 위반하지 않는다.
- U1: US1.1, US1.2 및 cross-cutting US4.1/US5.1 일부.
- U2: US2.1 및 cross-cutting US4.1/US5.1 일부.
- U3: US3.1 및 cross-cutting US4.1/US5.1 일부.
- U4: US4.1·US5.1의 최종 통합 판정.
- 계획에 배정되지 않은 Unit 또는 Story는 없다.
- CP-01~CP-04는 새 Unit이 아니라 기존 U1~U4의 착수·완료 조건이며, DAG를 우회하지 않는다.

## Assumptions & Open Questions

- Contract Design R-12~R-18은 사람이 승인한 열린 위험이며 CP-01~CP-04 및 각 Bolt의 checkpoint evidence로 추적한다. 새로운 외부 결과 조회 API가 확인되지 않는 한 문서화된 ITSM v2 operation만 사용한다.
- CP-01~CP-03은 현재 선택이 미정이다. Functional Design과 Code Generation이 이를 암묵적으로 결정하지 않으며, 영향받는 상위 산출물을 먼저 정합화한 뒤 구현한다.
