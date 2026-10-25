## Review

**Verdict:** READY
**Reviewer:** aidlc-product-lead-agent
**Date:** 2026-10-25T03:44:25Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/mockups.md > State M4 — Create Review and Confirmation | 등록 흐름이 이미 유효한 draft가 만들어진 시점부터 시작한다. FR3.1~FR3.3과 AC2.1.1~AC2.1.2가 요구하는 필수값 누락, 시간대가 없거나 모호한 발생 시각, 카탈로그 이름의 복수 일치·미존재·비활성·서비스 불일치에서 사용자가 보게 될 질문, 기존 입력 보존, 후보 선택 흐름은 generic validation 문구만 있고 mockup과 전이 규칙이 없다. 따라서 개발자와 QA가 review 이전 대화 상태를 추정해야 한다. | 등록 review 앞에 필수값 수집·검증 상태를 추가하고, 각 실패 조건에서 등록 요청 0회, 이미 유효한 입력 보존, 필요한 값만 재질문, 안전한 후보 제시 또는 수정 방법, 유일한 활성 일치 뒤에만 전체 review로 이동한다는 메시지와 전이를 명시한다. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/interaction-spec.md > Existing Conversation Message > Accessibility | 모든 loading/result/error 메시지에 live semantics를 부여하지만 신규 메시지와 저장된 대화 이력 재렌더링을 구분하지 않는다. 현재 `renderChatLog`는 이력의 각 항목을 `appendMessage`로 다시 추가하므로 그대로 구현하면 페이지 로드·사용자 세션 복원 때 과거 Assistant 메시지 전체가 재공지되어 “메시지 전체를 한 번”이라는 설계 목표와 기존 화면 읽기 흐름을 깨뜨릴 수 있다. | 메시지 렌더링 계약에 신규 삽입 여부 또는 `announce` 입력을 추가하고, 저장된 이력은 live role 없이 정적으로 렌더링하며 새 pending/result/error만 한 번 공지하도록 명시한다. 초기 이력 로드·사용자 전환·새 응답 각각의 공지 횟수를 검증 항목에 추가한다. | Resolved (reviewer) |
| R-03 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/accessibility-checklist.md > Robust > 기존 form label 보존 | 체크리스트는 textarea의 접근 가능한 이름을 “회귀 확인” 대상으로만 두지만 현재 `#chat-input`에는 연결된 label, `aria-label`, `aria-labelledby`가 없고 placeholder만 있다. WCAG 2.1 AA 목표에서 실패했을 때 무엇을 구현해야 하는지가 정해져 있지 않다. | 시각 재설계 없이도 가능한 고정 접근 가능 이름 방식을 선택해 명시하고, placeholder가 사라진 입력 상태에서도 screen reader가 입력 목적과 Enter/Shift+Enter 안내를 식별하는 pass/fail 검증을 추가한다. | Resolved (reviewer) |
| R-04 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/mockups.md > Message Anatomy | 승인된 Rough Mockups는 각 업무 상태를 `h2`, 메시지 내부 그룹을 `h3`로 식별하도록 했지만 refined 문서는 상태 제목을 plain text 줄로만 정의하고 design-system mapping도 heading semantics를 매핑하지 않는다. 구현자는 승인된 의미 구조를 유지해야 하는지 이번 명세가 이를 대체하는지 판단할 수 없다. | 업무 메시지의 heading hierarchy를 유지할지, 대화 로그의 단일 heading 아래 다른 접근 가능한 구조로 대체할지 결정하고 mockups·interaction spec·design-system mapping에 동일한 semantics와 screen-reader 탐색 검증을 기록한다. | Resolved (reviewer) |
| R-05 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/interaction-spec.md > Existing Conversation Message > Inputs; aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/design-system-mapping.md > Implementation Handoff | 명세는 `title`, `body`, `heading`, `announcement`, `announce`를 입력으로 요구하지만 현재 채팅 API와 저장 이력은 각각 `reply` 문자열과 `role`·`text`만 제공한다. 어떤 경계가 상태 제목·목록·live priority를 신뢰 가능한 구조로 만들고 기존 일반 대화와 저장 이력을 어떻게 같은 규칙으로 복원하는지 정해지지 않아, 구현자가 모델 텍스트를 휴리스틱으로 파싱하거나 기존 API 계약을 임의 변경할 수 있다. | 기존 API 응답 계약을 보존하면서 현재 응답과 저장 이력을 `h3`·목록·공지 priority로 매핑하는 결정적 직렬화/렌더링 규칙과 일반 메시지 fallback을 명시하거나, 서버가 제공할 비밀 아닌 구조화 presentation metadata의 하위 호환 계약을 명시한다. 모델이 DOM role·heading level을 선택하지 않는다는 검증도 연결한다. | New |
| R-06 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/mockups.md > State M4A — Create Input Collection and Validation; aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/refined-mockups/accessibility-checklist.md > State Coverage | M4A의 누락·잘못된 값·카탈로그 검증 메시지는 `status`로 표시되지만 접근성 checklist는 validation error를 assertive `alert`로 규정한다. 동일 상태의 live priority가 충돌해 구현과 QA 결과가 달라질 수 있다. | 등록 입력 수집의 validation 상태를 polite status 또는 assertive alert 중 하나로 정하고 mockup, interaction spec, accessibility checklist의 표시와 공지 횟수를 일치시킨다. | New |

> R-01 Reviewer note: M4A와 Create Input Collection Message가 누락·오류·시간대·카탈로그 분기, 유효 입력 보존, POST 0회, 유일한 활성 일치 뒤 review 전이를 구체화한다.

> R-02 Reviewer note: `announce` 입력과 history 정적 렌더링 규칙을 추가했고, 초기 이력·사용자 전환·신규 응답의 공지 횟수를 검증 항목으로 명시했다.

> R-03 Reviewer note: `#chat-input`의 고정 `aria-label`과 placeholder 비의존 pass/fail 검증을 선택했다.

> R-04 Reviewer note: 기존 “대화” `h2` 아래 업무 상태 `h3`, 목록/설명 목록 구조와 screen-reader heading 탐색 검증을 mockups·interaction spec·design-system mapping에 일관되게 기록했다.

### Summary

기존 네 지적은 모두 구체적으로 해결됐다. 수정본은 사용자 흐름과 접근성 경계를 크게 강화했으며, 남은 핵심 판단은 현재 문자열 기반 채팅 계약에서 구조화된 메시지 semantics를 어떻게 결정적으로 만들지 명시하는 것이다.
