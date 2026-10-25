# 기존 화면 Design System Mapping

## Sources

- `static/index.html`
- `static/app.js`
- `static/style.css`
- `inception/refined-mockups/mockups.md`
- `inception/refined-mockups/interaction-spec.md`

## Mapping Principle

이번 기능은 기존 화면을 재설계하지 않는다. 새 티켓 상태는 기존 DOM 요소, CSS token, 메시지 class와 입력 흐름에 매핑한다. 필요한 변화는 업무 텍스트 구조와 접근성 semantics에 한정하며 새 시각 component나 stylesheet 체계를 만들지 않는다.

## Existing Tokens

| Existing token | Current role | Ticket-flow use |
|---|---|---|
| `--bg` | 페이지 배경 | 변경 없음 |
| `--panel` | 대화 패널·Assistant 메시지 배경 | 변경 없음 |
| `--text` | 기본 텍스트 | 모든 업무 레이블·값 |
| `--muted` | 보조 상태 | pending 및 비핵심 설명 |
| `--border` | 패널·메시지 경계 | 기존 Assistant 메시지 경계 |
| `--accent` | 링크형 action | 기존 대화 초기화에만 사용; 티켓용 새 control 없음 |

새 색상 token을 요구하지 않는다. 오류는 기존 `.msg.error`의 배경·텍스트를 사용하되 `티켓 작업 미완료` 같은 텍스트 제목과 alert semantics를 함께 제공한다.

## Existing Component Mapping

| UX concept | Existing implementation | Refined mapping |
|---|---|---|
| App frame | `.topbar`, `.layout`, `.panel.chat` | 그대로 유지 |
| User identity | `#user-select`, `#current-user`, `.badge` | 현재 서버 세션 표현을 그대로 유지; 티켓 메시지에서 별도 role 표시를 만들지 않음 |
| Conversation heading | `.chat-head > h2` | `대화` heading 유지 |
| Reset | `#chat-reset.link` | 기존 동작 유지; pending confirmation과 티켓 상태도 함께 무효화 |
| Conversation log | `#chat-log.chat-log` | 티켓 상태 메시지를 기존 시간순 로그에 삽입 |
| User message | `.msg.user` | 변경 없음 |
| Assistant result | `.msg.assistant` | 목록·상세·확인·성공·빈 결과를 구조화된 plain text로 표시 |
| Pending | `.msg.assistant.muted` | 업무별 처리 중 문구 |
| Error | `.msg.error` | 인증·충돌·429·결과 불명확의 안전 문구 |
| Input | `#chat-input` | 확인·수정·취소와 후속 명령을 입력하는 유일한 입력 |
| Submit | `#chat-send` | 기존 전송 동작 유지; 새 티켓 action button 없음 |

## Semantic Enhancements Without Visual Redesign

| Surface | Required semantic behavior | Visual impact |
|---|---|---|
| 신규 loading/result message | `announce=true`에서만 `role="status"`, `aria-live="polite"`, `aria-atomic="true"` | 없음 |
| 신규 immediate-action error | `announce=true`에서만 `role="alert"`, `aria-live="assertive"`, `aria-atomic="true"` | 기존 `.msg.error`만 사용 |
| 저장된 history message | `announce=false`, live role 없음 | 기존 메시지 외관 유지 |
| Assistant 업무 메시지 제목 | 기존 `대화` `h2` 아래 `h3`; 필드 묶음은 list 또는 description list | `.msg h3`는 기존 메시지 텍스트 크기·굵기·간격 안에서 구분되도록 매핑 |
| message text | DOM text node 또는 동등한 escaping | 없음 |
| focus recovery | 요청 종료 뒤 `#chat-input.focus()` | 기존 동작 유지 |
| disabled state | `state.sending` 동안 기존 input/send disabled | 기존 동작 유지 |
| chat input accessible name | `aria-label="ITSM Assistant 메시지 입력 — Enter 전송, Shift+Enter 줄바꿈"` | 없음 |

한 메시지를 여러 live region으로 쪼개지 않는다. 메시지 전체를 한 번만 알리고 동일 오류를 status와 alert 양쪽에서 중복 공지하지 않는다. `renderChatLog`로 저장된 이력을 복원할 때는 live semantics를 붙이지 않으며, 이후 새 pending/result/error에만 `announce=true`를 사용한다.

## Response-to-UI Mapping Contract

기존 API의 필수 필드와 의미를 보존하고 선택적 `presentation` metadata만 추가한다.

| Source | Existing required content | Optional addition | Rendering |
|---|---|---|---|
| 새 chat 응답 | `reply: string` | `presentation: TicketPresentationV1` | metadata가 유효하면 구조화 ticket message, 없으면 일반 fallback |
| 저장 history | `role`, `text` | `presentation: TicketPresentationV1` | metadata가 유효하면 같은 구조를 정적으로 복원, 없으면 기존 text 복원 |
| transport/API error | 기존 HTTP error 경로 | 없음 | 고정 `요청 처리 오류` 제목과 assertive `.msg.error` |

`TicketPresentationV1.kind`는 server-owned allowlist다. client는 다음 고정 map을 사용한다.

| Kind family | Heading source | Live priority when new |
|---|---|---|
| progress, input collection, list, detail, review, success | client-localized allowlist title | polite |
| unavailable, auth error, conflict, rate limit, ambiguous result | client-localized allowlist title | assertive |
| absent/invalid/unknown metadata | fixed `Assistant 응답` | polite |

- 서버의 티켓 formatter만 `presentation`을 만들며 모델과 ITSM 텍스트는 kind·block type을 선택하지 않는다.
- client는 title 문자열을 metadata에서 받아 heading으로 쓰지 않고 `kind`의 local allowlist에서 찾는다.
- `paragraph`, `fields`, `items`, `actions` block만 DOM에 매핑하고 모든 label/value는 text node로 삽입한다.
- unknown metadata는 무시하고 기존 `reply/text`를 표시한다. 기존 client는 metadata를 무시해도 동작한다.
- 저장된 metadata는 history 복원의 모양만 보존하며 `announce=false`이므로 다시 공지되지 않는다.

## Typography and Spacing

- 기존 system font stack과 `14px` body size를 유지한다.
- 기존 `.msg` padding, radius, margin, `max-width: 92%`를 유지한다.
- 기존 “대화” `h2` 아래 Assistant 업무 상태 제목은 `h3`로 렌더링하고, `.msg h3`는 기존 메시지 안에서 과도한 크기 변화 없이 상태 제목임을 구분한다.
- 업무 메시지 안의 구분은 새 CSS component 대신 줄바꿈과 일관된 텍스트 레이블로 만든다.
- 기존 `white-space: pre-wrap`과 `overflow-wrap: anywhere`를 사용한다.
- 티켓 결과를 표 형태 DOM으로 새로 만들지 않으므로 좁은 화면의 table overflow 문제를 만들지 않는다.

## Responsive Mapping

저장소의 현재 CSS에는 별도 media query가 없다. 새 breakpoint를 추가하지 않고 다음 기존 적응 동작을 유지한다.

| Existing rule | Result |
|---|---|
| `.layout { max-width: 820px; ... }` | 큰 화면에서 읽기 폭 제한 |
| `.topbar { flex-wrap: wrap; ... }` | 좁은 화면에서 brand와 사용자 선택기 줄바꿈 |
| `.user-switch { flex-wrap: wrap; ... }` | 사용자 정보 재흐름 |
| `.panel { min-width: 0; }` | flex/grid 자식 overflow 방지 |
| `.chat-form textarea { flex: 1; min-width: 0; }` | 입력창이 가용 폭에 맞게 축소 |
| `.msg { overflow-wrap: anywhere; }` | 긴 ID·제목·설명 줄바꿈 |

## Allowed and Disallowed Changes

### Allowed

- 메시지 생성 경로에 안전한 role/live semantics 추가
- 저장된 history와 신규 메시지를 구분하는 `announce` 상태 추가
- 기존 필드를 유지하는 선택적 `TicketPresentationV1` metadata와 client allowlist mapping 추가
- 기존 “대화” `h2` 아래 업무 메시지의 `h3`와 목록 semantics 추가
- textarea에 시각 변화 없는 고정 `aria-label` 추가
- 티켓 업무 결과를 plain text 구조로 구성
- pending 문구를 업무 유형에 맞게 구체화
- 서버 응답의 안전한 다음 행동을 기존 메시지에 표시
- 자동화 테스트를 위한 비시각적 상태 표식

### Disallowed

- 새 화면·panel·modal·button·menu·tab·filter form
- 기존 token 색상, 폰트, 간격, 폭의 재설계
- 사용자 전환기, 대화 이력, reset, Enter/Shift+Enter 동작 변경
- `innerHTML` 등 ITSM 텍스트를 markup으로 실행할 수 있는 렌더링
- 권한이나 가시성을 추정하는 badge·label 추가

## Implementation Handoff

구현은 `appendMessage(role, text, { presentation, announce })`처럼 기존 인자를 유지하는 하위 호환 helper를 사용한다. `renderChatLog`는 `announce: false`, 현재 요청의 pending과 새 결과·오류는 `announce: true`를 전달한다. 서버가 정제한 `TicketPresentationV1`만 allowlist renderer로 보내고, metadata가 없거나 잘못되면 `text/reply` 일반 fallback을 사용한다. 모델 reply와 ITSM 문자열은 DOM role·class·heading level·live priority·사용자 신원을 정할 수 없다.
