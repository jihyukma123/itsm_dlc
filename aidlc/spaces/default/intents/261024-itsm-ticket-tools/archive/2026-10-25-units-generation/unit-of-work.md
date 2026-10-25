# ITSM 티켓 도구 Unit of Work

## Sources

- `inception/domain-design/components.md`
- `inception/domain-design/decisions.md`
- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `inception/units-generation/units-generation-questions.md`
- `aidlc/spaces/default/memory/team.md`
- `aidlc/spaces/default/memory/project.md`

## Unit Definitions

| Unit ID | Directory | Kind | 목적 | Deployment model | Complexity |
|---|---|---|---|---|---|
| U1 | `u1-ticket-read-skeleton` | `library` | 공통 안전·확인 저장소·확장 경계를 연결하고 `ticket_read` 목록·검색·상세를 실행 가능한 walking skeleton으로 제공 | 기존 FastAPI 배포에 embedded | XL |
| U2 | `u2-ticket-write` | `library` | 검증·명시적 확인·durable 멱등성을 갖춘 `ticket_write` 제공 | 기존 FastAPI 배포에 embedded | XL |
| U3 | `u3-ticket-update` | `library` | 최신 version·명시적 확인·낙관적 잠금을 갖춘 `ticket_update` 제공 | 기존 FastAPI 배포에 embedded | L |
| U4 | `u4-release-assurance` | — (omitted; full matrix) | 세 도구의 최종 조립, 전체 회귀·coverage·문서·성과 검증을 출시 가능한 한 묶음으로 완결 | 기존 FastAPI 애플리케이션과 배포 경로를 그대로 사용 | M |

네 Unit은 개발·검증 경계이지 독립 서비스나 프로세스가 아니다. 애플리케이션은 계속 하나의 FastAPI 배포 단위이며, 새 Agent·외부 API·이벤트 버스·배포 인프라를 만들지 않는다.

## U1 — Ticket Read Walking Skeleton

### Definition

- **Unit ID:** U1
- **Directory:** `u1-ticket-read-skeleton`
- **Kind:** `library`
- **Description:** 기존 서버 세션에서 현재 사용자를 복원하고, 요청 범위 ITSM capability를 기존 Agent·Runner context에 연결해 `ticket_read`가 사용자 위임 토큰으로 ITSM API v2 목록·상세를 호출하고 정제된 결과를 기존 대화 흐름에 반환하는 최소 통합 조각이다.

### Boundaries

**In scope**

- `ItsmGateway`의 티켓 목록·상세 typed HTTP adapter와 allowlist 응답·오류 변환
- `IdentitySession`의 현재 사용자 고정, 요청 범위 capability와 최대 한 번 token 갱신
- `TicketOperations`의 읽기 입력 검증, 필터·cursor·limit, timeout·재시도와 안전 projection
- `TicketOperations`가 소유하는 versioned `PendingTicketMutation` 공통 schema, repository·invalidation API와 create/update extension contract
- `AgentConversation`의 기존 Runner context 연결과 `ticket_read` function tool
- `AgentConversation` tool registry의 extension interface와 `ConversationPresentation`의 versioned envelope·kind registry 기반
- `ApplicationLifecycle`의 보호된 chat 순서와 공통 confirmation invalidation operation
- FakeModel과 `httpx.MockTransport`를 사용하는 목록·상세 end-to-end 및 계층별 테스트

**Out of scope**

- 등록별 payload binding·카탈로그 해석·idempotency ledger와 POST 실행
- 수정별 payload/version binding·`If-Match`, PATCH와 충돌 복구
- 최종 전체 회귀·coverage 판정과 README 완결

### Responsibilities and Deliverables

- ITSM v2 목록의 모든 허용 필터, 반복 query parameter, sort, cursor와 limit 1~100을 계약대로 전달한다.
- ID 상세를 불투명 식별자로 취급하고 404에서 실제 부재와 비가시성을 구분하지 않는다.
- 조회는 시도별 `ITSM_TIMEOUT_SECONDS`, 최초 포함 최대 2회와 250ms 고정 지연을 지키고 429에는 기다리거나 재시도하지 않는다.
- 사용자 위임 credential만 티켓 endpoint에 사용하고 원본 problem detail·header·비밀을 상위 경계에 내보내지 않는다.
- 외부 텍스트를 구조화된 비신뢰 data로 반환하고 기존 화면에서 안전하게 표시한다.
- user/session/conversation/operation/payload hash와 선택적 ticket/version을 담는 공통 pending-mutation table을 도입하고, operation별 binding이 별도 모듈에서 이를 확장하도록 한다.
- 공통 논리 저장 계약과 DB별 U1 migration namespace, tool registry extension interface와 presentation envelope/version을 소유해 후속 Unit이 같은 파일의 구조를 추측하거나 다시 정의하지 않게 한다.
- 서버 세션 → function tool → 사용자 위임 HTTP → 정제 결과 → FakeModel/MockTransport의 실제 통합 check를 제공한다.

### Implementation Notes and Constraints

- 기존 앱 단위 `httpx.AsyncClient`, Agent, Runner, SQLiteSession, 고정 model·reasoning과 tracing 비활성 설정을 재사용한다.
- 읽기 skeleton은 이후 U2·U3가 같은 context·gateway·오류 경계를 확장할 수 있는 내부 Python 인터페이스를 제공한다.
- U1의 논리 저장 계약 `ticket_tools_common_v1`은 물리 DB 경계를 넘는 하나의 migration이 아니다. Server Session SQLite에는 U1-owned `ticket_tools_state_v1` namespace로 `pending_ticket_mutations`와 서버 결합 continuation용 `ticket_cursor_bindings`를 만들고, Agents SDK history SQLite에는 U1-owned `ticket_tools_history_v1` namespace로 기존 assistant message와 표시 metadata를 결합하는 `ticket_message_presentations`를 만든다. cursor record는 session·user·conversation lifecycle 또는 upstream invalid cursor에서 폐기하고, presentation record는 대화 이력과 같은 수명으로 보존한다. U2는 Server Session SQLite의 별도 `ticket_tools_create_v1` namespace에 `ticket_create_attempts`만 추가하고 U3는 U1 공통 table을 소비하므로 U2와 U3는 U1의 두 migration namespace를 수정하지 않는다.
- U1은 tool factory를 이름별로 조립하는 registry contract와 presentation kind별 typed mapper contract를 제공한다. U2와 U3는 각자 `ticket_write`·`ticket_update` 및 고유 presentation mapper 모듈만 소유하고 공통 registry 구현을 수정하지 않는다.
- intermediate skeleton은 조회 경로를 검증하는 개발 체크포인트이며, 최종 배포에서는 U2·U3와 함께 정확히 세 도구만 Agent에 노출한다.
- 제품 코드, 지침과 테스트 fixture에 샘플 티켓이나 특정 운영 티켓 ID를 하드코딩하지 않는다.

### Test Obligations

- 목록 전체 필터·반복 parameter·cursor·sort·limit 경계와 빈 결과
- continuation reference의 user/session/conversation/query binding, lifecycle 무효화와 raw upstream cursor 비노출
- 상세 성공·404 안전 응답·허용 필드 projection
- timeout·transport·500/502/503/504 한 번 재시도, 429 무대기, 갱신 포함 최대 2회
- 사용자 위임 token 사용과 service token 티켓 호출 0건
- 공통 pending-mutation schema의 create/update binding round-trip, idempotent invalidation과 operation별 격리
- 별도 tool·presentation extension을 동일 registry에 결합하는 contract test
- assistant message sequence·text hash와 presentation companion metadata의 재시작 복원, 구형 row fallback과 clear ordering
- 비밀 canary와 악의적 외부 텍스트가 모델 결과·로그·HTTP 응답으로 새지 않음
- 기존 로그인·chat·대화 이력·화면 회귀

## U2 — Ticket Write

### Definition

- **Unit ID:** U2
- **Directory:** `u2-ticket-write`
- **Kind:** `library`
- **Description:** U1의 사용자·HTTP·오류 경계 위에 등록 필드·카탈로그·발생 시각 검증, 사용자 확인과 byte-identical 멱등 실행을 추가한다.

### Boundaries

**In scope**

- `TicketCreateIn` 허용 필드와 길이·enum·시간대 검증
- 서비스·컴포넌트·모델의 활성·유일 카탈로그 해석과 서비스 관계 검증
- U1의 공통 confirmation store에 전체 canonical body hash를 결합하는 create-specific `PendingTicketMutation`
- canonical request bytes, serialization version, hash, 예측 불가능한 key와 결과를 보존하는 `TicketCreateAttempt`
- 사용자 확인 이후 `POST /api/v2/tickets`, 멱등 재생과 결과 불명확 조정
- 등록 상태의 `TicketPresentationV1` 표현과 FakeModel/MockTransport 테스트

**Out of scope**

- PATCH 허용 필드, version·`If-Match`와 수정 충돌 처리
- 새 카탈로그 관리 화면 또는 티켓 데이터 복제
- 전체 제품 회귀와 최종 README 판정

### Responsibilities and Deliverables

- 필수·선택 등록 필드만 canonical body에 포함하고 시간대 있는 `occurred_at` 또는 명시적 “지금”만 UTC로 정규화한다.
- 모호하거나 비활성인 카탈로그 값은 추측하지 않고 안전한 후보·수정 방법을 제공한다.
- 전체 본문 요약에 대한 명시적 확인 전에는 POST를 호출하지 않으며 수정·취소·lifecycle 변경은 이전 확인을 폐기한다.
- 확인 직후 HTTP 전송 전에 durable ledger를 저장하고 session·conversation 종료 뒤에도 ambiguous·completed row를 최소 24시간 보존한다.
- 재조정은 저장된 canonical bytes와 같은 Idempotency-Key로만 최초 포함 최대 2회 수행하며 성공을 추측하지 않는다.
- 성공은 생성 또는 `Idempotent-Replayed`로 확인된 티켓 ID가 있을 때만 표시한다.

### Implementation Notes and Constraints

- U1의 `TicketOperations` 공개 경계와 `ItsmGateway` transport를 확장하고 credential을 durable state에 저장하지 않는다.
- U1의 `ticket_tools_state_v1`·`ticket_tools_history_v1` migration을 수정하지 않고 create variant binding을 사용하며, U2는 Server Session SQLite의 durable `TicketCreateAttempt` 전용 `ticket_tools_create_v1` additive migration만 소유한다.
- `ticket_write` tool factory와 create presentation mapper는 U2 전용 모듈로 추가하고 U1 registry contract를 통해 최종 조립한다.
- canonical serialization version을 저장해 재시작 뒤에도 byte-identical body를 재현한다.
- 사용자 전환·로그아웃·대화 초기화는 revocable confirmation만 폐기하고 create-attempt ledger는 보존한다.

### Test Obligations

- 모든 필수·선택 필드, 길이·enum·시간대·카탈로그 경계
- 확인 전 POST 0회, 수정 후 재확인, 취소와 lifecycle 무효화
- 동일 key·동일 bytes의 단일 결과, 다른 body 거부와 멱등 재생
- timeout·401·429·5xx의 허용된 최대 시도와 결과 불명확 상태
- 최소 24시간 ledger 보존, session·conversation 종료 뒤 조정과 비밀 0건

## U3 — Ticket Update

### Definition

- **Unit ID:** U3
- **Directory:** `u3-ticket-update`
- **Kind:** `library`
- **Description:** U1의 상세 조회·사용자·HTTP·오류 경계 위에 계약상 허용된 부분 수정, 변경 확인, `If-Match`와 충돌·불명확 결과 복구를 추가한다.

### Boundaries

**In scope**

- `TicketPatchIn`의 여덟 허용 필드, omit/null 구분과 금지 필드 거부
- 최신 상세·ETag 또는 version 조회와 실제 변경 diff
- U1의 공통 confirmation store에 사용자·session·conversation·ticket·payload·base version을 결합하는 update-specific `PendingTicketMutation`
- 명시적 확인 이후 `PATCH /api/v2/tickets/{id}`와 필수 `If-Match`
- 412·428 충돌과 전송 결과 불명확 상태의 재조회·재확인
- 수정 상태의 `TicketPresentationV1` 표현과 FakeModel/MockTransport 테스트

**Out of scope**

- 서비스, 상태, 담당자·담당 그룹, 전이, 댓글과 첨부파일 변경
- 자동 충돌 덮어쓰기 또는 불명확 PATCH 자동 재전송
- 전체 제품 회귀와 최종 README 판정

### Responsibilities and Deliverables

- 현재 값과 다른 허용 필드만 PATCH body에 넣고 empty/no-op 수정은 호출하지 않는다.
- 변경 전후와 base version을 읽기 쉬운 요약으로 보여주고 명시적 확인 전에 PATCH를 호출하지 않는다.
- 확인된 version을 `If-Match`로 보내고 권한·major 선언 가능 여부는 ITSM 응답에 맡긴다.
- 대상·값·version·사용자·session·conversation이 바뀌면 이전 확인을 폐기한다.
- 412·428 또는 불명확 결과에서 PATCH를 자동 재시도하지 않고 최신 상세로 적용 여부를 판단한 뒤 필요할 때 새 확인을 요구한다.
- 성공은 실제 적용 변경과 새 version이 확인될 때만 표시한다.

### Implementation Notes and Constraints

- U1의 상세 조회 projection은 update 비교에 필요한 ETag/version을 서버 전용 context로 보존하되 모델에 header 전체를 노출하지 않는다.
- U1의 `ticket_tools_state_v1.pending_ticket_mutations` table과 공통 discriminator repository API를 그대로 사용하므로 U2의 create binding이나 `ticket_tools_create_v1` migration에 의존하지 않는다.
- `ticket_update` tool factory와 update presentation mapper는 U3 전용 모듈로 추가하고 U1 registry contract를 통해 최종 조립한다.
- 명시적 null은 누락과 구분되는 sentinel 또는 typed patch model로 표현한다.
- 401 뒤 PATCH 재호출은 계약이 미적용을 보장하는 경우에만 한 번 허용하고, 그 밖에는 결과 불명확 경로를 사용한다.

### Test Obligations

- 여덟 허용 필드, 금지 필드, omit/null, empty/no-op 경계
- 확인 전 PATCH 0회와 사용자·session·conversation·ticket·value·version 변경 시 무효화
- 정확한 `If-Match`, version 증가와 권한 위임
- 412·428·timeout·transport 오류에서 자동 PATCH 0회와 최신 상세·재확인
- 비밀과 악의적 외부 텍스트가 결과·로그·표시 의미를 바꾸지 않음

## U4 — Release Assurance

### Definition

- **Unit ID:** U4
- **Directory:** `u4-release-assurance`
- **Kind:** omitted — 정의된 다섯 kind 중 통합 assurance 책임에 맞는 것이 없어 full design-artifact matrix를 적용한다.
- **Description:** U1~U3의 runtime 결과를 기존 Agent와 앱에 최종 조립하고, 외부 호출 없는 전체 검증·문서·성과 측정 계약을 출시 가능한 상태로 완결한다.

### Boundaries

**In scope**

- 기존 Agent에 `ticket_read`, `ticket_write`, `ticket_update` 정확히 세 개만 노출되는 최종 조립 검증
- 전체 기존·신규 pytest, 변경 application code 80% line coverage와 예상 밖 network 차단
- 사용자 전환·로그아웃·대화 초기화의 lifecycle 원자성·idempotent cleanup 회귀
- 기존 API·UI·키보드·화면 읽기·고정 model·reasoning·tracing 설정 회귀
- README의 기능, 설정, 실행, 보안 경계, test·coverage와 분리된 실제 API smoke 안내
- NFR8의 생성형 데이터 기반 성과 측정 절차와 기록 형식

**Out of scope**

- 새 CI/CD, 배포 인프라, 독립 runtime 또는 실제 ITSM/OpenAI 자동 호출
- NFR8의 운영 환경 실측 결과를 코드 생성 과정에서 임의로 작성하는 것
- 제품 기능을 U4까지 미루는 것; 각 기능·계층 테스트는 U1~U3에서 완료한다.

### Responsibilities and Deliverables

- 세 도구 schema와 tool-call loop를 FakeModel로, ITSM v2 계약을 MockTransport로 완전 검증한다.
- 자동화 중 실제 OpenAI·ITSM network 호출을 차단하고 비밀 canary가 실패 출력에도 나타나지 않게 한다.
- 기존 기준선과 완료본의 전체 테스트 결과·coverage를 비교하고 승인되지 않은 회귀를 0건으로 만든다.
- README와 성과 측정 절차가 실행 가능한 명령·조건·경계를 제공하는지 검증한다.
- 기존 배포 경로가 소비할 하나의 FastAPI 애플리케이션 결과를 제공한다.

### Implementation Notes and Constraints

- kind를 생략했으므로 U4에는 통합 조립과 cross-tool lifecycle 책임에 필요한 전체 design-artifact matrix를 적용한다. 이를 build/distribution `packaging`으로 축소 해석하지 않는다.
- U4는 앞선 Unit의 누락을 숨기는 대규모 구현 단계가 아니다. 발견된 결함은 소유 Unit 경계에서 수정하고 전체 검증을 다시 수행한다.
- 실제 API smoke는 기본 자동화와 명확히 분리하고 명시적 운영 credential 없이 실행되지 않게 한다.

### Test Obligations

- 기존 기준선과 신규 전체 suite 100% 통과
- 변경 application code line coverage 80% 이상
- 예상하지 않은 OpenAI·ITSM network 호출 0건
- 비밀 canary 노출 0건과 신원·권한·확인 상태 공격 회귀 0건
- 기존 사용자 전환·session·history·UI·API·model 설정 회귀 0건
- README 명령과 NFR8 측정 기록 schema의 재현 가능성 확인

## Cross-Unit Boundaries

| Boundary | Owner | Consumers | Contract |
|---|---|---|---|
| 사용자·위임 capability | U1의 `IdentitySession` 확장 | U1, U2, U3 | current user에 고정된 서버 전용 요청 범위 object; credential은 schema·결과에 없음 |
| ITSM HTTP transport | U1의 `ItsmGateway` 확장 | U1, U2, U3 | typed request/allowlist result, 앱 단위 AsyncClient, 시도별 timeout |
| 안전 업무 연산 | U1의 `TicketOperations` 기반 | U1, U2, U3 | read/create/update 내부 Python interface와 안정적 safe error taxonomy |
| Revocable confirmation | U1이 공통 discriminator schema·repository·invalidation과 `ticket_tools_state_v1` 소유 | U2 create variant, U3 update variant, U4 lifecycle 검증 | user/session/conversation/operation/payload 및 variant별 target/version 결합; 후속 Unit은 U1 migration을 수정하지 않음 |
| Durable create ledger | U2 | U2, U4 lifecycle 검증 | Server Session SQLite의 `ticket_tools_create_v1`; canonical bytes/version/hash/key/outcome, 최소 24시간 retention |
| Agent tool·표시 조립 | U1 registry·envelope·`ticket_tools_history_v1` message-correlation repository contract, U2·U3 별도 tool/mapper 모듈, U4 최종 확인 | 기존 chat API와 browser | U1 registry/history migration을 후속 Unit이 수정하지 않고 최종 세 function tool, 기존 reply 호환, optional `TicketPresentationV1`과 restart history를 조립 |

## Assumptions & Open Questions

None.
