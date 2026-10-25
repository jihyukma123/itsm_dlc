# Practices Discovery 근거

## 조사 범위

- `aidlc/spaces/default/codekb/itsm_dlc/code-structure.md`: 모듈 경계, 앱 팩토리, 의존성 주입, 테스트 대역, 티켓 기능 변경 표면
- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md`: Python/FastAPI/Agents SDK/httpx/pytest 버전, 품질 도구와 CI 부재
- `aidlc/spaces/default/codekb/itsm_dlc/dependencies.md`: 외부·내부 의존성, 서버 세션과 위임 토큰 결합 위험
- `aidlc/spaces/default/codekb/itsm_dlc/code-quality-assessment.md`: 현재 테스트 자산, 품질 공백, 보안·정합성 부채
- `aidlc/spaces/default/codekb/itsm_dlc/architecture.md`: 단일 FastAPI 배포 단위, 세션·Agent·ITSM 경계, ticket tool 확장 지점
- `aidlc/spaces/default/codekb/itsm_dlc/business-overview.md`: 사용자 가치, 시스템 소유 경계, 핵심 비즈니스 규칙
- `README.md`, `pytest.ini`, `requirements.in`, `.gitignore`, `.env.local.example`, `.python-version`: 실행·테스트·설정·무시 규칙과 프로젝트 소유 도구 설정
- `app/agent/service.py`, `tests/test_agent.py`: Python 명명·type hint·오류 처리·pytest fixture/parametrize·FakeModel 사용 패턴
- Git 이력과 현재 branch: `main` 위 애플리케이션 기준선 및 AI-DLC 설치 커밋 두 개
- `aidlc/spaces/default/intents/261024-itsm-ticket-tools/ideation/approval-handoff/decision-log.md`: 사람이 승인한 기능 범위와 hard constraint
- `aidlc/spaces/default/memory/team.md`: 기존에 확정된 팀 관행이 없는 초기 template
- `practices-discovery-questions.md`: 다섯 팀 관행에 대한 사람의 선택과 통합 요약 확인

## 근거별 판단

| 영역 | 확인된 저장소 근거 | 근거 강도 | 인터뷰에서 확정된 팀 결정 |
|---|---|---|---|
| Way of Working | 현재 branch는 `main`; 장기 branch·PR·merge 정책 증거 없음 | 낮음 | `main` 기준의 짧은 기능 브랜치에서 작업하고 검증 후 squash merge한다. |
| Walking Skeleton | 현재 앱은 동작하지만 ticket tool end-to-end 경로가 비어 있고 조회가 첫 기능 순서 | 중간 | `ticket_read` 최소 경로를 먼저 연결하고 등록·수정 전에 별도 확인한다. |
| Testing Posture | pytest, FakeModel, MockTransport, 기존 37-test 문서 기준선; 테스트 작성 순서 증거 없음 | 중간 | `test-after`를 사용하며 계층별 구현 직후 테스트, 마지막에 전체 회귀 테스트 순서로 실행한다. |
| Deployment | 프로젝트 소유 CI/CD·container·IaC·환경 설정 없음 | 높음(부재), 낮음(실제 운영 방식) | 새 배포 인프라 없이 기존 배포 경로를 유지하고 전체 테스트 통과를 승격 전 조건으로 둔다. |
| Code Style | Python 관용 명명, type hints, dataclass/Pydantic, pytest 패턴; formatter/linter/type checker 설정 없음 | 높음 | 현행 Python 3.13 관용구와 모듈 경계를 유지하며 새 formatter/linter/type checker를 이번 기능의 의무로 추가하지 않는다. |
| Hard constraints | 정확히 세 도구, v2 HTTP, 위임 권한, 비밀 보호, 무회귀·offline tests·README가 승인됨 | 높음 | 승인된 제약만 `discovered-rules.md`의 `ALWAYS`/`NEVER` 규칙으로 유지한다. |

## 비판적 해석

- branch가 `main`이라는 사실 자체가 브랜치·병합 방식을 입증하지는 않으므로, 짧은 branch와 squash merge는 인터뷰 결정에 근거한다.
- 테스트 자산은 작성 순서를 입증하지 않으므로, `test-after`는 인터뷰 결정에 근거한다.
- CI/CD 파일 부재는 배포 금지 규칙이 아니며, 저장소 밖 기존 배포 경로를 유지한다는 결정과 구분한다.
- formatter/linter/type checker 설정 부재는 해당 도구를 금지한다는 뜻이 아니다. 이번 feature에 새 의무 도구를 추가하지 않는다는 결정만 적용한다.
- Reverse Engineering 단계는 읽기 전용이어서 문서화된 기존 37개 테스트 기준선을 재실행하지 않았다.
- feature 범위의 80% line coverage floor는 조직 기준이지만 현재 저장소에는 coverage 측정 도구나 임계값 설정이 없다.

## Interview Gaps

- 해결됨: 사람은 `main` 기준의 짧은 기능 브랜치와 squash merge를 선택했다.
- 해결됨: 사람은 `ticket_read` 최소 end-to-end 조각 우선 구현과 별도 확인을 선택했다.
- 해결됨: 사람은 계층별 구현 직후 테스트하고 마지막에 전체 회귀 테스트를 수행하는 `test-after`를 선택했다.
- 해결됨: 사람은 새 배포 인프라 없이 기존 경로를 유지하고 전체 테스트 통과를 승격 전 조건으로 두기로 선택했다.
- 해결됨: 사람은 현행 Python 3.13 관용구와 모듈 경계를 유지하고 새 formatter·linter·type checker를 이번 기능의 의무로 추가하지 않기로 선택했다.

## Integration Status

- 프로젝트 유형: Brownfield
- 기존 affirmed team baseline: None
- Support contributions: None (`Collaborators: off`)
- Interview: Complete; consolidated summary confirmed as `Looks correct`
- Promotion: Not performed
