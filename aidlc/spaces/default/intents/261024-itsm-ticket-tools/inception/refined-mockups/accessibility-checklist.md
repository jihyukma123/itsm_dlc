# ITSM 티켓 대화 Accessibility Checklist

## Sources and Target

- 기준: WCAG 2.1 AA
- 화면 근거: `static/index.html`, `static/app.js`, `static/style.css`
- 디자인 근거: `inception/refined-mockups/mockups.md`, `inception/refined-mockups/interaction-spec.md`
- 범위: 기존 대화 화면 안의 티켓 조회·등록·수정 상태와 다음 행동

상태 표기: `Required`는 구현과 자동/수동 검증이 필요한 항목, `Inherited`는 기존 동작을 유지해야 하는 항목, `N/A`는 이번 범위에 새 요소가 없는 항목이다.

## Perceivable

| Check | WCAG | Status | Acceptance evidence |
|---|---|---|---|
| 상태·성공·오류·다음 행동을 텍스트로 제공 | 1.3.1, 1.4.1 | Required | 색상과 class를 제거해도 메시지 의미가 유지됨 |
| 오류를 색상만으로 표현하지 않음 | 1.4.1 | Required | `티켓 작업 미완료` 제목과 복구 행동 존재 |
| 긴 ID·제목·설명 재흐름 | 1.4.10 | Required | 좁은 폭과 400% zoom에서 가로 스크롤 없이 `overflow-wrap` 적용 |
| 텍스트 대비 | 1.4.3 | Inherited | 기존 token 조합이 normal text 4.5:1 이상인지 회귀 확인 |
| UI component 대비 | 1.4.11 | Inherited | 기존 input/button/focus 경계 3:1 이상인지 회귀 확인 |
| 이미지 대체 텍스트 | 1.1.1 | N/A | 새 이미지·아이콘 없음 |

## Operable

| Check | WCAG | Status | Acceptance evidence |
|---|---|---|---|
| 모든 티켓 흐름을 키보드로 완료 | 2.1.1 | Required | Tab, textarea, Enter 전송, Shift+Enter 줄바꿈으로 조회·확인·수정·취소 완료 |
| keyboard trap 없음 | 2.1.2 | Required | 대화 로그·입력창·사용자 선택기에서 정상 이동 |
| focus 순서 유지 | 2.4.3 | Inherited | 사용자 선택기 → reset → textarea → 전송의 기존 순서 유지 |
| 요청 뒤 입력창 focus 복원 | 2.4.3, 3.2.1 | Required | 성공·오류 모두 `#chat-input`으로 복귀 |
| 보이는 focus indicator | 2.4.7 | Inherited | browser 기본 또는 기존 스타일을 제거하지 않음 |
| 새 time limit 없음 | 2.2.1 | Required | 확인에 만료 countdown을 표시하지 않음; session 변화 시 안전하게 무효화 |
| 새 pointer-only action 없음 | 2.1.1 | Required | 티켓 action button·hover-only control 없음 |

## Understandable

| Check | WCAG | Status | Acceptance evidence |
|---|---|---|---|
| 페이지 언어 유지 | 3.1.1 | Inherited | `<html lang="ko">` 유지 |
| 일관된 상태 제목과 필드 레이블 | 3.2.4 | Required | 목록·상세·확인·오류에서 동일 용어 사용 |
| 명시적 실행 확인 | 3.3.4 | Required | 등록·수정 summary와 `확인`·`수정`·`취소` 표시, 모호한 답변은 요청 0회 |
| 구체적인 입력 오류 | 3.3.1, 3.3.3 | Required | 잘못된 필드와 허용 형태, 수정 방법 표시 |
| 성공하지 않은 작업을 성공으로 표시하지 않음 | 3.3.1 | Required | 충돌·429·결과 불명확·인증 실패에 미완료 상태 명시 |
| 내부 전문용어 최소화 | 3.1.5 | Required | 사용자 문구에는 raw problem, stack trace, ETag, cursor, token을 노출하지 않음 |

## Robust

| Check | WCAG | Status | Acceptance evidence |
|---|---|---|---|
| 처리 중·일반 결과 공지 | 4.1.3 | Required | `role="status"`, polite, atomic으로 메시지 전체를 한 번 공지 |
| 즉시 행동 오류 공지 | 4.1.3 | Required | `role="alert"`, assertive, atomic으로 한 번 공지 |
| 중복 공지 방지 | 4.1.3 | Required | 같은 메시지를 status와 alert로 동시에 표시하지 않음 |
| 안전한 텍스트 삽입 | 4.1.2 | Required | ITSM 텍스트가 text node로 렌더링되고 markup·role·label을 만들지 않음 |
| 대화 입력의 고정 접근 가능 이름 | 1.3.1, 3.3.2, 4.1.2 | Required | `#chat-input`에 `aria-label="ITSM Assistant 메시지 입력 — Enter 전송, Shift+Enter 줄바꿈"`을 제공해 placeholder가 사라진 입력 상태에서도 목적과 키 동작을 식별 |
| 업무 상태 heading hierarchy | 1.3.1, 2.4.6 | Required | 기존 `대화` `h2` 아래 새 Assistant 업무 메시지 상태가 시간순 `h3`이며 필드 묶음은 list/description list로 탐색됨 |

## State Coverage

| State | Visible text | Live behavior | Focus after completion |
|---|---|---|---|
| loading | 작업 종류와 진행 중 | polite status | 입력창 복원 |
| populated list/detail | 결과 수·필드·다음 행동 | polite status | 입력창 |
| empty | 결과 없음·조건 변경 | polite status | 입력창 |
| create/update review | 전체 요약·세 선택 | polite status | 입력창 |
| success | 완료 작업·안전 결과 | polite status | 입력창 |
| validation guidance | 필드·수정 방법 | polite status | 입력창 |
| auth failure | 변경 미실행·재로그인 | assertive alert | 입력창 또는 로그인 흐름의 기존 target |
| conflict | 덮어쓰기 없음·최신 상세 | assertive alert | 입력창 |
| rate limit | 자동 재시도 없음·재요청 시점 | assertive alert | 입력창 |
| create ambiguous | 추측 없음·중복 금지·다음 행동 | assertive alert | 입력창 |

저장된 대화 이력은 위 상태를 시각적으로 유지하되 live role 없이 정적으로 렌더링한다. 초기 이력 로드와 사용자 전환에서는 과거 메시지 공지 횟수가 0회이고, 전환 뒤 발생한 새 상태만 표의 live behavior에 따라 한 번 공지된다.

## Content Stress Checklist

- [ ] 0, 1, 기본 20, 최대 100개 목록에서 의미와 읽기 순서가 유지된다.
- [ ] 매우 긴 제목·설명·영향 범위·불투명 ID가 패널 밖으로 넘치지 않는다.
- [ ] `<script>`, Markdown link, heading, bidi/control 문자가 지시나 markup이 아닌 데이터로 표시된다.
- [ ] 선택 값 누락은 빈 공간이 아니라 `값 없음`으로 이해할 수 있다.
- [ ] 긴 확인 요약 뒤에도 `확인`·`수정`·`취소` 선택이 같은 메시지에서 발견된다.
- [ ] 200%와 400% zoom에서 정보 순서와 입력 흐름이 유지된다.

## Verification Plan

### Automated

- DOM unit/integration test로 role, `aria-live`, `aria-atomic`, text escaping을 검사한다.
- 누락·잘못된 값·시간대·카탈로그 선택을 포함한 등록 입력 검증은 모두 polite status로 1회이며 assertive alert가 0회인지 검사한다.
- 모델 reply에 상태 제목·ARIA role·heading 형태 문자열을 주입해도 `presentation` metadata가 없으면 고정 일반 fallback semantics가 유지되는지 검사한다.
- 허용된 server-owned `TicketPresentationV1`만 `h3`·list·live priority로 변환되고 unknown kind/block은 escaped `reply/text` fallback으로 처리되는지 검사한다.
- 초기 `loadChatHistory`는 저장된 메시지의 live 공지 0회, 사용자 전환은 과거 메시지 공지 0회, 새 pending/result/error는 각 의도한 priority로 1회인지 검사한다.
- `#chat-input`의 접근 가능한 이름이 placeholder 표시 여부와 무관하게 목적과 Enter/Shift+Enter 동작을 포함하는지 검사한다.
- heading 탐색에서 `대화` `h2` 아래 신규 업무 상태가 시간순 `h3`로 나타나고 필드 묶음이 heading level을 건너뛰지 않는지 검사한다.
- 키보드 event test로 Enter 전송과 Shift+Enter 줄바꿈을 회귀 검증한다.
- 사용자 전환·reset 뒤 이전 티켓 메시지와 확인 상태가 남지 않는지 검증한다.
- 성공·오류 처리 뒤 active element가 기존 입력창인지 검증한다.
- 정적 HTML 검사 또는 axe 계열 검사를 사용할 경우 기존 화면 전체의 회귀 결과와 분리하지 않는다.

### Manual

- mouse 없이 조회·상세·등록 확인·수정 확인·취소·오류 복구를 수행한다.
- VoiceOver 또는 NVDA로 각 상태가 한 번만 알림되는지 확인한다.
- browser zoom 200%와 400%, 좁은 viewport에서 수평 overflow와 정보 손실을 확인한다.
- 고대비·색각 조건에서 텍스트 제목만으로 상태를 구분할 수 있는지 확인한다.

## Definition of Done

- 모든 `Required` 항목이 자동 또는 수동 증거를 가진다.
- 기존 사용자 전환, 대화 이력·초기화, 입력 방식과 focus 순서의 승인되지 않은 변경이 0건이다.
- 새 티켓 상태가 색상·아이콘·위치에만 의존하는 사례가 0건이다.
- screen reader가 같은 상태를 중복 공지하는 사례가 0건이다.
- 접근성 수정 때문에 새 화면·버튼·메뉴를 추가하지 않는다.
