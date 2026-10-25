# ITSM 티켓 대화 상태 저충실도 스케치

## 목적과 범위

이 스케치는 `intent-statement.md`의 대화 안에서 업무를 완료한다는 목표, `scope-document.md`의 기존 화면 유지 경계, `intent-backlog.md`의 조회·등록·수정 능력을 사용자에게 보이는 대화 상태로 표현한다.

- 새 화면, 탭, 버튼, 카드 또는 메뉴를 제안하지 않는다.
- 기존 ITSM Assistant의 대화 영역과 입력창을 그대로 사용한다.
- 스케치의 대괄호 표기는 기존 화면 영역 또는 메시지의 의미를 나타낼 뿐 새 시각 구성요소가 아니다.
- 실제 티켓 ID나 샘플 티켓을 사용하지 않고 `[티켓 ID]`, `[제목]` 같은 자리표시자만 사용한다.

## 정보 구조

기존 화면에서 정보 우선순위는 다음과 같다.

1. 사용자의 현재 요청과 Assistant가 이해한 작업
2. 사용자가 다음 결정을 내리는 데 필요한 핵심 업무 정보
3. 데이터 변경 전 최종 변경 요약과 확인·수정·취소 선택
4. 처리 결과와 가능한 다음 행동
5. 필요한 경우에만 추가 상세 또는 다음 페이지 안내

기존 화면 영역은 변경하지 않는다.

```text
[EXISTING_HEADER_AND_USER_SWITCHER]

[MAIN_EXISTING_CONVERSATION]
  USER_MESSAGE
  ASSISTANT_MESSAGE
  USER_MESSAGE
  ASSISTANT_MESSAGE

[EXISTING_CONVERSATION_INPUT]
```

### 공통 접근성 규칙

- 기존 페이지의 `h1`과 `header`·`main`·대화 입력 `form` landmark를 유지하며 새 landmark를 만들지 않는다.
- 각 Assistant 업무 상태 메시지는 `main` 안의 `h2`로 식별하고, 한 메시지 안에서 결과 항목을 다시 나눌 때만 `h3`를 사용한다.
- 새 메시지가 추가되어도 키보드 초점은 기존 대화 입력창에 유지한다. 사용자가 입력한 확인·수정·취소 또는 재시도 명령 뒤에도 초점을 강제로 결과로 옮기지 않는다.
- 처리 중·빈 결과·조회 결과·상세·확인·성공 메시지는 기존 대화 로그의 `role="status"`, `aria-live="polite"`, `aria-atomic="true"` 영역에서 메시지 전체를 한 번 알린다.
- 인증 만료, 수정 충돌, 처리 실패처럼 즉시 행동이 필요한 오류는 `role="alert"`, `aria-live="assertive"`로 오류 요약과 다음 행동을 한 번만 알린다. 같은 내용을 반복 공지하지 않는다.

## 상태 1 — 진입과 처리 중

사용자는 별도 진입점 없이 기존 입력창에서 자연어로 티켓 업무를 요청한다.

```text
[MAIN_EXISTING_CONVERSATION]
  USER: SEARCH_TICKETS_WITH_CONDITIONS

  ASSISTANT: CHECKING_TICKETS

[EXISTING_CONVERSATION_INPUT]
```

- **처리 중 상태:** 현재 어떤 작업을 수행하는지 짧은 텍스트로 알린다.
- **빈 결과 상태:** “조건에 맞는 티켓이 없습니다”와 함께 조건 변경 또는 새 검색을 안내한다.
- **취소 가능 시점:** 데이터 변경 전 확인 단계에서는 사용자가 취소할 수 있다.
- **접근성 메모:** 기존 `h1` 아래에서 “티켓 처리 중”을 `h2`로 제공하고 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 대화 입력창에 두며 처리 시작과 빈 결과는 `role="status"`의 polite live 알림으로 한 번 전달한다.

## 상태 2 — 조회 목록

목록은 스캔하기 쉬운 핵심 정보만 제공하며 상세 내용과 다음 페이지는 필요할 때 요청한다.

```text
[MAIN_EXISTING_CONVERSATION]
  ASSISTANT: TICKETS_FOUND

  1. [TICKET_ID] | [TITLE]
     STATUS: [STATUS] | PRIORITY: [PRIORITY] | SERVICE: [SERVICE]

  2. [TICKET_ID] | [TITLE]
     STATUS: [STATUS] | PRIORITY: [PRIORITY] | SERVICE: [SERVICE]

  NEXT_PAGE_AVAILABLE
  ASK_FOR_DETAIL_OR_NEXT_PAGE

[EXISTING_CONVERSATION_INPUT]
```

- **많은 결과:** 현재 응답에는 한 페이지 분량만 보여주고 다음 결과가 있음을 명확히 알린다.
- **긴 제목:** 의미를 잃지 않는 범위에서 간결하게 제시하고 상세 요청에서 전체 허용 정보를 보여준다.
- **가시성:** 현재 사용자에게 보이는 결과만 표시하며 보이지 않는 티켓의 존재를 추측하지 않는다.
- **접근성 메모:** “티켓 검색 결과”는 `h2`, 각 티켓 제목은 `h3`로 제공하고 기존 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 입력창에 두며 결과 수, 목록, 다음 페이지 가능 여부를 `role="status"`의 polite live 알림으로 한 번 전달한다.

## 상태 3 — 티켓 상세

상세 요청에는 ITSM이 허용한 정보를 의미 있는 그룹으로 나누어 보여준다.

```text
[MAIN_EXISTING_CONVERSATION]
  USER: SHOW_DETAIL_FOR_[TICKET_ID]

  ASSISTANT: TICKET_DETAIL
  - ID: [TICKET_ID]
  - TITLE: [TITLE]
  - DESCRIPTION: [DESCRIPTION]
  - SERVICE_AND_CONFIGURATION: [ALLOWED_VALUES]
  - IMPACT_AND_URGENCY: [ALLOWED_VALUES]
  - IMPACT_SCOPE: [ALLOWED_VALUES]
  - STATUS_AND_TIMESTAMPS: [ALLOWED_VALUES]

  USER_MAY_REQUEST_ALLOWED_UPDATES

[EXISTING_CONVERSATION_INPUT]
```

- **부분 정보:** 선택 정보가 없으면 누락 사실을 일반 언어로 표시하고 값을 추측하지 않는다.
- **권한 없는 결과:** 실제 부재와 권한 문제를 구분해서 추측하지 않는다.
- **접근성 메모:** “티켓 상세 [티켓 ID]”를 `h2`, 의미별 상세 묶음을 `h3`로 제공하고 기존 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 입력창에 두며 상세 메시지 전체를 `role="status"`의 polite live 알림으로 한 번 전달한다.

## 상태 4 — 등록 전 확인

필수 정보가 모이면 실행 전에 한 번의 읽기 쉬운 요약을 제공한다.

```text
[MAIN_EXISTING_CONVERSATION]
  ASSISTANT: CREATE_TICKET_REVIEW
  - TITLE: [TITLE]
  - DESCRIPTION: [DESCRIPTION]
  - SERVICE: [SERVICE]
  - IMPACT: [IMPACT]
  - URGENCY: [URGENCY]
  - IMPACT_SCOPE: [IMPACT_SCOPE]
  - OCCURRED_AT: [TIMEZONE_AWARE_TIMESTAMP]
  - OPTIONAL_FIELDS: [PRESENT_FIELDS_ONLY]

  CHOOSE_CONFIRM_EDIT_OR_CANCEL

[EXISTING_CONVERSATION_INPUT]
```

- **확인:** 사용자가 명시적으로 확인한 뒤에만 등록한다.
- **수정:** 사용자가 바꿀 내용을 말하면 요약을 갱신한 뒤 다시 확인한다.
- **취소:** 티켓을 만들지 않고 대화에 취소 결과를 알린다.
- **접근성 메모:** “티켓 등록 내용 확인”을 `h2`로 제공하고 기존 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 확인 답변을 입력할 기존 대화 입력창에 두며 전체 요약과 확인·수정·취소 선택을 `role="status"`의 polite live 알림으로 한 번 전달한다.

## 상태 5 — 수정 전 확인과 충돌

현재 값과 변경될 값을 구분하여 의도하지 않은 수정과 최신 변경 손실을 방지한다.

```text
[MAIN_EXISTING_CONVERSATION]
  ASSISTANT: UPDATE_TICKET_REVIEW
  - TARGET: [TICKET_ID] | [TITLE]
  - TITLE: [CURRENT_VALUE] -> [NEW_VALUE]
  - IMPACT: [CURRENT_VALUE] -> [NEW_VALUE]
  - OTHER_CHANGES: [CHANGED_FIELDS_ONLY]

  CHOOSE_CONFIRM_EDIT_OR_CANCEL

  [ON_CONFLICT]
  ASSISTANT: UPDATE_NOT_APPLIED
  ASK_TO_RELOAD_LATEST_DETAIL

[EXISTING_CONVERSATION_INPUT]
```

- **변경 없음:** 바뀌는 항목이 없으면 실행하지 않고 사용자에게 알린다.
- **충돌:** 최신 변경을 덮어쓰지 않으며 자동 재시도하지 않는다.
- **접근성 메모:** “티켓 수정 내용 확인”은 `h2`, 변경 항목은 텍스트 레이블로 제공하고 기존 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 입력창에 두며 확인 요약은 polite status로, 충돌은 `role="alert"`로 “변경 미적용”과 최신 상세 재조회 행동을 한 번 전달한다.

## 상태 6 — 성공과 안전한 오류

```text
[MAIN_EXISTING_CONVERSATION]
  [SUCCESS]
  ASSISTANT: TICKET_ACTION_COMPLETED
  - ACTION: [READ_OR_CREATE_OR_UPDATE]
  - TARGET: [ALLOWED_IDENTIFIER]
  - RESULT: [SAFE_BUSINESS_SUMMARY]

  [ERROR]
  ASSISTANT: REQUEST_NOT_COMPLETED
  - SAFE_REASON: [SAFE_GENERAL_DESCRIPTION]
  - NEXT_ACTION: [EDIT_INPUT_OR_RETRY_LATER_OR_RELOAD]
```

- 원본 오류 본문, 요청 헤더, 토큰, secret, key, 내부 예외를 표시하지 않는다.
- 티켓이 보이지 않을 때 권한 유무나 실제 존재를 추측하지 않는다.
- 자동 재시도가 안전하지 않은 등록·수정은 성공 여부를 추측하지 않는다.
- **접근성 메모:** 성공은 “티켓 작업 완료”, 오류는 “티켓 작업 미완료” `h2`로 제공하고 기존 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 입력창에 두며 성공은 polite status로, 오류는 alert로 결과와 다음 행동을 한 번 전달한다.

## 상태 7 — 세션 또는 위임 인증 만료

티켓 요청을 보내기 전에 현재 서버 세션 또는 사용자 위임 인증이 유효하지 않으면 데이터 변경 없이 재인증을 안내한다.

```text
[MAIN_EXISTING_CONVERSATION]
  ASSISTANT: AUTHENTICATION_EXPIRED
  - RESULT: REQUEST_NOT_SENT_AND_NO_TICKET_CHANGE_APPLIED
  - NEXT_ACTION: SIGN_IN_AGAIN_THEN_REPEAT_THE_REQUEST

[EXISTING_CONVERSATION_INPUT]
```

- 토큰 값, 만료 시각의 내부 표현, 클라이언트 정보 또는 인증 오류 원문을 표시하지 않는다.
- 등록·수정 확인 뒤라도 인증이 유효하지 않아 ITSM 요청을 보내지 않았다면 “등록 또는 수정이 실행되지 않았습니다”라고 명시한다.
- 재로그인이 끝나기 전에는 같은 등록·수정 작업을 자동 재시도하지 않는다. 재로그인 뒤 사용자가 다시 요청해야 한다.
- **접근성 메모:** “로그인이 만료되었습니다”를 `h2`로 제공하고 기존 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 기존 입력창에 두며 작업 미실행과 재로그인 후 재요청 안내를 `role="alert"`로 한 번 전달한다.

## 상태 8 — 등록 결과 불명확과 동일 요청 재전송

사용자가 등록을 확인한 뒤 응답이 끊기거나 시간 초과가 발생하면 성공 또는 실패를 추측하지 않고 원래 요청의 중복 방지 식별 상태를 유지한다.

```text
[MAIN_EXISTING_CONVERSATION]
  ASSISTANT: CREATE_RESULT_NOT_CONFIRMED
  - RESULT: DO_NOT_ASSUME_SUCCESS_OR_FAILURE
  - DUPLICATE_PROTECTION: ORIGINAL_REQUEST_IDEMPOTENCY_STATE_RETAINED
  - NEXT_ACTION: CHECK_EXISTING_RESULT_OR_RETRY_THE_SAME_REQUEST_SAFELY

  [ON_SAME_REQUEST_RETRY]
  ASSISTANT: REUSE_ORIGINAL_IDEMPOTENCY_STATE
  - RESULT: RETURN_EXISTING_RESULT_OR_ONE_CREATE_OUTCOME

  [IF_STILL_UNRESOLVED]
  ASSISTANT: DO_NOT_START_A_NEW_CREATE_REQUEST
  - NEXT_ACTION: WAIT_OR_REQUEST_ADDITIONAL_CONFIRMATION

[EXISTING_CONVERSATION_INPUT]
```

- 같은 등록 요청을 다시 보내더라도 새 중복 방지 키를 만들지 않고 원래 요청 상태를 재사용한다.
- 기존 처리 결과를 확인할 수 있으면 새 티켓을 만들지 않고 그 결과를 안내한다.
- 안전한 동일 요청 재시도 후에도 결과가 불명확하면 새 등록을 시작하지 않고 대기 또는 추가 확인을 안내한다.
- 사용자가 제목이나 다른 등록 내용을 바꾸면 동일 요청 재시도가 아니라 새 등록 의도로 취급하고 다시 전체 요약과 명시적 확인을 받는다.
- **접근성 메모:** “티켓 등록 결과 확인 중”을 `h2`로 제공하고 기존 `header`·`main`·입력 `form` landmark를 유지한다. 초점은 입력창에 두며 결과 불명확, 중복 생성 금지, 가능한 다음 행동을 `role="alert"`로 한 번 전달한다.

## 상태 적용 원칙

- **Empty:** 결과 없음과 다음 검색 행동을 텍스트로 안내한다.
- **Loading:** 진행 중인 작업의 종류를 간결하게 알린다.
- **Success:** 완료된 작업과 안전한 결과를 분명히 표시한다.
- **Error:** 원인을 안전하게 요약하고 가능한 복구 행동을 제시한다.
- **Partial:** 다음 페이지, 선택 정보 누락, 긴 내용 또는 충돌처럼 불완전한 상태를 숨기지 않는다.
- **Authentication expired:** 작업이 전송·적용되지 않았음을 알리고 재로그인 뒤 재요청하게 한다.
- **Ambiguous create:** 원래 중복 방지 상태를 유지하고 기존 결과 확인 또는 안전한 동일 요청 재시도만 허용한다.
- 모든 상태는 기존 화면과 입력 방식을 유지하고 새 시각 구성요소를 요구하지 않는다.

