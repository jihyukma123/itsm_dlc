# ITSM 티켓 도구 사용자 스토리

## Sources

- `inception/requirements-analysis/requirements.md`
- `aidlc/spaces/default/codekb/itsm_dlc/business-overview.md`
- `aidlc/spaces/default/codekb/itsm_dlc/component-inventory.md`
- `inception/practices-discovery/team-practices.md`
- `inception/user-stories/personas.md`
- `inception/user-stories/user-stories-questions.md`

## Story Map

| Delivery order | Story | Persona | Journey step | Priority |
|---|---|---|---|---|
| 1 | US1.1 | P1, P2 | 티켓 검색·목록 조회 | Must Have |
| 2 | US1.2 | P1, P2 | ID로 티켓 상세 조회 | Must Have |
| 3 | US2.1 | P1, P2 | 확인 후 티켓 등록 | Must Have |
| 4 | US3.1 | P2, P1 | 최신 version으로 티켓 수정 | Must Have |
| 5 | US4.1 | P1, P2 | 세션·인증·오류의 안전한 복구 | Must Have |
| 6 | US5.1 | P3 | 회귀 검증·문서화·성과 확인 | Must Have |

US1.1은 팀이 확정한 walking skeleton이다. 서버 세션에서 Agent function tool, 사용자 위임 ITSM HTTP, 정제된 도구 결과, FakeModel/MockTransport 검증까지 최소 end-to-end 경로를 먼저 증명한다.

## US1.1 — 권한 범위 안에서 티켓 검색·목록 조회

**Story:** As a P1 일반 사내 사용자 또는 P2 서비스 데스크·운영 담당자, I want 자연어 조건으로 티켓을 검색하고 페이지 단위 목록을 보고 싶다, so that 외부 ITSM 화면으로 이동하지 않고 필요한 티켓을 빠르게 찾을 수 있다.

- **Priority:** Must Have
- **Requirements:** FR1.1~FR1.5, FR2.2~FR2.5, FR5.1~FR5.3, FR6.1~FR6.2, FR7.1~FR7.4, NFR1, NFR2, NFR4, NFR7, NFR9
- **Dependencies:** 기존 로그인 세션과 위임 토큰. 다른 신규 스토리에 대한 기능 의존성은 없다.

### Acceptance Criteria

- **AC1.1.1 — 전체 목록 조건 전달**
  - Given 현재 사용자가 유효한 서버 세션으로 로그인했고 검색어와 하나 이상의 문서화된 필터 또는 정렬을 요청했다
  - When Agent가 `ticket_read` 목록 조회를 실행한다
  - Then `GET /api/v2/tickets`에 계약의 `q`, 반복 가능한 `status`·`priority`와 나머지 허용 필터·정렬만 전달하고 현재 사용자 위임 토큰을 사용한다.
- **AC1.1.2 — 페이지 크기와 cursor**
  - Given 사용자가 limit을 생략하거나 1·20·100·101 중 하나를 요청했다
  - When 목록 결과를 반환한다
  - Then 기본값 20과 최대값 100을 지키고 `has_more`와 `next_cursor`를 표시하며, 101은 계약 오류로 처리하고 조건·정렬이 바뀐 cursor를 재사용하지 않는다.
- **AC1.1.3 — 간결한 목록과 비신뢰 데이터 경계**
  - Given ITSM 목록에 매우 긴 텍스트, HTML/Markdown 제어 문자 또는 지시문 형태 제목이 포함되어 있다
  - When 결과가 도구와 기존 대화 화면에 표시된다
  - Then 허용된 요약 필드만 구조화된 비신뢰 데이터로 제공하고 목적지에 맞게 escape하며, 해당 문자열이 사용자 신원·확인 상태·도구 선택을 바꾸지 않는다.
- **AC1.1.4 — 빈 결과와 부분 조건 안내**
  - Given 조회는 성공했지만 사용자의 조건과 권한 범위에서 일치하는 티켓이 없다
  - When 목록 응답을 표시한다
  - Then 실패와 구분되는 빈 결과와 조건 변경이라는 다음 행동을 텍스트로 안내하고 보이지 않는 티켓의 존재를 추론하지 않는다.
- **AC1.1.5 — 제한된 조회 재시도와 호출 제한**
  - Given 첫 조회가 timeout·전송 오류, HTTP 500·502·503·504 또는 429 `rate_limited`로 실패한다
  - When 복구 정책을 적용한다
  - Then timeout·전송 오류와 500·502·503·504에만 250ms 고정 지연 후 한 번 재시도하여 최초 호출 포함 최대 2회와 시도별 `ITSM_TIMEOUT_SECONDS`, 전체 `2 × ITSM_TIMEOUT_SECONDS + 0.25초` 상한을 지킨다. 429에는 자동 대기와 자동 재시도를 0회로 하고 즉시 안전 오류를 반환하며, `Retry-After`가 유효한 초 단위 값일 때 그 값과 다시 요청할 시점을 안내하고 유효하지 않거나 없으면 원문을 노출하지 않은 채 나중에 다시 요청하도록 안내한다.
- **AC1.1.6 — 접근 가능한 텍스트 흐름**
  - Given 사용자가 키보드와 화면 읽기 도구로 기존 대화 화면을 사용한다
  - When 로딩·성공·빈 결과·오류·다음 페이지 상태가 바뀐다
  - Then 각 상태와 다음 행동을 색상·아이콘에 의존하지 않는 텍스트와 기존 live 알림 흐름으로 이해할 수 있다.

**INVEST:** 독립적인 읽기 수직 조각이고 사용자 가치가 명확하며, 한 iteration 안에 구현 가능한 범위와 자동화 가능한 정상·경계·실패 기준을 가진다.

## US1.2 — ID로 티켓 상세 조회

**Story:** As a P1 일반 사내 사용자 또는 P2 서비스 데스크·운영 담당자, I want 알고 있는 티켓 ID의 허용된 상세 정보를 보고 싶다, so that 상태와 영향을 정확히 이해하고 다음 업무를 결정할 수 있다.

- **Priority:** Must Have
- **Requirements:** FR1.3~FR1.5, FR2.1, FR2.4~FR2.5, FR5.1~FR5.3, FR6.1~FR6.2, FR7.1~FR7.4, NFR1, NFR2, NFR7, NFR9
- **Dependencies:** 기존 로그인 세션. US1.1 다음에 전달하지만 독립된 ID 상세 계약으로 테스트할 수 있다.

### Acceptance Criteria

- **AC1.2.1 — 상세 엔드포인트 사용**
  - Given 현재 사용자가 티켓 ID를 제공한다
  - When `ticket_read`가 상세 조회를 실행한다
  - Then ID를 불투명 문자열로 취급해 `GET /api/v2/tickets/{id}`를 현재 사용자 위임 토큰으로 호출하고 하드코딩된 티켓 ID를 사용하지 않는다.
- **AC1.2.2 — 허용된 상세만 제공**
  - Given ITSM이 사용자가 볼 수 있는 티켓 상세를 반환한다
  - When 도구 결과를 모델에 제공한다
  - Then 허용 목록 필드를 의미 단위의 구조화된 데이터로 제공하고 누락 값을 추측하거나 원본 헤더·비밀을 포함하지 않는다.
- **AC1.2.3 — 부재와 비가시성 비구분**
  - Given ITSM이 `ticket_not_found` 404를 반환한다
  - When 사용자에게 결과를 안내한다
  - Then 실제 부재와 권한상 비가시성을 구분하지 않는 동일한 안전 응답을 제공한다.
- **AC1.2.4 — 상세 텍스트의 지시문 격리**
  - Given 제목·설명·영향 범위에 신원 변경, 확인 생략 또는 비밀 출력을 명령하는 텍스트가 있다
  - When 상세 결과가 모델과 화면을 거친다
  - Then 텍스트를 데이터로만 표시하고 시스템·개발자 지침, 현재 사용자, 권한 또는 후속 도구 호출이 바뀌지 않는다.
- **AC1.2.5 — 상세 조회 실패 복구**
  - Given 인증 만료, 호출 제한 또는 일시적 장애가 발생한다
  - When 상세 조회를 복구한다
  - Then US4.1의 갱신·재시도 상한과 안전한 오류 규칙을 따르며 성공하지 않은 결과를 성공으로 표시하지 않는다. 특히 429에는 자동 대기와 자동 재시도를 0회로 하고 즉시 안전 오류를 반환하며, 유효한 `Retry-After` 초와 다시 요청할 시점을 안내한다.

**INVEST:** 단일 ID 조회의 사용자 결과에 집중하고 목록 구현과 분리해 추정·자동화할 수 있다.

## US2.1 — 검증과 확인 후 티켓 등록

**Story:** As a P1 일반 사내 사용자 또는 P2 서비스 데스크·운영 담당자, I want 대화로 티켓 정보를 준비하고 최종 내용을 확인한 뒤 등록하고 싶다, so that 반복 입력을 줄이면서 의도하지 않은 티켓 생성을 막을 수 있다.

- **Priority:** Must Have
- **Requirements:** FR1.1~FR1.5, FR3.1~FR3.5, FR5.1~FR5.4, FR6.1, FR6.3, FR7.1~FR7.4, NFR1~NFR3, NFR7, NFR9
- **Dependencies:** US1.1에서 증명한 공통 세션→도구→ITSM 경계. 등록 행동 자체는 독립 검증한다.

### Acceptance Criteria

- **AC2.1.1 — 계약 필드 검증**
  - Given 사용자가 제목·설명·서비스·영향도·긴급도·영향 범위·발생 시각과 선택 필드를 제공한다
  - When 등록 내용을 준비한다
  - Then `TicketCreateIn` 허용 필드만 사용하고 필수·길이·enum·시간대 조건을 검증하며 오류 시 사용자가 입력한 값을 보존한 채 필드와 수정 방법을 안내한다.
- **AC2.1.2 — 카탈로그와 발생 시각 해석**
  - Given 사용자가 서비스·컴포넌트·모델의 ID 또는 이름과 발생 시각을 제공한다
  - When 서버가 계약 값으로 해석한다
  - Then 유일하게 일치하는 활성 카탈로그 항목만 선택하고, 모호함·미존재·폐기·서비스 불일치에서는 등록하지 않으며, 시간대가 있는 값 또는 명시적 “지금”만 UTC로 정규화한다.
- **AC2.1.3 — 정확한 최종 확인**
  - Given 등록에 필요한 모든 값이 유효하다
  - When 사용자가 실행 전 요약을 본다
  - Then 현재 사용자·세션·대화·전체 본문에 결합된 읽기 쉬운 요약과 확인·수정·취소 선택을 받고, 명시적 확인 전에는 POST를 보내지 않는다.
- **AC2.1.4 — 변경·취소와 확인 무효화**
  - Given 사용자가 요약 후 필드를 바꾸거나 취소하거나 사용자·세션·대화가 바뀐다
  - When 다음 동작을 처리한다
  - Then 이전 확인을 무효화하고, 취소는 미실행으로 끝내며, 변경된 전체 요약을 다시 확인받기 전까지 등록하지 않는다.
- **AC2.1.5 — 멱등 등록과 결과 불명확 복구**
  - Given 사용자가 확인한 등록의 첫 응답이 불명확하거나 동일 요청을 반복한다
  - When 등록 결과를 복구한다
  - Then 성공·실패를 추측하지 않고 계약이 기존 결과 확인 수단을 제공하면 그 확인을 먼저 수행한다. 결과가 여전히 불명확할 때만 최초 포함 최대 2회 안에서 사용자·대화·동일 본문에 결합된 예측 불가능한 같은 `Idempotency-Key`와 바이트 단위로 동일한 본문으로 한 번 재시도하며, 새 키로 조용히 재시도하지 않는다. 최종 결과는 생성 또는 멱등 재생으로 확인된 티켓 ID, 생성되지 않음이 확인된 상태, 또는 여전히 결과 불명확하여 추가 자동 등록을 중단한 상태 중 하나로 사용자에게 명시하고, 다른 본문에는 새 확인과 새 키를 요구해 생성 결과가 최대 1개다.
- **AC2.1.6 — 안전한 성공·오류 결과**
  - Given ITSM이 성공, `Idempotent-Replayed`, 4xx, 429 또는 5xx를 반환한다
  - When 결과를 사용자에게 표시한다
  - Then 생성된 티켓 ID 또는 안전한 오류·다음 행동만 텍스트로 제공하고, 429는 자동 대기 없이 검증된 `Retry-After`를 안내하며 원본 detail·헤더·비밀을 노출하지 않는다.

**INVEST:** 준비부터 사용자 확인과 생성 결과까지 하나의 가치 흐름이며 멱등·오류 기준으로 독립 자동화할 수 있다.

## US3.1 — 최신 version을 확인한 티켓 부분 수정

**Story:** As a P2 서비스 데스크·운영 담당자 또는 권한 있는 P1 사용자, I want 변경 전후 값을 확인하고 최신 티켓 version에 필요한 필드만 수정하고 싶다, so that 다른 사용자의 변경을 잃지 않고 정확한 내용을 반영할 수 있다.

- **Priority:** Must Have
- **Requirements:** FR1.1~FR1.5, FR4.1~FR4.5, FR5.1~FR5.4, FR6.1, FR6.4, FR7.1~FR7.4, NFR1~NFR3, NFR7, NFR9
- **Dependencies:** ID 상세 조회 계약을 재사용하지만 PATCH 동작과 충돌 경로는 독립적으로 검증한다.

### Acceptance Criteria

- **AC3.1.1 — 허용된 부분 변경**
  - Given 사용자가 티켓 ID와 하나 이상의 수정값을 요청한다
  - When PATCH 본문을 준비한다
  - Then `title`, `description`, `component_id`, `model`, `impact_level`, `urgency`, `impact_note`, `is_major`만 받고 생략과 계약상 명시적 null을 구분하며 서비스·상태·담당 관련 필드는 거부한다.
- **AC3.1.2 — 현재 값과 version 조회**
  - Given 수정 가능한 요청이 들어온다
  - When 변경 요약을 만들기 전이다
  - Then 현재 사용자 위임 토큰으로 최신 상세를 조회하고 ETag 또는 응답 `version`을 보존하며 이전 값과 새 값만 비교한다.
- **AC3.1.3 — 변경에 결합된 확인**
  - Given 변경할 필드가 현재 값과 다르다
  - When 실행 전 요약을 표시한다
  - Then 현재 사용자·세션·대화·대상·이전/새 값·version에 결합된 확인·수정·취소를 요청하고 명시적 확인 전에는 PATCH를 보내지 않는다.
- **AC3.1.4 — 조건부 PATCH와 권한 위임**
  - Given 사용자가 정확한 요약을 확인한다
  - When `PATCH /api/v2/tickets/{id}`를 호출한다
  - Then 확인된 version의 `If-Match`와 사용자 위임 토큰을 보내고 실제 수정·major 선언 권한 판단은 ITSM 응답을 따른다.
- **AC3.1.5 — 충돌과 결과 불명확 처리**
  - Given ITSM이 412·428을 반환하거나 전송 결과가 불명확하다
  - When 복구를 시도한다
  - Then PATCH를 자동 재시도하거나 덮어쓰지 않고 최신 상세와 version을 다시 조회해 적용 여부를 판별하며, 변경이 여전히 필요하면 새 요약과 확인을 요구한다.
- **AC3.1.6 — 빈 변경과 상태 전환 무효화**
  - Given 변경 필드가 없거나 현재 값과 같거나 사용자·세션·대상·값·version이 확인 후 바뀐다
  - When 수정 실행 여부를 결정한다
  - Then PATCH를 보내지 않고 이유와 다음 행동을 텍스트로 안내하며 이전 확인을 재사용하지 않는다.

**INVEST:** 허용 필드의 부분 수정과 낙관적 잠금이라는 하나의 사용자 목표를 다루며 정상·충돌·불명확 결과가 자동화 가능하다.

## US4.1 — 사용자 경계를 유지하는 안전한 복구

**Story:** As a P1 일반 사내 사용자 또는 P2 서비스 데스크·운영 담당자, I want 세션·인증·호출 오류가 발생해도 내 권한과 확인 상태가 안전하게 유지되길 원한다, so that 다른 사용자로 작업하거나 실패한 변경을 성공으로 오해하지 않을 수 있다.

- **Priority:** Must Have
- **Requirements:** FR1.3~FR1.5, FR5.1~FR5.4, FR6.1~FR6.4, FR7.2~FR7.4, NFR1~NFR3, NFR7, NFR9
- **Dependencies:** 모든 티켓 스토리에 적용되는 공통 수직 안전 흐름이며 FakeModel/MockTransport로 독립 검증한다.

### Acceptance Criteria

- **AC4.1.1 — 서버 세션 신원 고정**
  - Given 사용자 메시지·도구 인자·ITSM 텍스트가 다른 username·role·permission 사용을 지시한다
  - When 어떤 티켓 도구를 실행한다
  - Then HttpOnly 세션 ID로 복원된 현재 사용자만 사용하고 모델 입력으로 신원·권한을 변경하지 않는다.
- **AC4.1.2 — 위임 토큰과 비밀 비노출**
  - Given 티켓 요청이 준비된다
  - When Authorization을 구성하고 결과·로그·오류를 만든다
  - Then 사용자 위임 토큰만 티켓 API 요청 경계에서 사용하고 토큰·client secret·OpenAI API key·Authorization 값은 schema·모델·결과·로그·테스트 출력에 0건 노출된다.
- **AC4.1.3 — 도구별 만료 토큰 한 번 갱신**
  - Given 서버 세션은 유효하지만 조회·등록·수정에 사용할 위임 토큰이 만료됐거나 만료 임박했거나 요청이 401 `token_expired`를 반환한다
  - When 해당 티켓 요청의 인증을 복구한다
  - Then 기존 경로로 토큰을 한 번만 갱신한다. 조회는 갱신 후 재호출까지 최초 포함 최대 2회 상한을 지키고, 등록은 확인된 원래 `Idempotency-Key`와 바이트 단위로 동일한 본문을 유지하며 최초 포함 최대 2회 안에서만 계속한다. 수정은 401 응답이 변경 미적용을 계약상 보장할 때에만 같은 확인·version·본문으로 갱신 후 한 번 계속하고, 보장하지 않으면 PATCH를 자동 재호출하지 않고 US3.1의 결과 불명확 경로로 전환한다. 갱신이 실패하면 어떤 변경 요청도 새로 보내지 않고 작업 미실행과 재로그인을 안내한다.
- **AC4.1.4 — 인증 복구 실패 시 미실행**
  - Given 토큰 갱신 실패, 비활성 사용자 또는 세션 만료가 발생한다
  - When 등록·수정이 보류 중이다
  - Then ITSM 변경 요청을 보내지 않고 확인·멱등 상태를 무효화하며 재로그인과 미실행 상태를 안내한다.
- **AC4.1.5 — 사용자·대화 전환 격리**
  - Given 사용자 전환, 대화 초기화 또는 세션 종료가 발생한다
  - When 다음 사용자가 티켓 작업을 시작한다
  - Then 이전 사용자의 capability·토큰·확인·멱등키·도구 결과를 재사용하거나 대화 이력에 섞지 않는다.
- **AC4.1.6 — 안정적인 안전 오류**
  - Given 악의적 problem detail, 403·404·409·412·422·428·429·5xx 또는 전송 오류가 발생한다
  - When 오류를 도구와 사용자에게 전달한다
  - Then 허용된 범주·안전한 설명·필드·재시도 가능 여부·비밀 아닌 request ID와 다음 행동만 제공하고, 수정 결과 불명확 시 자동 PATCH는 0회다. 429에는 자동 대기와 자동 재시도를 0회로 하고 즉시 안전 오류를 반환하며, 유효한 `Retry-After` 초와 다시 요청할 시점을 안내하고 유효하지 않거나 없는 값은 원문 그대로 반환하지 않는다.

**INVEST:** 모든 도구가 공유하지만 관찰 가능한 인증·오류 복구 가치와 명확한 공격·경계 테스트를 가진 독립 안전 스토리다.

## US5.1 — 재현 가능한 출시 검증과 사용 안내

**Story:** As a P3 개발·운영 유지보수 담당자, I want 세 티켓 도구를 외부 호출 없이 검증하고 실행·보안 경계를 문서로 확인하고 싶다, so that 기존 Assistant를 깨뜨리지 않고 기능을 안전하게 출시하고 지원할 수 있다.

- **Priority:** Must Have
- **Requirements:** FR1.1~FR1.3, FR7.3~FR7.5, NFR1~NFR9
- **Dependencies:** 각 기능 스토리의 구현 결과를 검증하지만 테스트 fixture·문서·측정 절차 자체는 독립적으로 작성하고 실행할 수 있다.

### Acceptance Criteria

- **AC5.1.1 — 기존 Agent에 정확히 세 도구**
  - Given 애플리케이션을 현재 설정으로 시작한다
  - When Agent 구성을 검사한다
  - Then 기존 `Agent`와 `Runner`에 `ticket_read`, `ticket_write`, `ticket_update`만 노출되고 새 Agent·서비스·자체 loop가 없으며 고정 model·reasoning과 tracing 비활성 설정이 유지된다.
- **AC5.1.2 — 외부 호출 없는 계약 테스트**
  - Given 자동화 테스트를 실행한다
  - When 도구 schema·tool-call loop·ITSM HTTP 계약·오류·공격 경로를 검증한다
  - Then FakeModel과 `httpx.MockTransport`만 사용하고 예상하지 않은 실제 OpenAI·ITSM 네트워크 호출은 차단된다.
- **AC5.1.3 — 회귀와 coverage**
  - Given 코드 변경 전 기준선과 구현 완료본이 있다
  - When 문서화된 전체 pytest와 coverage 명령을 실행한다
  - Then 기존 37개와 신규 테스트의 통과율은 100%이고 새로 만들거나 변경한 애플리케이션 코드의 line coverage는 80% 이상이다.
- **AC5.1.4 — 기존 경험 보존**
  - Given 사용자 전환, 세션, 대화 이력·초기화, 기존 UI와 API 회귀 시나리오가 있다
  - When 전체 테스트를 실행한다
  - Then 승인되지 않은 동작 변경은 0건이고 티켓 기능의 상태·오류·확인은 기존 키보드·화면 읽기 흐름에서 텍스트로 제공된다.
- **AC5.1.5 — README와 스모크 경계**
  - Given 유지보수 담당자가 저장소 README를 읽는다
  - When 기능을 설정·실행·테스트한다
  - Then 세 도구, 기존 설정, 세션·위임 보안 경계, 테스트·coverage 명령과 실제 API 스모크가 기본 자동화와 분리되어 있음을 확인할 수 있다.
- **AC5.1.6 — 재현 가능한 성과 측정**
  - Given 요구사항 NFR8의 동일 계정·환경·network·warm cache·생성형 테스트 데이터와 세 시나리오가 준비된다
  - When 기존 ITSM 화면과 Assistant를 조회·등록·수정별 각 3회 monotonic clock으로 측정한다
  - Then 지정된 기록 필드를 남기고 각 중앙값을 산출하며, Assistant는 외부 화면 전환 0회이고 각 시나리오 중앙 완료 시간이 기존 방식보다 짧다.

**INVEST:** 출시 안전성이라는 P3의 가치를 제공하며 테스트, 문서와 측정 결과로 완료 여부를 독립 판정할 수 있다.

## Cross-Story Rules

- Agent에 노출되는 function tool은 정확히 세 개이며 내부 helper·catalog lookup·capability는 모델 도구가 아니다.
- 티켓 권한·가시성·우선순위·서버 생성 필드는 ITSM API가 원천이며 로컬에서 확대하거나 재구현하지 않는다.
- 모든 ITSM 업무·오류 텍스트는 비신뢰 데이터로 구조적으로 구분하고 목적지에 맞게 escape한다.
- 등록·수정의 확인은 사용자·세션·대화·대상·필드·값과 필요한 version에 결합하며 어느 하나라도 바뀌면 재확인한다.
- 제품 코드·지침에는 샘플 티켓이나 특정 티켓 ID를 하드코딩하지 않는다.

## Won't Have This Time

- 티켓 삭제, 상태 전이, 담당자·담당 그룹 배정
- 댓글, 내부 메모, 작업 기록, 첨부파일, 변경 이력, 통계, 문제 연결, 병합, 내보내기
- 새 Agent·서비스·화면·탭·버튼 또는 기존 화면 재설계
- ITSM v1이나 계약 밖 필드 변경, 자동 권한 확대, 보이지 않는 티켓 존재 추론
