# 발견된 프로젝트 규칙

## Mandated

- ALWAYS 기존 OpenAI Agents SDK `Agent`와 `Runner`, 서버 측 사용자 세션, 사용자 위임 토큰 경계를 확장한다.
- ALWAYS Agent에는 `ticket_read`, `ticket_write`, `ticket_update` 세 function tool만 노출한다.
- ALWAYS `docs/itsm/integration-guide.md`와 `docs/itsm/openapi.json`을 계약 기준으로 삼아 ITSM API v2를 HTTP로 호출한다.
- ALWAYS 권한과 티켓 가시성은 ITSM API에 맡기고, 등록·수정은 명시적 사용자 확인과 계약상 정합성 보호 뒤 실행한다.
- ALWAYS 실제 OpenAI API를 호출하지 않는 자동화 테스트와 기존 전체 테스트를 통과시키고 README에 기능·실행·테스트 방법을 반영한다.
- ALWAYS 기존 사용자 전환, 세션, 대화 이력, 고정 모델·reasoning 설정, 화면과 기존 API 동작을 보존한다.
- ALWAYS 이번 기능은 `main` 기준의 짧은 기능 브랜치에서 작업하고 검증 후 squash merge한다.
- ALWAYS `ticket_read` 최소 end-to-end 경로를 walking skeleton으로 먼저 연결하고 등록·수정 구현 전에 별도 확인한다.
- ALWAYS 각 테스트 가능한 계층 구현 직후 해당 pytest 테스트를 작성·실행하고 마지막에 전체 회귀 테스트를 실행하는 `test-after` 순서를 따른다.
- ALWAYS feature 범위에서 조직 기준인 80% line coverage floor를 충족한다.
- ALWAYS 새 배포 인프라를 만들지 않고 기존 배포 경로를 유지하며 전체 자동화 테스트 통과를 승격 전 조건으로 둔다.
- ALWAYS 현행 Python 3.13 관용구와 기존 모듈 경계를 유지한다.

## Forbidden

- NEVER 새 Agent나 별도 서비스를 만들거나 다른 저장소의 ITSM 내부 코드를 import·복사한다.
- NEVER 액세스 토큰, client secret 또는 OpenAI API key를 모델 입력, function tool 결과, 로그 또는 오류 응답에 노출한다.
- NEVER 제품 지침이나 도구 코드에 샘플 티켓 또는 특정 티켓 ID를 하드코딩한다.
- NEVER 보이지 않는 티켓의 존재를 추론하거나 ITSM API가 부여하지 않은 권한을 로컬에서 확대한다.
- NEVER 등록 결과가 불명확할 때 새 멱등 상태로 중복 생성을 시도하거나, 수정 충돌에서 최신 변경을 자동 덮어쓴다.
