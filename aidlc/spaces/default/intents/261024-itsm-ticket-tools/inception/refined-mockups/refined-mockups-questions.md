# Refined Mockups 질문

## Sources

- `ideation/rough-mockups/wireframes.md`
- `ideation/rough-mockups/user-flow.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/practices-discovery/team-practices.md`

## Q1. 산출물의 표현 수준

새 화면이나 시각 컴포넌트를 만들지 않는 범위에서 기존 대화 화면의 티켓 상태를 어느 수준까지 구체화할까요?

- A. 실제 대화 메시지 구조, 정보 우선순위, 상태 전환, 긴 텍스트·페이지 처리까지 개발 가능한 텍스트 명세로 구체화한다. (Recommended)
- B. Rough Mockups의 상태 구조만 정돈하고 세부 메시지 구조는 구현 단계에 맡긴다.
- C. 기존 화면의 픽셀·색상·간격까지 새로 정의한다.
- X. Other (please specify)

[Answer]: A. 실제 대화 메시지 구조, 정보 우선순위, 상태 전환, 긴 텍스트·페이지 처리까지 개발 가능한 텍스트 명세로 구체화한다. (Recommended)

## Q2. 등록·수정 확인 방식

기존 입력창만 유지하면서 등록·수정의 명시적 확인을 어떻게 표현할까요?

- A. 전체 요약 뒤 `확인`, `수정`, `취소`의 의미와 예시 문구를 텍스트로 제시하고, 모호한 답변에는 실행하지 않고 다시 확인한다. (Recommended)
- B. 사용자가 자유롭게 답하게 하고 모델이 확인 의도를 추정한다.
- C. 새 확인 버튼과 취소 버튼을 추가한다.
- X. Other (please specify)

[Answer]: A. 전체 요약 뒤 `확인`, `수정`, `취소`의 의미와 예시 문구를 텍스트로 제시하고, 모호한 답변에는 실행하지 않고 다시 확인한다. (Recommended)

## Q3. 반응형·접근성 기준

현재 화면 동작을 보존하면서 어떤 기준으로 정교화할까요?

- A. 기존 breakpoint와 레이아웃을 그대로 상속하고, 모든 상태를 텍스트·키보드·기존 live 영역으로 제공하며 WCAG 2.1 AA와 긴 콘텐츠 재흐름을 명시한다. (Recommended)
- B. 모바일·태블릿·데스크톱용 새 breakpoint와 레이아웃을 정의한다.
- C. 데스크톱 흐름만 명세하고 모바일·접근성은 구현 단계에 맡긴다.
- X. Other (please specify)

[Answer]: A. 기존 breakpoint와 레이아웃을 그대로 상속하고, 모든 상태를 텍스트·키보드·기존 live 영역으로 제공하며 WCAG 2.1 AA와 긴 콘텐츠 재흐름을 명시한다. (Recommended)

## Consolidated Summary Confirmation

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
