# ITSM 티켓 도구 요구사항

## Sources

- 최초 요청: `aidlc/spaces/default/intents/261024-itsm-ticket-tools/project-description.json`
- 제품 의도와 성공 기준: `ideation/intent-capture/intent-statement.md`
- 승인된 범위와 제외 항목: `ideation/scope-definition/scope-document.md`
- 위험 인계와 수용 근거: `ideation/approval-handoff/initiative-brief.md`, `ideation/feasibility/raid-log.md`
- 기존 사용자 흐름과 오류·접근성 상태: `ideation/rough-mockups/user-flow.md`, `ideation/rough-mockups/wireframes.md`
- 현재 제품·아키텍처·코드 경계: `aidlc/spaces/default/codekb/itsm_dlc/business-overview.md`, `aidlc/spaces/default/codekb/itsm_dlc/architecture.md`, `aidlc/spaces/default/codekb/itsm_dlc/code-structure.md`
- 확정된 팀 관행: `inception/practices-discovery/team-practices.md`
- ITSM 연동 계약: `docs/itsm/integration-guide.md`, `docs/itsm/openapi.json`
- 이 단계에서 확인한 결정: `inception/requirements-analysis/requirements-analysis-questions.md`

## Intent Analysis

기존 ITSM Assistant 사용자가 현재 대화 화면을 벗어나지 않고 자신의 ITSM 권한 범위에서 티켓을 조회·등록·수정하게 하는 것이 목표다. 구현은 기존 OpenAI Agents SDK `Agent`와 `Runner`, 서버 측 사용자 세션, 사용자 위임 토큰, 대화 이력과 고정 모델 설정을 그대로 확장한다. ITSM 업무 데이터와 권한의 원천은 API v2이며 Assistant는 권한을 확대하거나 보이지 않는 티켓의 존재를 추론하지 않는다.

핵심 사용자 가치는 외부 ITSM 화면 전환 제거, 반복 작업 시간 단축, 변경 전 명시적 확인과 안전한 오류 복구다. 첫 전달 순서는 공통 안전 경계, `ticket_read` walking skeleton, `ticket_write`, `ticket_update`, 전체 회귀·문서 검증이다.

## Functional Requirements

### FR1 — Agent 도구 표면과 서버 경계

- **FR1.1** 시스템은 기존 Agent에 OpenAI Agents SDK function tool인 `ticket_read`, `ticket_write`, `ticket_update`를 정확히 세 개만 등록해야 한다.
- **FR1.2** 세 도구는 기존 `Runner` 실행과 대화 이력을 사용해야 하며 새 Agent, 별도 서비스 또는 자체 Agent loop를 만들지 않아야 한다.
- **FR1.3** 도구 입력에는 업무 필드와 확인에 필요한 비밀 아닌 식별 정보만 포함해야 하며, 액세스 토큰, client secret, OpenAI API key 또는 Authorization 헤더를 모델이 생성하거나 볼 수 있는 schema에 포함하지 않아야 한다.
- **FR1.4** 도구 실행은 현재 서버 세션에 결합된 서버 전용 ITSM capability를 통해서만 API v2 HTTP 요청을 수행하고, 모델에는 허용 목록으로 정제된 업무 결과 또는 안전한 오류만 반환해야 한다.
- **FR1.5** ITSM이 반환한 제목·설명·영향 범위·오류 문구 등 모든 외부 텍스트는 신뢰할 수 없는 데이터로 취급해야 한다. 서버는 이를 허용된 필드의 구조화된 `data` 영역에만 넣고, 모델 지침과 분리된 데이터 경계를 표시하며, UI 등 최종 목적지에 맞게 escape해야 한다. 외부 텍스트의 지시문 형태 내용은 시스템·개발자 지침, 현재 사용자 신원·권한, 확인 상태, 도구 선택 또는 도구 인자를 변경하는 근거로 사용해서는 안 된다.

검증 기준: Agent 구성 검사에서 도구 이름 집합이 정확히 세 개이고, FakeModel에 전달된 입력과 각 도구 결과에서 비밀 canary가 0건이어야 한다. 제목·설명·영향 범위·문제 응답에 사용자 전환, 확인 생략, 비밀 출력 또는 추가 도구 호출을 명령하는 문자열과 HTML/Markdown 제어 문자를 주입해도 구조화된 데이터 경계가 유지되고 신원·권한·확인·도구 동작이 바뀌지 않음을 자동 검증해야 한다.

### FR2 — `ticket_read` 목록·검색·상세 조회

- **FR2.1** 티켓 ID가 제공되면 `GET /api/v2/tickets/{id}`를 호출해 현재 사용자가 볼 수 있는 상세 정보를 조회해야 한다.
- **FR2.2** 티켓 ID가 없으면 `GET /api/v2/tickets`를 사용하며 계약의 `q`, 반복 가능한 `status`·`priority`, `service_id`, `component_id`, `model`, `assignment_group_id`, `assignee`, `requester`, `classification`, `is_major`, `created_from`, `created_to`, `updated_from`, `sort`, `limit`, `cursor`를 지원해야 한다.
- **FR2.3** 목록은 계약 기본값 20과 최대값 100을 지키는 한 페이지 단위로 반환하고, 핵심 요약 필드와 `has_more`, `next_cursor`를 제공해야 한다. 조건 또는 정렬이 바뀐 이전 cursor는 재사용하지 않아야 한다.
- **FR2.4** 상세 결과는 ITSM이 반환한 허용 필드를 의미 단위의 구조화된 데이터로 제공하되 선택 값이 없으면 추측하지 않아야 하며, 목록 결과는 모델 context를 제한하기 위해 요약 필드만 반환해야 한다. 반환된 텍스트는 FR1.5의 신뢰 경계 안에 유지하고 지시문으로 해석하지 않아야 한다.
- **FR2.5** 결과 없음은 실패와 구분하고 검색 조건 변경을 안내해야 한다. 404 `ticket_not_found`는 실제 부재와 비가시성을 구분하지 않는 동일한 안전 응답이어야 한다.

검증 기준: ID 상세, 전체 필터 전달, 정렬, cursor 다음 페이지, limit 경계 1·20·100·101, 잘못된 cursor, 빈 목록과 비가시 404를 MockTransport로 검증해야 한다. 통계 조회는 이 도구의 첫 버전 범위가 아니다.

### FR3 — `ticket_write` 등록

- **FR3.1** 도구는 계약상 필수인 `title`, `description`, `service_id`, `impact_level`, `urgency`, `impact_note`, 시간대가 있는 `occurred_at`과 선택적인 `component_id`, `model`, `classification`만 등록 본문에 포함해야 한다.
- **FR3.2** 사용자가 서비스·컴포넌트·모델의 ID 또는 이름을 제공하면 서버는 ITSM 카탈로그 계약으로 유일하게 일치하는 활성 항목만 해석해야 한다. 모호함, 미존재, 폐기·종료 또는 서비스-컴포넌트 불일치는 등록하지 않고 안전한 후보나 수정 방법을 안내해야 한다.
- **FR3.3** `occurred_at`은 시간대가 명시된 시각 또는 사용자가 명확히 “지금”이라고 요청한 시각만 UTC로 정규화해야 한다. 누락되거나 모호하거나 시간대가 없으면 등록 전에 해당 값만 다시 물어야 한다.
- **FR3.4** 최종 등록 본문 전체를 읽기 쉬운 요약으로 보여주고 현재 사용자가 정확한 내용에 명시적으로 확인한 뒤에만 `POST /api/v2/tickets`를 호출해야 한다. 수정 또는 취소 응답은 등록을 실행하지 않아야 한다.
- **FR3.5** 확인된 한 등록 의도에는 예측 불가능한 Idempotency-Key 하나를 할당하고 사용자·대화·확인된 본문에 결합해야 한다. 동일 요청의 재전송과 안전한 재시도는 24시간 계약 안에서 같은 키를 사용하고, 본문이 달라지면 새 요약과 확인을 거친 새 의도로 처리해야 한다.

검증 기준: 필수·선택 필드, 길이·enum·시간대 경계, 카탈로그 일치·불일치, 확인 전 미호출, 취소, 같은 키·같은 본문의 단일 결과, 같은 키·다른 본문의 거부, `Idempotent-Replayed` 결과를 검증해야 한다.

### FR4 — `ticket_update` 부분 수정

- **FR4.1** 도구는 티켓 ID와 계약의 `TicketPatchIn`이 허용하는 `title`, `description`, `component_id`, `model`, `impact_level`, `urgency`, `impact_note`, `is_major`만 변경 대상으로 받아야 하며 서비스·상태·담당자·담당 그룹·전이 필드는 받지 않아야 한다.
- **FR4.2** 변경 전 현재 상세를 조회하고 ETag 또는 응답 `version`을 보존해야 한다. 사용자가 생략한 필드는 PATCH 본문에서 제외하고, 계약상 허용된 명시적 null은 다른 값과 구분해야 한다.
- **FR4.3** 대상 티켓과 변경 필드의 이전 값·새 값을 요약하고 현재 사용자·세션·대상·필드·값·version에 결합된 명시적 확인을 받은 뒤에만 PATCH를 실행해야 한다. 어느 요소라도 바뀌면 최신 값을 다시 보여주고 재확인해야 한다.
- **FR4.4** PATCH에는 확인된 version의 `If-Match`를 반드시 보내야 한다. 412 `version_conflict` 또는 428 `precondition_required`에서는 변경을 적용하거나 자동 덮어쓰지 않고 최신 상세 조회와 새 확인을 요구해야 한다.
- **FR4.5** 변경 필드가 없거나 현재 값과 동일하면 PATCH를 보내지 않아야 한다. 요청자 본인 예외, `ticket:update`, `ticket:declare_major` 등 실제 수정 권한은 로컬에서 확대하지 않고 ITSM API 판정과 오류를 따라야 한다.

검증 기준: 각 허용 필드, 금지 필드, omit/null 구분, empty update, 확인 전 미호출, 올바른 `If-Match`, 성공 시 version 증가, 412·428 미적용과 비권한 응답을 검증해야 한다.

### FR5 — 사용자 세션·위임 인증·확인 수명주기

- **FR5.1** 모든 티켓 요청의 사용자는 HttpOnly 세션 ID로 복원한 현재 서버 세션 사용자여야 하며 사용자 메시지, 도구 인자 또는 모델 출력으로 username·역할·권한을 바꿀 수 없어야 한다.
- **FR5.2** 티켓 조회·등록·수정에는 사용자 위임 토큰만 사용해야 하며 서비스 토큰은 기존 디렉터리·카탈로그 용도를 제외한 티켓 API에 사용하지 않아야 한다.
- **FR5.3** 서버 세션이 유효하고 위임 토큰이 만료됐거나 만료 임박이면 기존 갱신 경로로 한 번 갱신해 계속해야 한다. 갱신 실패, 비활성 사용자 또는 세션 만료면 ITSM 변경 요청을 보내지 않고 작업 미실행과 재로그인을 안내해야 한다.
- **FR5.4** 사용자 전환, 세션 만료, conversation 초기화, 대상·본문·version 변경은 보류 중인 등록·수정 확인을 무효화해야 하며 이전 사용자의 capability, 확인 또는 멱등 상태를 새 사용자에게 재사용하지 않아야 한다.

검증 기준: 유효 토큰, 만료 임박 갱신, 401 `token_expired` 한 번의 안전한 복구, 갱신 실패, 사용자 전환과 session/conversation 경계에서 다른 사용자 데이터나 변경 권한이 섞이지 않아야 한다.

### FR6 — 오류 정제와 재시도

- **FR6.1** 도구 오류는 허용 목록 기반의 안정적인 범주, 안전한 설명, 수정 가능한 필드 정보, 재시도 가능 여부와 필요한 경우 비밀이 아닌 request ID만 포함해야 한다. 원본 problem `detail`, 예외 문자열, 요청·응답 헤더와 비밀값은 반환·로그하지 않아야 한다.
- **FR6.2** 조회의 ITSM 티켓 요청은 최초 호출을 포함해 최대 2회만 시도해야 한다. 첫 시도의 `httpx` timeout·연결/전송 오류 또는 HTTP 500·502·503·504에 한해 250ms 고정 지연 후 한 번 재시도하며, 다른 4xx와 그 밖의 상태는 자동 재시도하지 않아야 한다. 401 `token_expired`의 토큰 갱신 후 재호출도 이 2회 상한에 포함한다. 각 시도의 전체 HTTP timeout은 기존 `ITSM_TIMEOUT_SECONDS` 설정(기본 10초)을 사용하고, 재시도 지연을 포함한 티켓 조회의 최대 대기 상한은 `2 × ITSM_TIMEOUT_SECONDS + 0.25초`여야 한다. 429 `rate_limited`에서는 서버가 기다리지 않고 즉시 안전한 오류와 검증된 `Retry-After` 초를 반환해 사용자가 그 시각 이후 다시 요청하도록 안내해야 한다.
- **FR6.3** 등록은 결과가 불명확한 경우 성공·실패를 추측하지 않고, 자동 또는 사용자 재시도 모두 최초 호출을 포함해 최대 2회 안에서 원래 Idempotency-Key와 바이트 단위로 동일한 본문을 사용해야 한다. 두 번째 시도 전에 기존 결과를 확인할 수 있으면 확인을 우선하고, 새 키로 조용히 재시도해서는 안 된다. 429에서는 자동 대기·재시도하지 않고 FR6.2의 안전한 안내를 반환해야 한다.
- **FR6.4** 수정은 전송 결과가 불명확하면 자동 재시도하지 않아야 한다. 최신 상세와 version을 다시 조회하고 변경 여부를 판별한 뒤, 아직 필요한 변경이면 새 요약과 사용자 확인을 받아야 한다.

검증 기준: 악의적 problem 본문, timeout, 연결 실패, 401, 403, 404, 409, 412, 422, 428, 429, 500·502·503·504를 주입했을 때 중복·덮어쓰기·비밀 노출 없이 각 안전 경로를 따라야 한다. MockTransport의 요청 수와 가상 clock으로 최대 2회, 250ms 지연, `2 × ITSM_TIMEOUT_SECONDS + 0.25초` 상한, 429 무대기와 `Retry-After` 반환을 판정해야 한다.

### FR7 — 기존 경험, 검증과 문서화

- **FR7.1** 기존 대화 입력창과 텍스트 메시지 흐름에서 조회·등록·수정을 완료해야 하며 새 화면, 탭, 버튼, 메뉴 또는 외부 ITSM 화면 이동을 요구하지 않아야 한다.
- **FR7.2** 목록·상세·확인·성공·빈 결과·인증 만료·충돌·등록 결과 불명확 상태는 텍스트로 구분되어야 하며 기존 키보드·화면 읽기 지원과 현재 화면 landmark·live 알림 동작을 훼손하지 않아야 한다.
- **FR7.3** 기존 사용자 전환, 서버 세션, 대화 이력·초기화, 고정 모델 이름과 reasoning effort, SDK tracing 비활성, 기존 UI·API 응답 계약을 유지해야 한다.
- **FR7.4** 신규 자동화 테스트는 FakeModel과 `httpx.MockTransport`를 사용해 실제 OpenAI API와 실제 ITSM을 호출하지 않고 세 도구의 schema·tool-call loop·HTTP 계약·안전 경계를 검증해야 한다.
- **FR7.5** README는 세 도구의 동작, 필요한 기존 설정, 실행 방법, 세션·위임 보안 경계, 테스트·coverage 실행 명령과 실제 API를 호출하는 스모크 테스트가 기본 자동화와 분리됨을 설명해야 한다.

검증 기준: 신규 테스트와 문서화된 기존 37개 테스트가 모두 통과하고, 네트워크 대역이 예상하지 않은 외부 OpenAI·ITSM 호출을 차단해야 한다.

## Non-Functional Requirements

- **NFR1 — 비밀정보와 외부 텍스트 신뢰 경계:** 액세스 토큰, client secret, OpenAI API key 또는 Authorization 값이 모델 입력, function tool schema·결과, 애플리케이션 로그, 테스트 실패 출력과 HTTP 오류 응답에 나타나는 사례가 0건이어야 한다. 고유 canary를 각 경계에 주입해 자동 검증한다. ITSM 업무·오류 텍스트는 100% 구조화된 비신뢰 데이터 경계 안에 있어야 하며, 지시문 형태의 문자열로 인해 현재 사용자, 권한, 확인 상태, 시스템·개발자 지침 또는 도구 호출이 달라지는 테스트 사례는 0건이어야 한다.
- **NFR2 — 권한·가시성 보존:** 티켓 API 호출의 100%가 현재 사용자 위임 토큰을 사용해야 하며, 서비스 토큰을 사용한 티켓 호출은 0건이어야 한다. 목록 누락과 상세 404의 의미를 로컬에서 확대 해석하지 않는다.
- **NFR3 — 데이터 무결성:** 동일 사용자·동일 Idempotency-Key·동일 본문을 반복해도 생성되는 티켓은 최대 1개여야 한다. 다른 본문 재사용은 실패해야 하며, 잘못된 `If-Match`로 성공하는 수정은 0건이어야 한다.
- **NFR4 — 응답 범위:** 한 목록 응답은 최대 100개를 넘지 않아야 하고 기본값은 20이어야 한다. 긴 목록과 상세는 조용히 잘라내지 않고 cursor 또는 추가 상세 요청으로 점진적으로 제공해야 한다.
- **NFR5 — 회귀 호환성:** 기존 37개 테스트와 신규 테스트의 통과율은 100%여야 하며 고정 모델·reasoning 설정, 사용자 전환, 세션, 대화 이력, 기존 UI·API 동작의 승인되지 않은 변경은 0건이어야 한다.
- **NFR6 — 테스트 품질:** 이번 기능에서 새로 만들거나 변경하는 애플리케이션 코드의 line coverage는 80% 이상이어야 한다. 각 테스트 가능한 계층 구현 직후 pytest 테스트를 실행하고 마지막에 전체 회귀를 실행한다.
- **NFR7 — 복구 가능성:** 모든 티켓 HTTP 호출은 `ITSM_TIMEOUT_SECONDS`(기본 10초)를 시도별 전체 timeout으로 사용해야 한다. 조회는 최대 2회와 250ms 고정 지연, 등록은 같은 멱등 키·동일 본문의 최대 2회, 수정은 자동 재시도 0회라는 FR6의 상한을 넘어서는 안 된다. 429 자동 대기는 0회이고, 사용자에게 성공하지 않은 작업을 성공으로 표시하는 경우는 0건이어야 한다.
- **NFR8 — 사용자 성과:** 대표 조회·등록·수정 시나리오는 Assistant 안에서 외부 ITSM 화면 전환 0회로 완료되어야 한다. 비교 측정은 아래 절차를 고정해 기존 ITSM 화면과 Assistant 방식을 시나리오별 각 3회 수행하고, Assistant의 각 시나리오 중앙 완료 시간이 기존 방식보다 짧아야 한다.
  - 공통 조건: 동일한 사용자 계정·역할·권한, 동일한 브라우저·장치·배포 버전과 네트워크에서 수행한다. 측정 전 방식별 1회 warm-up을 제외하고 이후 세 번 모두 warm cache로 측정하며, 각 trial 전에 생성형 일회용 테스트 데이터로 동일한 초기 상태를 복원한다.
  - 조회: 현재 사용자가 볼 수 있는 생성형 테스트 티켓의 ID와 검색어를 시작 전에 제공한다. 두 방식 모두 해당 티켓의 제목·상태·영향도·긴급도가 화면에 표시되면 종료한다.
  - 등록: 동일한 생성 규칙의 제목·설명, 활성 서비스, 영향도·긴급도·영향 범위와 시간대가 있는 발생 시각을 시작 전에 제공한다. Assistant의 명시적 확인과 기존 화면의 최종 검토·제출 동작을 모두 측정에 포함하며, 생성된 티켓 ID가 표시되면 종료한다.
  - 수정: 생성형 테스트 티켓을 동일한 기준 값과 version으로 준비하고, 시작 전에 정해진 제목·설명·컴포넌트·모델·영향도·긴급도·영향 범위 변경값을 제공한다. Assistant의 명시적 확인과 기존 화면의 최종 검토·저장 동작을 모두 포함하며, 변경값과 새 version이 표시되면 종료한다.
  - 타이머와 기록: 사용자가 준비된 시나리오 입력을 보고 첫 조작을 시작하는 순간부터 위 종료 사건까지 monotonic clock으로 잰다. 결과 표에 UTC 측정 시각, commit/version, 환경, 익명화한 계정 역할, 방식, 시나리오, trial 번호, 생성된 테스트 데이터 참조, cache·network 조건, 시작·종료 시각, 초 단위 duration, 성공 여부와 실패 사유를 기록하고 각 세 번의 중앙값을 산출한다. 제품 코드·지침에는 측정용 또는 실제 티켓 ID를 하드코딩하지 않는다.
- **NFR9 — 접근성:** 새 티켓 흐름의 모든 상태와 다음 행동은 색상·아이콘·위치에만 의존하지 않는 텍스트로 제공되어야 하며 기존 키보드 입력과 화면 읽기 흐름에서 수행 가능해야 한다.

## Constraints

- ITSM 연동의 유일한 계약 기준은 `docs/itsm/integration-guide.md`와 `docs/itsm/openapi.json`이며 `/api/v2/*`를 HTTP로 호출한다.
- 다른 저장소의 ITSM 내부 코드, 새 Agent, 별도 서비스, 새 UI, 새 배포 인프라를 추가하지 않는다.
- Agent에 노출되는 티켓 도구는 `ticket_read`, `ticket_write`, `ticket_update` 세 개뿐이다. 내부 helper나 서버 capability는 모델 도구로 노출하지 않는다.
- Python 3.13, FastAPI, OpenAI Agents SDK, httpx, SQLite와 기존 의존성 주입·앱 팩토리·pytest 패턴을 유지한다.
- 새 formatter, linter 또는 type checker를 이 기능의 의무 게이트로 추가하지 않는다.
- 실제 권한, 가시성, 카탈로그 유효성, 우선순위 계산과 서버 생성 필드는 ITSM API가 최종 결정한다.
- 고정 납기와 새 처리량·가용성 목표를 만들지 않고 기존 Assistant 운영 기준을 유지한다.

## Assumptions

- 현재 서버 세션이 유효할 때 기존 `itsm_token_for()` 경로로 사용자 위임 토큰을 갱신할 수 있다. 갱신할 수 없는 경우 FR5.3의 실패 경로가 적용된다.
- ITSM 카탈로그 조회는 기존 애플리케이션 자격증명과 배포 구조 안에서 사용할 수 있다. 이름이 유일하지 않으면 추측하지 않고 사용자에게 선택을 요청한다.
- 외부 배포 절차는 저장소 밖에 이미 존재하며 이번 변경은 그 절차와 인프라를 바꾸지 않는다.
- 기존 테스트 기준선은 승인된 Practices Discovery에 기록된 37개이며 코드 변경 전에 다시 실행해 실제 기준선을 확인한다.

## Out of Scope

- 티켓 삭제, 상태 전이, 담당자·담당 그룹 배정
- 댓글, 내부 메모, 작업 기록, 첨부파일, 변경 이력, 통계, 문제 연결, 병합, 내보내기
- ITSM v1 사용 또는 v2 계약 밖 필드 변경
- 새 Agent·서비스·화면·탭·버튼, 기존 화면 재설계, 새 CI/CD·클라우드 인프라
- 다른 저장소 코드의 import·복사, 샘플 티켓이나 특정 티켓 ID의 하드코딩
- 모델·reasoning 설정 변경, 자동 권한 확대, 보이지 않는 티켓 존재 추론

## Open Questions

None.

## Traceability Summary

| 요구사항 묶음 | 주요 상위 근거 | 후속 검증 초점 |
|---|---|---|
| FR1 | 최초 요청, `architecture.md`, `code-structure.md` | 정확히 세 도구, 서버 전용 capability, 비밀 비노출, 외부 텍스트 격리 |
| FR2 | `scope-document.md`, ITSM v2 목록·상세 계약 | 전체 필터, cursor, 404 비추론, context 제한 |
| FR3 | `scope-document.md`, Q1~Q3, 등록·멱등 계약 | 확인 결합, 카탈로그, 시각, 중복 방지 |
| FR4 | `scope-document.md`, Q1, PATCH·ETag 계약 | 허용 필드, 부분 수정, `If-Match`, 충돌 |
| FR5 | `business-overview.md`, Q1·Q4, `team-practices.md` | 현재 사용자, 갱신, 사용자 전환 격리 |
| FR6 | RAID R-02~R-08, Q5, 오류 계약 | 허용 목록 오류, 수치화된 timeout·재시도, 429 무대기 |
| FR7 | `user-flow.md`, `wireframes.md`, `team-practices.md` | 기존 경험·설정 회귀, FakeModel/MockTransport, README |
| NFR1~NFR9 | `intent-statement.md`, `initiative-brief.md`, `team-practices.md` | 비밀·프롬프트 인젝션 방어, 무결성, coverage, 접근성, 재현 가능한 사용자 성과 |
