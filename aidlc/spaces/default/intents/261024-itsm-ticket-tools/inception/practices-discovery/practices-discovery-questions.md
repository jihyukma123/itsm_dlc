# Practices Discovery 질문

## Context

저장소 근거로 Python/FastAPI·pytest·FakeModel·MockTransport 패턴과 프로젝트 소유 CI/CD·coverage·formatter·linter·type checker 설정의 부재를 확인했다. 그러나 설정의 부재만으로 팀 의도를 확정하지 않으며, 아래 다섯 선택은 사람이 결정한다.

## Q1. 작업 브랜치와 병합 방식

이번 작업에서 Git 변경을 어떤 방식으로 통합할까요?

- A. `main`에서 짧은 기능 브랜치를 만들고 검증 후 squash merge한다.
- B. 별도 기능 브랜치 없이 `main`에 직접 커밋한다.
- C. 장기 `develop` 또는 release branch를 사용한다.
- D. 저장소 밖에 이미 정해진 브랜치·PR·병합 정책을 적용한다.
- E. 아직 결정하지 않는다.
- X. Other (please specify)

[Answer]: A. `main`에서 짧은 기능 브랜치를 만들고 검증 후 squash merge한다.

## Q2. 얇은 end-to-end 통합 조각 우선 여부

먼저 얇은 end-to-end 조각을 만들까요? A walking skeleton is a minimal version that runs the whole way through, built first to prove the pieces connect before the real features go in.

- A. Yes — `ticket_read` 최소 경로를 서버 세션 → Agent tool → 사용자 위임 ITSM HTTP → 정제된 결과 → FakeModel/MockTransport 테스트까지 먼저 연결하고 별도 확인한다.
- B. No — 별도 통합 체크포인트 없이 계획된 능력을 순서대로 구현한다.
- X. Other (please specify)

[Answer]: A. Yes — `ticket_read` 최소 경로를 서버 세션 → Agent tool → 사용자 위임 ITSM HTTP → 정제된 결과 → FakeModel/MockTransport 테스트까지 먼저 연결하고 별도 확인한다.

## Q3. 테스트 작성 방식

구현과 자동화 테스트의 작성 순서를 어떻게 확정할까요?

- A. `test-after` — 각 테스트 가능한 계층을 구현한 직후 해당 pytest 테스트를 작성·실행하고 마지막에 전체 회귀 테스트를 실행한다.
- B. `tdd` — 실패하는 테스트를 먼저 작성하고 구현으로 통과시킨다.
- C. `bdd` — 사용자 행동 시나리오를 먼저 작성하고 구현·하위 테스트를 연결한다.
- D. `atdd` — 수용 테스트를 먼저 합의·작성하고 구현한다.
- E. 아직 결정하지 않는다.
- X. Other (please specify)

[Answer]: A. `test-after` — 각 테스트 가능한 계층을 구현한 직후 해당 pytest 테스트를 작성·실행하고 마지막에 전체 회귀 테스트를 실행한다.

## Q4. 배포 방식

저장소에는 프로젝트 소유 배포 설정이 없고 신규 인프라는 범위 밖입니다. 이번 기능의 배포 관행을 어떻게 기록할까요?

- A. 새 배포 인프라를 만들지 않고 기존 배포 경로를 유지하며, 전체 자동화 테스트 통과를 승격 전 조건으로 둔다.
- B. 저장소 밖에 이미 존재하는 환경·승격·승인 절차를 지금 문서화한다.
- C. 이번 기능 범위에서 새 CI/CD 또는 배포 인프라를 만든다.
- D. 배포 관행은 이번 작업에서 정의하지 않는다.
- E. 아직 결정하지 않는다.
- X. Other (please specify)

[Answer]: A. 새 배포 인프라를 만들지 않고 기존 배포 경로를 유지하며, 전체 자동화 테스트 통과를 승격 전 조건으로 둔다.

## Q5. 코드 스타일과 자동 품질 도구

현재 Python 관용구를 유지하면서 formatter·linter·type checker를 어떻게 다룰까요?

- A. 현행 Python 3.13 관용구와 모듈 경계를 유지하고 새 formatter·linter·type checker를 이번 기능의 의무로 추가하지 않는다.
- B. Ruff와 Black을 이번 기능의 새 품질 게이트로 추가한다.
- C. Ruff, Black, mypy를 이번 기능의 새 품질 게이트로 추가한다.
- D. 저장소 밖의 기존 팀 품질 도구와 규칙을 적용한다.
- E. 아직 결정하지 않는다.
- X. Other (please specify)

[Answer]: A. 현행 Python 3.13 관용구와 모듈 경계를 유지하고 새 formatter·linter·type checker를 이번 기능의 의무로 추가하지 않는다.

## Consolidated Summary Confirmation

- Looks correct
- Request changes

[Answer]: Looks correct
