# ITSM 티켓 도구 Architecture Decision Records

## Sources

- `inception/domain-design/domain-design-questions.md`
- `inception/domain-design/components.md`
- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `aidlc/spaces/default/codekb/itsm_dlc/architecture.md`
- `aidlc/spaces/default/codekb/itsm_dlc/component-inventory.md`
- `docs/itsm/integration-guide.md`
- `docs/itsm/openapi.json`

## ADR-001: TicketOperations와 application lifecycle 경계로 안전 불변식과 호출 순서 분리

### Status

Accepted

### Context

기존 `AgentService`는 모델 실행과 대화 이력을, `ItsmAuthClient`는 외부 인증·HTTP를 책임진다. 현재 session route는 사용자 전환·종료 시 app state를 통해 `AgentService`의 이력 정리를 호출하므로, Agent가 다시 session에 의존하면 실제 brownfield 호출 그래프에 순환이 생긴다. 새 기능은 조회 제한 재시도, 등록 확인·멱등성, 수정 `If-Match`·충돌 복구, 사용자·세션·대화 수명주기 무효화라는 서로 강하게 결합된 규칙도 추가한다. 새 Agent나 별도 서비스는 금지되어 있고 기존 배포와 API를 유지해야 한다. 보안상 token과 원본 오류는 모델 경계에 들어갈 수 없다.

### Decision

같은 FastAPI 프로세스 안에 내부 논리 컴포넌트 `TicketOperations`를 추가한다. 기존 FastAPI route와 앱 조립 경계는 `ApplicationLifecycle`로 명시해 보호된 chat, 사용자 전환, 로그아웃, 대화 초기화의 순서를 소유한다. `ApplicationLifecycle`은 `IdentitySession`, `AgentConversation`, `TicketOperations`을 단방향으로 호출하고, 이 세 컴포넌트는 coordinator를 역호출하지 않는다. 사용자 전환·로그아웃은 새 session 변경을 마지막에 commit하며, 그 전에 revocable confirmation 무효화와 conversation 이력 정리를 idempotent하게 수행한다. 정리 실패 시 새 session을 활성화하지 않는다. `AgentConversation`은 정확히 세 function tool을 노출하고 `TicketOperations`를 호출하며, `TicketOperations`는 조회·등록·수정의 검증, 확인, 멱등성, 충돌, 재시도와 안전 결과를 단일 소유한다. 어느 경계도 새 배포 단위나 별도 서비스가 아니다.

### Consequences

- Positive: 세 도구가 공유하는 안전 불변식의 소유권이 명확하고 격리 단위 테스트가 가능하다.
- Positive: Agent 지침, 외부 HTTP 세부사항, 상태 저장이 서로 직접 결합되지 않는다.
- Positive: 기존 session→Agent 역호출을 coordinator 호출로 대체해 실제 의존 그래프와 실패 순서가 비순환으로 명시된다.
- Negative: 기존 소규모 코드베이스에 내부 인터페이스와 application-level 조립 책임이 늘어난다.
- Negative: session commit을 마지막에 두고 정리 operation을 idempotent하게 만드는 구현·테스트가 필요하다.
- Security: 비밀 credential은 요청 범위 capability 뒤에 머물고 function tool schema·결과에는 들어가지 않는다.

### Alternatives Rejected

- 기존 `AgentService`와 `ItsmAuthClient`에 분산: 파일 수는 줄지만 확인·멱등·충돌 규칙의 단일 소유자가 사라지고 테스트 경계가 흐려진다.
- 조회·등록·수정을 각각 별도 컴포넌트로 분리: 작업별 경계는 선명하지만 세션·확인·오류 정책이 중복되고 현재 범위에 비해 복잡하다.
- 새 티켓 서비스로 분리: 독립 배포 가능성은 생기지만 명시된 범위를 위반하고 운영·인증 경계를 불필요하게 늘린다.
- session과 Agent가 서로 직접 호출: 현재 코드 변경량은 적지만 reverse dependency와 순환을 보존하고 부분 실패 순서를 소유할 경계가 없다.

## ADR-002: 하나의 ItsmGateway와 내부 계약 어댑터 사용

### Status

Accepted

### Context

기존 ITSM client는 앱 단위 `httpx.AsyncClient`, 설정, 인증과 오류 변환을 이미 소유한다. 티켓 기능은 같은 API v2 base URL과 timeout 수명주기를 사용하지만 서비스 credential 기반 디렉터리·카탈로그 호출과 사용자 위임 credential 기반 티켓 호출을 엄격히 구분해야 한다. 외부 계약 변경은 애플리케이션 업무 규칙에 전파되지 않아야 한다.

### Decision

`ItsmGateway`를 하나의 논리 컴포넌트로 두고 인증·디렉터리, 카탈로그, 티켓 HTTP 책임을 내부 클래스 또는 모듈로 분리한다. 공개 경계는 typed request/response와 allowlist 오류만 제공한다. 원본 problem detail, 예외 문자열, Authorization과 response header 전체는 경계 밖으로 내보내지 않는다.

### Consequences

- Positive: 기존 HTTP client 생명주기와 test transport 주입을 재사용한다.
- Positive: token 종류와 endpoint별 계약을 내부 어댑터 수준에서 분리해 서비스 token의 티켓 사용을 막을 수 있다.
- Negative: 논리 컴포넌트 내부에 여러 어댑터가 있어 명명과 공개 API 규율이 필요하다.
- Negative: 너무 큰 단일 Python 클래스가 되지 않도록 내부 모듈 분리를 유지해야 한다.
- Security: credential은 HTTP 요청 조립 순간에만 사용하며 정제된 결과에 포함하지 않는다.

### Alternatives Rejected

- 기존 `ItsmAuthClient` 한 클래스에 모든 메서드 직접 추가: 초기 변경은 작지만 인증과 티켓 계약이 하나의 큰 클래스에 결합된다.
- endpoint군마다 별도 논리 컴포넌트 생성: 격리는 높지만 같은 transport·설정·오류 규칙을 중복하고 조립 복잡도가 커진다.
- 다른 저장소의 ITSM client import: 구현 속도 이점이 있을 수 있으나 계약 기준과 금지 제약을 위반한다.

## ADR-003: ITSM 원천 데이터와 서버 측 변경 상태의 소유권 분리

### Status

Accepted

### Context

권한·가시성·우선순위·서버 생성 필드의 원천은 ITSM이다. Assistant가 티켓을 복제하면 stale 데이터와 로컬 권한 판단 위험이 생긴다. 반면 등록의 24시간 멱등성, 수정의 확인 version, 사용자·세션·대화 변경 시 무효화는 모델 대화나 프로세스 메모리만으로 안전하게 유지할 수 없다.

### Decision

티켓과 카탈로그는 ITSM 소유 외부 데이터로 남기고 Assistant는 요청별 안전 projection만 사용한다. Assistant가 소유하는 업무·대화 상태는 `ServerSession`, `Conversation`, `PendingTicketMutation`, `TicketCreateAttempt`이며, continuation과 기존 대화 표시 복원을 위한 기술 persistence record로 `TicketCursorBinding`, `TicketMessagePresentation`도 소유한다. `PendingTicketMutation`은 U1이 소유하는 하나의 discriminator schema와 create/update variant로 정의하며, 확인 전 상태를 사용자·session·conversation·작업·정규화된 본문 hash와, 수정이면 티켓 ID·base version에 결합하고 사용자 전환·로그아웃·대화 초기화에서 폐기한다. `TicketCreateAttempt`는 별도의 durable ledger다. 확인 직후 HTTP 호출 전에 canonical request bytes, serialization version, bytes hash, 예측 불가능한 idempotency key, 원래 사용자 범위, 시도·결과 상태와 retention 시각을 SQLite에 저장한다. ambiguous·completed ledger row는 session·conversation lifecycle과 무관하게 계약 window인 최소 24시간 보존하고, 재조정은 저장된 동일 bytes와 key만 사용한다. `TicketCursorBinding`은 canonical normalized query·hash와 upstream cursor를 사용자·session·conversation에 결합하고 해당 lifecycle 종료나 upstream invalid cursor에서 폐기한다. `TicketMessagePresentation`은 기존 SDK assistant message의 conversation·sequence·text hash에 결합하며 대화 이력과 같은 수명으로 보존한다.

논리 공통 저장 계약 `ticket_tools_common_v1`은 물리 DB 경계에 따라 U1-owned migration 두 개로 배치한다. Server Session SQLite의 `ticket_tools_state_v1`은 `pending_ticket_mutations`와 `ticket_cursor_bindings`를, Agents SDK history SQLite의 `ticket_tools_history_v1`은 `ticket_message_presentations`를 소유한다. U2의 create ledger는 Server Session SQLite의 별도 `ticket_tools_create_v1.ticket_create_attempts`에 저장하며 U2와 U3는 U1의 두 migration namespace를 수정하지 않는다.

### Consequences

- Positive: 로컬 복제 때문에 ITSM 가시성과 권한을 확대 해석하지 않는다.
- Positive: 재시작과 불명확한 응답 뒤에도 같은 등록 의도를 식별하고 중복을 막을 수 있다.
- Positive: 사용자 전환·세션 종료·대화 초기화에서 확인 권한은 즉시 폐기하면서도 중복 방지 원장은 보존한다.
- Positive: cursor와 presentation metadata는 서버 소유 기술 record로 격리되어 raw upstream cursor나 모델 추론으로 대화 이력을 복원하지 않는다.
- Negative: SQLite에 canonical request bytes를 포함한 ledger와 cursor·presentation companion schema, serialization version과 만료·정리 로직이 추가된다.
- Negative: ITSM 조회 없이는 오프라인 티켓 표시가 불가능하지만 이번 범위에 오프라인 요구는 없다.
- Security: canonical request에는 계약상 업무 필드만 저장하고 credential·Authorization·API key는 저장하지 않는다. 모델·클라이언트는 ledger 식별자나 idempotency key를 권한으로 사용할 수 없다.

### Alternatives Rejected

- 티켓·카탈로그 전체 로컬 복제: 성능·오프라인 이점보다 stale 권한·가시성·동기화 위험이 크다.
- 프로세스 메모리 저장: 구현은 단순하지만 재시작·다중 프로세스·결과 불명확 복구에서 멱등성을 보장하지 못한다.
- SDK 대화 이력과 모델 추론: 추가 저장소는 없지만 비밀·확인 상태가 모델 경계를 넘고 결정성이 없다.
- request hash와 idempotency key만 저장: 저장량은 작지만 재시작 뒤 byte-identical body를 재현할 근거가 없어 계약상 안전한 재시도를 보장하지 못한다.

## ADR-004: 서버 소유의 허용 목록 대화 표시 계약

### Status

Accepted

### Context

기존 API는 자유 형식 `reply`와 텍스트 대화 흐름을 사용한다. 새 흐름은 목록·상세·확인·성공·충돌·결과 불명확 상태를 접근 가능하게 구분해야 하며, 생성 성공에는 티켓 ID, 수정 성공에는 실제 적용 변경과 새 version이 필요하다. ITSM 텍스트와 모델 응답은 신뢰할 수 없으므로 DOM role, heading, live priority를 선택해서는 안 된다.

### Decision

`ConversationPresentation`이 기존 응답 필드를 유지하면서 선택적 `TicketPresentationV1`을 소유한다. 서버는 안전한 도구 결과를 allowlist kind와 block으로 매핑한다. 브라우저는 schema를 검증하고 textContent 등 목적지별 escape로 렌더링한다. metadata가 없거나 잘못되면 기존 일반 메시지로 fallback하고, 필수 성공 근거가 없거나 모호하면 성공 kind를 만들지 않는다.

### Consequences

- Positive: 기존 API·화면 호환성을 유지하면서 상태와 접근성 의미가 결정적이다.
- Positive: 외부 문자열과 모델 문구가 DOM 의미나 live 우선순위를 조작하지 못한다.
- Negative: 서버와 브라우저가 같은 presentation version과 allowlist를 맞춰야 한다.
- Negative: 새 상태를 추가할 때 계약 version 또는 하위 호환 규칙을 검토해야 한다.
- Security: raw HTML을 사용하지 않고 외부 텍스트를 data로만 렌더링한다.

### Alternatives Rejected

- `TicketOperations`가 UI 계약까지 소유: 구현 파일은 줄지만 업무 규칙과 표현 변경이 결합된다.
- 브라우저가 자유 형식 `reply`를 분석: 서버 변경은 적지만 상태 추론이 불안정하고 prompt injection·접근성 의미 조작 위험이 있다.
- 새 티켓 화면·버튼 추가: 시각적 제어는 쉬워지지만 승인된 기존 대화 화면 유지 범위를 위반한다.

## Assumptions & Open Questions

None.
