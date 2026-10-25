# ITSM 티켓 도구 Delivery Planning 질문

## Sources

- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `inception/refined-mockups/mockups.md`
- `inception/domain-design/components.md`
- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-dependency.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/contract-design/contract-summary.md`
- `inception/practices-discovery/team-practices.md`
- `ideation/team-formation/team-assessment.md`
- `ideation/team-formation/mob-composition.md`

## Q1 [딜리버리] Bolt 순서를 설명할 경제적 휴리스틱

U1 `ticket_read` walking skeleton을 첫 Bolt로 두고 U2 `ticket_write`, U3 `ticket_update`, U4 통합 검증으로 이어가는 확정 순서를 어떤 판단 기준으로 설명할까요?

- A. **Walking-skeleton-first 후 risk-first (추천)** — U1에서 전체 경로를 먼저 증명하고, 중복 생성 위험이 있는 U2, 충돌 위험이 있는 U3, 최종 U4 순으로 불확실성을 줄입니다.
- B. **Walking-skeleton-first 후 value-first** — U1 뒤에는 사용자 가치 체감 순서를 주로 강조하고 위험 감소는 각 Bolt의 완료 조건으로 다룹니다.
- C. **WSJF 점수화** — 가치·시간 중요도·위험 감소·작업 크기를 수치화해 순서를 설명하지만, 현재 확정 순서를 위해 추가 추정치가 필요합니다.
- X. Other (please specify)

[Answer]: A. Walking-skeleton-first 후 risk-first

## Q2 [구현] Unit을 Bolt로 묶는 크기

네 Unit을 어떤 Bolt 경계로 실행할까요?

- A. **Unit당 한 Bolt (추천)** — U1, U2, U3, U4를 각각 독립 완료·검증해 소유권과 실패 범위를 명확히 합니다.
- B. **U2와 U3를 한 Bolt로 묶기** — 공통 U1 뒤 등록·수정을 함께 구현해 단계 수를 줄이지만 위험과 검토 범위가 커집니다.
- C. **U1을 둘로 분할** — 공통 기반과 조회 end-to-end를 나눠 더 작은 작업으로 만들지만 walking skeleton 체크포인트까지 시간이 늘어납니다.
- X. Other (please specify)

[Answer]: A. Unit당 한 Bolt

## Q3 [품질] Bolt별 검증 체크포인트

필수 U1 walking-skeleton 승인 외에 어느 수준으로 Bolt별 검증을 멈춰 확인할까요?

- A. **모든 Bolt에 체크포인트 (추천)** — U2 멱등성, U3 낙관적 잠금, U4 전체 회귀 증거를 각 경계에서 확인합니다.
- B. **U1과 U4만 체크포인트** — 중간 승인 부담은 줄지만 U2·U3 결함이 최종 통합까지 누적될 수 있습니다.
- C. **U1 필수 체크포인트만 사용** — 이후를 연속 실행해 속도는 높지만 보안·데이터 변경 위험에 대한 사람 검토가 가장 늦습니다.
- X. Other (please specify)

[Answer]: A. 모든 Bolt에 체크포인트

## Q4 [테스트] 각 기능 Bolt의 완료 증거

U1~U3에서 어떤 테스트 범위를 Bolt 완료 조건으로 둘까요?

- A. **소유 계층 테스트 + 관련 통합·회귀 subset (추천)** — 각 Bolt에서 빠르게 결함을 막고, U4에서 전체 suite와 80% coverage를 최종 판정합니다.
- B. **매 Bolt마다 전체 suite와 coverage** — 가장 이른 회귀 탐지가 가능하지만 반복 실행 비용이 큽니다.
- C. **Unit 전용 테스트만** — 가장 빠르지만 기존 세션·대화·화면 회귀 발견이 U4로 늦어집니다.
- X. Other (please specify)

[Answer]: A. 소유 계층 테스트 + 관련 통합·회귀 subset

## Q5 [외부 의존성] ITSM 운영·보안 자문을 차단 조건으로 둘지

현재 계약 문서가 명확한 동안 외부 자문을 선행 승인으로 요구할까요?

- A. **조건부 자문만 사용 (추천)** — 문서 충돌, 운영 의미 불명확, 보안 정책 해석 필요가 생길 때만 해당 Bolt를 멈추고 자문합니다.
- B. **U1 전에 선행 확인 필수** — 구현 전 운영·보안 확인을 받아 위험을 낮추지만 지금 확인되지 않은 대기 의존성이 생깁니다.
- C. **U2·U3 전에 각각 확인 필수** — 변경 작업만 별도 확인하지만 등록·수정 착수가 외부 일정에 종속됩니다.
- X. Other (please specify)

[Answer]: A. 조건부 자문만 사용

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- 첫 Bolt는 U1 `ticket_read` walking skeleton이며, 이후 U2 등록, U3 수정, U4 출시 보증을 직렬로 진행합니다.
- Unit당 하나의 Bolt를 사용하고, 네 Bolt 모두 완료 증거를 사람 체크포인트에서 확인합니다.
- U1~U3은 소유 계층 테스트와 관련 통합·회귀 subset을 통과하고, U4에서 전체 suite와 변경 application code 80% coverage를 최종 판정합니다.
- 외부 자문은 계약 충돌, 운영 의미 공백 또는 보안 정책 해석이 실제로 필요할 때만 해당 Bolt의 조건부 차단 의존성으로 활성화합니다.
- Contract Design에서 수용된 R-12~R-15는 B2의 명시적 위험과 완료 증거로 추적합니다. 상위 재시도 정책 정합성, 결과 조회 계약의 존재 여부, 취소·수정 원장 종결 상태, CAS claim과 `attempt_count + 1`의 원자성을 구현 전에 고정하고 테스트합니다.
- Contract Design에서 수용된 R-16~R-18은 B1~B3의 교차 Unit 선행조건으로 추적합니다. U3 저장소·migration 소유권을 Unit·컴포넌트 경계와 정합화하고, 모든 lifecycle 경로의 U3 retirement 순서·실패 처리를 고정하며, C-02를 미배포 V1 동시 재기준화 또는 새 version 전환 중 하나로 구현 전에 확정합니다. U4는 이 결정들의 통합 계약 테스트를 수행합니다.

Does this all look correct before I generate the artifact?
- Looks correct
- Request changes

[Answer]: Looks correct
