# Team-Level Rules

> This team's affirmed practices and corrections. Loaded after `org.md` as
> strict-additive guidance; contradictions with broader policy are rejected.
> Populated by the practices-discovery affirmation gate. Edit at the gate,
> not directly.

## Way of Working

- `main`을 기준으로 수명이 짧은 기능 브랜치를 만들고, 검증을 마친 뒤 squash merge한다.
- 이번 기능은 공통 안전 경계를 먼저 확정한 다음 조회, 등록, 수정 순으로 진행한다.
- 이 방식은 저장소에서 추론한 관행이 아니라 Practices Discovery 인터뷰에서 팀이 명시적으로 선택한 방식이다. 현재 Git 이력에는 애플리케이션 기준선과 AI-DLC 설치 커밋만 있고, 프로젝트 소유 PR 설정이나 장기 브랜치 정책은 없다.

## Walking Skeleton

- 첫 번째 walking skeleton은 `ticket_read` 최소 end-to-end 조각이다. 서버 세션 → Agent function tool → 사용자 위임 ITSM HTTP → 정제된 도구 결과 → FakeModel/MockTransport 자동화 테스트 경로를 먼저 연결한다.
- 이 최소 조각은 등록·수정 기능을 추가하기 전에 별도 체크포인트에서 동작을 확인한다.
- 현재 Assistant의 사용자 세션부터 Agent 응답까지의 경로는 이미 동작하지만 ITSM 티켓 도구 경로가 없고, 승인된 기능 순서에서 조회가 첫 항목이라는 근거에 따라 팀이 이 방식을 선택했다.

## Testing Posture

- **Methodology**: test-after
- **Ordering**: 각 테스트 가능한 계층을 구현한 직후 그 계층의 pytest 테스트를 작성·실행하고, 마지막에 실제 OpenAI 호출이 없는 전체 회귀 테스트를 실행한다.
- **Methodology evidence**: 저장소에는 pytest 통합·회귀 테스트, FakeModel, `httpx.MockTransport` 패턴이 있지만 테스트 선작성 이력은 입증되지 않았으며, 팀은 현재 구조와 조직 기본값에 맞춰 `test-after`를 선택했다.
- 세 function tool의 schema·호출, ITSM v2 계약, 사용자 위임과 가시성, 토큰 갱신, 비밀정보 비노출, 등록 멱등성, 수정 `If-Match`, 오류 정제, 기존 사용자 전환·세션·대화 이력·고정 모델 회귀를 자동화 테스트로 다룬다.
- 실제 OpenAI API와 실제 ITSM은 호출하지 않고 FakeModel과 MockTransport를 사용한다. 문서화된 기존 37개 테스트 기준선은 코드 변경 전후에 재실행한다.
- feature 범위에는 조직 기준인 80% line coverage floor를 적용한다. 현재 저장소에는 coverage 측정 도구나 임계값 설정이 없으므로, 이 기능의 테스트·검증 설계에서 측정 방법을 구체화해야 한다.

## Guard Policy

<!-- Affirmed by the team. Mode: strict, relaxed, or off. Strict here holds for every intent, whatever one person asks in chat; relaxed or off here applies to every intent whose policy came from its scope, unless project.md or the person sets another; changing this line changes it. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

- 이번 기능을 위해 새 CI/CD 또는 배포 인프라를 만들지 않고 기존 배포 경로를 유지한다.
- 전체 자동화 테스트 통과를 승격 전 필수 조건으로 둔다.
- 저장소에는 프로젝트 소유 CI/CD workflow, container, cloud IaC, 환경 승격 설정 또는 배포 runbook이 없다. 이는 배포 금지의 근거가 아니며, 실제 환경·주기·승인자는 기존 저장소 밖 배포 경로가 제공하는 절차를 따른다.

## Code Style

- 현행 Python 3.13 관용구와 모듈 경계를 유지한다. `snake_case`, type hints, dataclass/Pydantic 경계, 모듈 docstring, 작은 함수, 명시적 의존성 주입을 기존 코드와 일관되게 적용한다.
- 테스트는 기존 pytest fixture·parametrize·직접 `assert` 패턴을 따른다.
- 이번 기능의 의무 품질 게이트로 새 formatter, linter 또는 type checker를 추가하지 않는다. 현재 저장소에 Ruff, Black, mypy 또는 동등한 프로젝트 설정이 없다는 사실은 해당 도구의 일반적 사용을 금지하는 규칙으로 해석하지 않는다.
## Forbidden

<!-- Team-specific forbidden patterns -->

## Mandated

<!-- Team-specific mandates -->

## Corrections

<!-- Self-learning loop appends here. -->
