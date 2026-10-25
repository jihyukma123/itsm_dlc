# U1 Ticket Read Skeleton — NFR Requirements Questions

## Context

U1은 기존 애플리케이션 안에 포함되는 `library` Unit이다. 기능 설계와 상위 요구사항은 보안, 복구, 응답 범위, 회귀, 테스트 품질, 접근성 목표를 이미 측정 가능하게 확정했고, 프로젝트 제약은 새 처리량·가용성 목표나 새 인프라를 만들지 않도록 정했다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U1에 적용되는 보안 기준은 비밀 노출 0건, 외부 텍스트로 인한 신원·권한·확인·도구 동작 변경 0건, 티켓 호출의 사용자 위임 토큰 사용 100%, 서비스 토큰 티켓 호출 0건이다.
- 목록 범위는 기본 20·최대 100이며, 조회는 시도별 `ITSM_TIMEOUT_SECONDS`, 최초 포함 최대 2회, 허용된 일시 오류에만 250ms 뒤 한 번 재시도하고 429 자동 대기·재시도는 0회다.
- U1은 기존 사용자 전환·세션·대화 이력·고정 모델·reasoning·tracing·UI/API 동작을 보존하고, 실제 외부 호출 없는 테스트와 변경 애플리케이션 코드 line coverage 80% 이상을 후속 검증 기준으로 유지한다.
- 서버 세션 migration은 기존 인증·사용자·권한·위임 credential 필드의 이름, 의미, 선택성 및 저장 방식을 제거하거나 바꾸지 않고 `session_expires_at`만 additive하게 추가한다. 기존 세션 복원·토큰 갱신·사용자 전환 회귀 테스트가 이를 검증한다.
- pending mutation의 `confirm`과 `consume_once`는 별도 원자 연산으로 유지한다. `consume_once`는 정확한 actor·operation·payload·target·version binding을 다시 확인하고 `ConsumedMutationEvidenceV1 { mutation_id, confirmed_at }`만 한 번 반환하며, 이 증거만으로 POST/PATCH 권한이 생기지 않는다.
- 사용자 전환·로그아웃·대화 초기화·세션 만료는 U1의 pending/cursor/presentation/history 권한을 정리하되, U2가 소유하는 `ticket_tools_create_v1` durable create-attempt ledger를 삭제하거나 다시 쓰지 않는다.
- 같은 conversation의 Runner와 세션 만료 cleanup은 하나의 lock을 공유하고, Runner 직후 persisted `session_expires_at`을 presentation·응답 결정 전에 재검증한다. 만료됐다면 Runner 결과를 폐기하고 성공 응답이나 metadata를 게시하지 않는다.
- 새 처리량·가용성·배포 인프라 목표는 추가하지 않고 기존 Assistant 운영 기준을 유지한다. U1이 `library`이므로 이 단계 산출물은 적용 가능한 `security-requirements.md`, `tech-stack-decisions.md`, `traceability.json`으로 제한한다.
- 기술 선택은 기존 Python 3.13, FastAPI, Pydantic, OpenAI Agents SDK, httpx, SQLite, pytest/FakeModel/MockTransport를 확장하며 새 Agent·서비스·UI·formatter·linter·type checker를 도입하지 않는다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
