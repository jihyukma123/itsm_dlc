# ITSM 티켓 도구 팀 할당

## Sources

- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `inception/refined-mockups/mockups.md`
- `inception/domain-design/components.md`
- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-dependency.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/contract-design/contract-summary.md`
- `ideation/team-formation/team-assessment.md`
- `ideation/team-formation/mob-composition.md`
- `ideation/team-formation/skill-matrix.md`
- `inception/delivery-planning/bolt-plan.md`
- `inception/practices-discovery/team-practices.md`

## Allocation Model

mob은 한 Bolt를 함께 완결하는 교차기능 협업 그룹이다. Team Formation에서 승인된 하나의 ITSM 티켓 도구 교차기능 팀이 네 Bolt를 직렬로 소유하며, 별도 팀이나 서비스별 인수인계를 만들지 않는다. 팀이 하나이므로 다중 팀 의존성을 시각화하는 Program Board는 필요하지 않다.

## Bolt-to-Mob Assignment

| Bolt | 실행 주도 | 주 탐색·검토 | 조건부 자문 | 요청자 역할 |
|---|---|---|---|---|
| B1 Read Skeleton | 개발 책임자 | 아키텍처, 품질, 보안 | ITSM 운영 | walking-skeleton 및 CP-01/CP-03 결과 승인 |
| B2 Ticket Write | 개발 책임자 | 품질, 보안, 아키텍처 | ITSM 운영 | 등록 확인·중복 방지 및 CP-02/CP-04 결과 승인 |
| B3 Ticket Update | 개발·아키텍처 책임자 | 품질, 보안 | ITSM 운영 | 저장소·lifecycle·version 정합성과 충돌 방지 결과 승인 |
| B4 Release Assurance | 품질 책임자 | 개발, 보안, 전달 | 기존 배포 경로 책임자 | 출시 준비 결과 승인 |

AI-DLC stage lead는 해당 산출물의 실행 주도를 맡고, 지원 역할의 관점을 완료 기준과 테스트 증거에 직접 반영한다. 팀을 병렬로 분리하거나 U2와 U3를 동시에 구현하지 않는다.

## Role Responsibilities

- **요청자 / 제품 책임자:** 범위·우선순위·사용자 가치와 각 Bolt 체크포인트를 승인한다.
- **전달 책임자:** Bolt 흐름, 외부 의존성, 차단 조건과 완료 증거를 관리한다.
- **아키텍처 책임자:** U1 공통 계약, Unit·컴포넌트·migration 소유권, C-02 version/cutover, U3 `If-Match`와 retirement lifecycle 경계를 검토한다. B2에서는 R-12~R-15의 단일 재시도 정책, 결과 조회 계약 존재 여부, 원장 종결 상태와 원자적 CAS 경계를 함께 판정한다.
- **개발 책임자:** 기존 FastAPI·Agent·Runner·session 구조를 확장하고 test-after 순서로 구현한다.
- **보안·DevSecOps 책임자:** delegated token, 비밀정보 비노출, 외부 text 격리와 안전 오류를 검증한다.
- **품질 책임자:** FakeModel·MockTransport, contract/integration/regression, coverage와 network 차단 증거를 판정한다.
- **ITSM 운영 책임자:** 문서 충돌이나 실제 운영 의미가 불명확할 때만 자문한다.

## Working Agreements

- `main` 기준의 짧은 기능 브랜치와 검증 후 squash merge 방식을 유지한다.
- 기록된 `unit-major`·`serial` Construction 설정으로 B1부터 B4까지 한 번에 하나씩 진행한다.
- 각 계층 구현 직후 해당 pytest를 작성·실행하고, 각 Bolt에서 관련 통합·회귀 subset을 통과시킨다.
- CP-01~CP-04는 해당 Bolt 착수 전 아키텍처·개발·품질이 공동 검토하며, 상위 산출물 변경이 필요하면 구현보다 먼저 반영한다.
- 모든 Bolt 완료 후 사람 체크포인트를 거치며, U1은 별도의 walking-skeleton 승인이다.
- blocking 계약·보안 해석이 생기면 해당 Bolt만 정지하고 ITSM 운영 또는 보안 책임자에게 에스컬레이션한다.

## Capacity and Handoff

- 정량 FTE·고정 납기·추가 예산 제약은 확인되지 않았으므로 추정치를 만들지 않는다.
- 진행 중 작업 한도는 하나의 Bolt다.
- Bolt handoff는 코드만이 아니라 승인된 설계, 소유 테스트, 관련 회귀 결과, 비밀정보 비노출 증거를 포함한다.
- B4 완료본은 새 배포 인프라 없이 기존 FastAPI 배포 경로에 인계한다.

## Assumptions & Open Questions

- Contract Design R-12~R-18은 별도 팀으로 넘기지 않고 같은 교차기능 팀이 CP-01~CP-04와 Bolt별 테스트 증거로 닫는다. 문서 밖 ITSM operation 또는 운영 의미 확인이 필요할 때만 조건부 ITSM 운영 자문을 활성화한다.
