# ITSM 티켓 대화 Interaction Specification

## Sources

- `inception/refined-mockups/mockups.md`
- `inception/refined-mockups/refined-mockups-questions.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `static/index.html`, `static/app.js`, `static/style.css`

## Interaction Model

모든 상호작용은 기존 `#chat-input`과 `#chat-send`를 통해 이루어진다. 새 control은 추가하지 않는다. 사용자가 메시지를 보내면 기존 `.msg.user`가 추가되고, 처리 중 메시지 뒤에 `.msg.assistant` 또는 `.msg.error` 결과가 추가된다. 저장된 대화 이력을 정적으로 재구성하는 경로와 지금 발생한 메시지를 공지하는 경로를 구분한다.

```text
IDLE → USER_MESSAGE → PENDING → SAFE_RESULT → IDLE
                              ↘ SAFE_ERROR  → IDLE

CREATE_OR_UPDATE_DRAFT → REVIEW → CONFIRM → EXECUTING → RESULT
                               ↘ EDIT → UPDATED_REVIEW
                               ↘ CANCEL → NO_ACTION
```

텍스트 대체: 조회는 pending 뒤 결과 또는 안전 오류로 끝난다. 등록·수정은 draft와 review를 거쳐 명백한 확인에서만 실행하며, 수정은 새 review로 돌아가고 취소는 미실행으로 끝난다.

## Existing Conversation Message

| Field | Value |
|---|---|
| Component | Existing Conversation Message |
| Description | 사용자·Assistant·오류 텍스트를 기존 대화 로그에 표시 |
| Category | display / feedback |

### States

| State | Description | Trigger |
|---|---|---|
| user | 기존 `.msg.user` | 사용자 전송 |
| loading | 기존 `.msg.assistant.muted` | 요청 진행 중 |
| result | 기존 `.msg.assistant` | 조회·확인·성공·빈 결과 |
| error | 기존 `.msg.error` | 인증·충돌·호출 제한·처리 실패 |

### Inputs

| Input | Type | Required | Description |
|---|---|---|---|
| role | enum | yes | 기존 history의 `user`, `assistant` 역할과 기존 error 경로 |
| reply/text | string | yes | `POST /api/agent/chat`의 기존 `reply` 또는 history item의 기존 `text`; 일반 메시지와 구형 client의 fallback |
| presentation | object | no | 티켓 업무에만 서버가 만드는 비밀 아닌 구조화 metadata; 없으면 일반 메시지 fallback |
| announce | boolean | render-time | 신규 메시지만 `true`; 저장된 이력 재렌더링은 `false` |

### Backward-Compatible Presentation Contract

기존 필드와 HTTP 상태 의미는 바꾸지 않는다.

```text
POST /api/agent/chat
  { reply: string, presentation?: TicketPresentationV1 }

GET /api/agent/messages
  { messages: [{ role: string, text: string, presentation?: TicketPresentationV1 }] }

TicketPresentationV1
  version: 1
  kind: allowlisted ticket presentation kind
  blocks: ordered allowlisted display blocks
```

- `reply`, `role`, `text`는 계속 필수이며 기존 client는 선택적 `presentation`을 무시해도 같은 대화 텍스트를 사용할 수 있다.
- 기존 history row와 일반 대화에는 `presentation`이 없을 수 있다. 이때 client는 고정 제목 `Assistant 응답`과 escaped `reply/text`를 사용하고, 신규 응답이면 polite status, history 복원이면 live role 없음으로 렌더링한다.
- `presentation`은 서버의 티켓 capability/응답 formatter가 정제된 tool 결과와 서버 상태에서 생성한다. 모델 reply, ITSM 문자열, 사용자 입력은 `kind`, block type, DOM role 또는 heading level을 선택할 수 없다.
- `kind`는 `ticket_progress`, `ticket_list`, `ticket_detail`, `ticket_input`, `ticket_review`, `ticket_success`, `ticket_unavailable`, `ticket_auth_error`, `ticket_conflict`, `ticket_rate_limited`, `ticket_ambiguous`의 allowlist만 허용한다.
- client의 고정 `PRESENTATION_MAP`이 각 `kind`를 로컬 상태 제목과 live priority에 매핑한다. `ticket_input`을 포함한 진행·입력 수집·일반 결과·review·success는 polite이고, 인증 실패·충돌·429·결과 불명확은 assertive다.
- block type은 `paragraph`, `fields`, `items`, `actions`만 허용한다. 서버는 block의 label과 text를 허용 목록에서 만들고, client는 모든 업무 값을 text node로 삽입한다.
- 알 수 없는 version·kind·block, schema 불일치 또는 metadata 부재는 실패가 아니라 일반 메시지 fallback으로 처리한다. metadata 문자열을 HTML, CSS class, ARIA role 또는 heading name으로 직접 사용하지 않는다.
- 티켓 metadata는 해당 Assistant message와 함께 선택적으로 저장해 history에서 같은 `h3`·list 구조를 복원한다. 구형 row는 일반 message fallback으로 복원한다.

### Responsive Behaviour

| Context | Behaviour |
|---|---|
| 기존 유동 레이아웃 | `.msg`의 `max-width: 92%`, `pre-wrap`, `overflow-wrap: anywhere`를 유지한다. |
| 좁은 화면 | 메시지가 패널 너비에 맞게 재흐름하며 새 수평 스크롤을 만들지 않는다. |
| 긴 목록 | 기존 `.chat-log` 세로 스크롤을 사용하고 페이지 단위로 제한한다. |

### Accessibility

| Requirement | Implementation |
|---|---|
| Semantics | 기존 `#chat-log` 안에 메시지 순서대로 삽입하고, 신규 Assistant 업무 메시지는 `article` 안의 상태 제목 `h3`와 레이블이 있는 목록으로 구성한다. |
| Loading/result announcement | `announce=true`인 새 처리 중·조회·확인·성공만 `role="status"`, `aria-live="polite"`, `aria-atomic="true"`로 한 번 알린다. |
| Error announcement | `announce=true`인 새 인증 실패·충돌·호출 제한·결과 불명확만 `role="alert"`, `aria-live="assertive"`, `aria-atomic="true"`로 한 번 알린다. |
| History rendering | 초기 `loadChatHistory`와 session 복원의 저장 메시지는 `announce=false`로 렌더링하고 live role을 부여하지 않는다. |
| User switch | 기존 동작처럼 로그를 비우며 과거 메시지를 다시 공지하지 않는다. 새 사용자의 이후 신규 응답만 공지한다. |
| Focus | 새 메시지로 강제 이동하지 않고 처리 종료 뒤 기존 `#chat-input`에 초점을 돌린다. |
| Non-color meaning | 상태 제목과 다음 행동을 텍스트로 제공한다. `.msg.error` 색상만으로 실패를 표현하지 않는다. |
| General fallback | metadata가 없거나 유효하지 않으면 고정 `Assistant 응답` `h3`와 escaped `reply/text`를 사용하고 모델 텍스트로 semantics를 추론하지 않는다. |

## Ticket Result List

| Field | Value |
|---|---|
| Component | Ticket Result List |
| Description | 목록 응답을 간결한 텍스트 항목으로 표시 |
| Category | display |

### States

| State | Description | Trigger |
|---|---|---|
| loading | 티켓 검색 진행 문구 | 조회 시작 |
| populated | 한 페이지의 허용된 요약 | 결과 1건 이상 |
| empty | 결과 없음과 조건 변경 안내 | 0건 |
| partial | 다음 결과 가능 안내 | `has_more=true` |
| error | 안전 오류와 다음 행동 | 조회 실패 |

### Inputs

| Input | Type | Required | Description |
|---|---|---|---|
| items | list | yes | ID, 제목, 상태, 우선순위, 서비스의 허용된 요약 |
| has_more | boolean | yes | 다음 페이지 존재 여부 |
| next_cursor | opaque server state | conditional | 사용자에게 노출하지 않고 같은 조건·정렬에 결합 |

### Interaction Rules

- 한 페이지는 기본 20개, 최대 100개다.
- 사용자가 `다음 결과`를 요청하면 현재 대화의 직전 검색 조건·정렬과 cursor가 모두 유효할 때만 다음 페이지를 조회한다.
- 검색 조건 또는 정렬이 바뀌면 이전 cursor를 사용하지 않는다.
- 상세 요청은 사용자 메시지의 티켓 ID를 새 상세 조회로 처리한다.
- 빈 결과와 오류를 서로 다른 제목·문구로 표시한다.

## Ticket Detail Message

| Field | Value |
|---|---|
| Component | Ticket Detail Message |
| Description | 허용된 티켓 상세를 의미별 텍스트 그룹으로 표시 |
| Category | display |

### States

| State | Description | Trigger |
|---|---|---|
| populated | 허용된 상세 필드 | 조회 성공 |
| partial | 선택 필드에 `값 없음` 표시 | 값 누락 |
| unavailable | 부재·비가시성을 구분하지 않는 메시지 | 안전한 404 |
| error | 인증·호출 제한·일시 장애 | 안전 오류 |

### Interaction Rules

- ID는 불투명 문자열로 취급한다.
- 제목·설명·영향 범위의 명령문 형태 텍스트를 사용자 데이터로만 표시한다.
- HTML/Markdown을 실행 가능한 markup으로 삽입하지 않고 DOM text node 또는 동등한 escape 경로를 사용한다.

## Create Input Collection Message

| Field | Value |
|---|---|
| Component | Create Input Collection Message |
| Description | 등록 review 전 필수값·시각·카탈로그 식별을 안전하게 완성 |
| Category | feedback / input guidance |

### States

| State | Description | Transition |
|---|---|---|
| missing-required | 누락 필드와 허용 형태 안내 | 필요한 값만 재질문 |
| invalid-field | 길이·enum 등 오류와 수정 방법 안내 | 수정값 대기 |
| ambiguous-time | 시간대 포함 시각 또는 명시적 “지금” 요청 | 명확한 시각 대기 |
| catalog-ambiguous | 공개 가능한 활성 후보 표시 | 명확한 한 항목 선택 대기 |
| catalog-invalid | 미존재·비활성·서비스 불일치의 안전 설명 | 후보 선택 또는 값 수정 대기 |
| valid-draft | 모든 필드와 카탈로그 해석 완료 | Change Confirmation Message의 review-create로 이동 |

### Rules

- 모든 collection state에서 POST 요청 수는 0이다.
- 서버는 이미 유효한 입력을 draft에 보존하고 문제가 있는 필드만 갱신한다.
- 카탈로그 이름은 유일한 활성 일치에서만 ID로 해석한다. 여러 후보 중 임의 선택하지 않는다.
- 후보는 현재 계약과 사용자에게 공개 가능한 값만 포함한다.
- 필수값이 모두 유효해진 뒤에도 바로 등록하지 않고 전체 review를 표시한다.
- 누락·잘못된 값·시간대·카탈로그 선택 안내는 모두 `ticket_input`이며 polite status로 한 번 공지한다. 변경 실패나 긴급 오류로 승격하지 않는다.

## Change Confirmation Message

| Field | Value |
|---|---|
| Component | Change Confirmation Message |
| Description | 등록 전체 본문 또는 수정 diff를 실행 전에 검토 |
| Category | feedback / input guidance |

### States

| State | Description | Trigger |
|---|---|---|
| review-create | 등록 전체 필드와 선택 설명 | 유효한 등록 draft |
| review-update | 대상과 변경 전·후 값, version 결합 | 유효한 수정 draft |
| awaiting-explicit-choice | `확인`·`수정`·`취소` 안내 | review 표시 직후 |
| invalid-choice | 실행하지 않고 명확한 선택 재요청 | 모호한 답변 |
| invalidated | 이전 확인 폐기와 새 review 요구 | 사용자·세션·대화·대상·값·version 변경 |

### Inputs

| Input | Type | Required | Description |
|---|---|---|---|
| operation | enum | yes | create 또는 update |
| target | opaque string | update | 티켓 ID |
| fields | ordered mapping | yes | 등록 전체 값 또는 수정된 값만 |
| previous_values | ordered mapping | update | 변경 전 값 |
| version | opaque string/int | update | 최신 상세에서 받은 ETag 또는 version |
| confirmation_binding | server state | yes | 사용자·세션·대화·대상·본문·version 결합 정보이며 모델에 비밀을 노출하지 않음 |

### Choice Processing

| User intent | Result |
|---|---|
| 명백한 확인 | 현재 binding이 유효할 때만 변경 요청 실행 |
| 수정 + 변경값 | 실행하지 않고 draft를 갱신한 뒤 전체 review 재표시 |
| 취소 | 변경 요청 0회, 확인 상태 폐기, 미실행 안내 |
| 모호한 동의·조건부 동의·새 값 혼합 | 변경 요청 0회, 세 선택 중 하나를 다시 요청 |
| 사용자·세션·대화 전환 | 변경 요청 0회, 확인 상태 폐기 |

### Accessibility

| Requirement | Implementation |
|---|---|
| Choice discovery | `확인`, `수정`, `취소`의 의미를 visible text로 제공 |
| Keyboard | 기존 textarea와 Enter/Shift+Enter 동작만 사용 |
| Announcement | 전체 요약과 세 선택을 하나의 polite status로 알림 |
| Focus | 확인 응답을 입력할 textarea에 유지 |

## Safe Recovery Message

| Field | Value |
|---|---|
| Component | Safe Recovery Message |
| Description | 업무 실패를 비밀 없이 설명하고 안전한 다음 행동 제공 |
| Category | feedback |

### States

| State | User-visible result | Recovery | Live behavior |
|---|---|---|---|
| validation | 수정할 필드와 허용 형태 | 값 수정 | polite status |
| unavailable | 티켓을 확인할 수 없음 | ID 확인 또는 다른 검색 | assertive alert |
| forbidden | 요청을 수행할 수 없음 | 내부 절차 확인 | assertive alert |
| rate_limited | 자동 대기·재시도하지 않았음 | 유효한 `Retry-After` 이후 재요청 | assertive alert |
| auth_failed | 변경 요청 미실행 | 재로그인 후 새 확인 | assertive alert |
| version_conflict | 덮어쓰지 않았음 | 최신 상세와 새 확인 | assertive alert |
| create_ambiguous | 성공·실패를 추측하지 않음 | 기존 결과 확인 후 동일 키·동일 본문 1회 한도 | assertive alert |
| temporary_failure | 완료하지 못함 | 읽기만 정책 한도에서 재시도, 변경은 안전 규칙 적용 | assertive alert |

### Error Content Allowlist

- 안정적인 오류 범주
- 사용자에게 안전한 일반 설명
- 수정 가능한 필드 이름과 허용 형태
- 재시도 가능 여부와 다음 행동
- 필요한 경우 비밀이 아닌 request ID

원본 problem detail, 예외 문자열, 요청·응답 헤더, Authorization, 토큰, client secret, OpenAI API key는 포함하지 않는다.

## Operation Sequences

### Read

1. 사용자 메시지를 기존 로그에 추가한다.
2. pending status를 추가한다.
3. 서버 세션 사용자와 위임 인증으로 목록 또는 상세를 조회한다.
4. transient read 실패는 250ms 뒤 최대 한 번만 재시도한다.
5. 429는 기다리거나 재시도하지 않고 안전 오류와 검증된 재요청 시점을 표시한다.
6. pending을 제거하고 result 또는 error 메시지를 추가한다.
7. 입력 가능 상태와 textarea 초점을 복원한다.

### Create

1. 제공된 값 중 유효한 값은 보존하고 누락·오류 필드만 수집한다.
2. 시간대가 없는 발생 시각은 명시적 시간대 또는 “지금”을 다시 요청한다.
3. 카탈로그 이름은 유일한 활성 일치를 확인하고, 모호함·미존재·비활성·서비스 불일치는 안전한 후보 또는 수정 방법을 안내한다.
4. collection 단계의 등록 요청 수는 0이며, 모든 값이 유효할 때만 전체 등록 review와 세 선택을 표시한다.
5. 명백한 확인 및 binding 유효성을 검사한다.
6. 하나의 Idempotency-Key로 요청한다.
7. 결과 불명확 시 계약상 기존 결과 확인을 우선한다.
8. 여전히 불명확할 때만 같은 키와 바이트 동일 본문으로 한 번 더 시도한다.
9. 확인된 결과 또는 추가 자동 등록 중단 상태를 표시한다.

### Update

1. 최신 상세와 version을 조회한다.
2. 실제 변경값만 전·후 비교로 표시한다.
3. 명백한 확인 및 binding 유효성을 검사한다.
4. 확인된 version을 `If-Match`에 넣어 PATCH한다.
5. 충돌·불명확 결과에서는 자동 PATCH를 하지 않는다.
6. 최신 상세로 적용 여부를 판별하고 필요하면 새 review와 확인으로 돌아간다.

## Session and Conversation Boundaries

- 사용자 전환과 대화 초기화는 pending confirmation, capability, 멱등 상태, cursor를 즉시 폐기한다.
- 새 사용자는 이전 사용자의 도구 결과·권한·토큰을 보지 않는다.
- 사용자 전환 뒤 기존 동작대로 대화 로그를 비운다.
- 서버 세션 만료와 토큰 갱신 실패는 변경 요청 미실행을 명시한다.
- 토큰 갱신 후 등록은 같은 멱등 키·동일 본문, 수정은 변경 미적용이 보장된 401에서만 같은 확인·version·본문으로 계속한다.

## Verification Hooks

| Behaviour | Observable check |
|---|---|
| confirmation required | 확인 전 POST/PATCH 요청 수 0 |
| ambiguous confirmation | 요청 수 0, 재확인 문구 존재 |
| cancel | 요청 수 0, 미실행 문구 존재 |
| focus restoration | 요청 종료 후 `document.activeElement === chat-input` |
| live announcement | status/alert role과 atomic 속성 검사 |
| history restore announcement | 초기 이력 로드 시 저장 메시지 공지 0회 |
| user switch announcement | 로그 초기화 시 과거 메시지 공지 0회, 전환 뒤 신규 응답만 1회 |
| new response announcement | 새 pending과 최종 result/error를 각각 의도한 priority로 1회 공지 |
| heading navigation | `대화` `h2` 아래 신규 업무 메시지 상태가 시간순 `h3`로 탐색됨 |
| metadata authority | 모델 reply가 kind·title·role·heading처럼 보여도 일반 fallback이며 DOM semantics 불변 |
| backward compatibility | `presentation` 없는 chat 응답·구형 history row가 기존 `reply/text`로 표시됨 |
| structured rendering | 허용된 presentation kind/block만 로컬 map으로 `h3`·list·priority에 변환됨 |
| untrusted text | DOM text로 표시되고 신원·확인·도구 선택 불변 |
| user switch | 이전 대화·확인·cursor·멱등 상태 재사용 0 |
| rate limit | 대기 0회, 재시도 0회, 검증된 시점 안내 |
