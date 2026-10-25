# ITSM 티켓 도구 위험 및 순서 근거

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
- `inception/delivery-planning/delivery-planning-questions.md`

## Chosen Heuristic

이 계획은 walking-skeleton-first 후 risk-first를 사용한다. 즉, 핵심 통합 경로를 관통하는 최소 실행 조각을 먼저 증명한 뒤 보안·데이터 무결성 위험이 큰 능력을 한 번에 하나씩 닫는다. 별도 수치 근거가 없는 가치·긴급도·크기 점수를 임의로 만들지 않으므로 WSJF는 사용하지 않는다.

## Sequence Rationale

| 순서 | Bolt | 먼저 다루는 불확실성 | 늦출 경우 영향 |
|---:|---|---|---|
| 1 | B1 Read Skeleton | 기존 session·Agent·Runner·delegated HTTP·safe presentation이 실제로 연결되는가 | 모든 후속 도구가 잘못된 공통 경계 위에 구축될 수 있음 |
| 2 | B2 Ticket Write | 명시적 확인과 durable idempotency가 중복 생성을 막는가 | 비가역적 중복 티켓과 ambiguous recovery 결함이 늦게 발견됨 |
| 3 | B3 Ticket Update | 강한 ETag/version과 `If-Match`가 최신 변경 덮어쓰기를 막는가 | 충돌 처리와 no-op/null 의미 결함이 통합 단계까지 누적됨 |
| 4 | B4 Release Assurance | 세 도구 조립이 기존 동작·coverage·문서·보안 기준을 함께 만족하는가 | 개별 성공을 출시 준비로 잘못 판단할 수 있음 |

B1은 DAG의 유일한 시작 Unit이며 walking skeleton이다. B2와 B3는 DAG상 U1 이후 병렬 가능하지만, 팀이 승인한 등록 후 수정 순서와 한 개의 주요 능력 흐름을 따르기 위해 직렬화한다. 이는 topology를 위반하지 않는 경제적 선택이다. B4는 U1~U3 모두에 직접 의존하므로 마지막이다.

## Risk Register and Early Evidence

| Risk | 심각도 | 조기 완화 Bolt | 필수 증거 | 실패 시 행동 |
|---|---|---|---|---|
| credential 또는 원본 오류 노출 | 높음 | B1, 전 Bolt | 비밀 canary, safe error allowlist, 실제 network 0건 | 해당 Bolt 완료 보류, 보안 경계 수정 |
| 잘못된 사용자·session·conversation 결합 | 높음 | B1 | capability/cursor/pending binding과 lifecycle 테스트 | 공통 repository·context 계약 재검토 |
| 등록 중복 또는 성공 추측 | 높음 | B2 | write-before-send ledger, 동일 key/bytes, ambiguous 비성공 | U2에서 수정 후 재검증 |
| 수정 충돌 자동 덮어쓰기 | 높음 | B3 | exact quoted `If-Match`, PATCH 자동 재시도 0회, 412/428 경로 | U3에서 수정 후 재확인 |
| 외부 text가 지침 또는 HTML로 해석됨 | 높음 | B1~B4 | untrusted marker, text-node 렌더링, 공격 fixture | presentation/gateway 경계 수정 |
| 기존 session/history/UI/API 회귀 | 높음 | 각 Bolt, 최종 B4 | 관련 subset과 최종 전체 suite | 소유 Bolt로 결함 환류 |
| 변경 코드 coverage 미달 | 중간 | 각 Bolt 추적, B4 판정 | 변경 application code 80% 이상 | 누락 테스트를 소유 Bolt에 추가 |
| 계약 문서 충돌 또는 운영 해석 공백 | 중간 | 발생 Bolt | 두 문서 근거와 ITSM 운영 답변 | 해당 Bolt만 정지, 조건부 자문 |
| R-12 상위 fail-closed 문구와 승인된 마지막 재시도 정책 불일치 | 높음 | B2 | Q6 결정과 B2 상태 전이·테스트가 같은 정책을 사용 | B2 설계에서 단일 정책으로 정합화 전 POST 구현 금지 |
| R-13 권한 있는 결과 조회 operation 부재 | 높음 | B2 | ITSM 문서에 endpoint·입출력·오류 계약이 있거나, 조회 불가 전제 replay 상태 전이가 명시됨 | 문서에 없으면 조회 분기 제거; 임의 endpoint 생성 금지 |
| R-14 cancel·revise attempt 종결 상태 누락 | 높음 | B2 | terminal `cancelled`·`superseded`, 새 attempt 관계와 retention contract test | 원장 상태표와 CAS 전이가 없으면 B2 완료 보류 |
| R-15 claim과 예산 소비의 비원자성 | 높음 | B2 | 한 SQLite CAS transaction이 claim 필드와 `attempt_count + 1`을 함께 commit하고 crash 지점 테스트 통과 | 원자적 transaction과 복구 증거가 없으면 POST 실행 금지 |
| R-16 U3 저장소·migration 소유권과 상위 경계 충돌 | 높음 | B1 결정, B3 적용 | Unit·컴포넌트·계약에 한 소유자와 migration 책임이 일치하고 schema test 계획이 존재 | CP-01이 닫힐 때까지 공통 persistence 구현 금지; 영향 산출물 재정합화 |
| R-17 update execution retirement 순서·실패 의미 누락 | 높음 | B2 결정, B3 적용 | 모든 lifecycle 경로의 호출 순서, transaction, retry/compensation, 부분 실패 상태와 테스트 | CP-02가 닫힐 때까지 lifecycle mutation 구현 금지 |
| R-18 breaking 변경의 C-02 V1 유지 | 높음 | B1 결정, B3 적용 | 미배포 V1 동시 재기준화 또는 새 version/cutover 결정과 consumer·producer 호환 테스트 | CP-03이 닫힐 때까지 C-02 소비 코드 구현 금지 |

## Checkpoint Policy

- B1: integrated skeleton 동작과 공통 안전 경계를 사람이 확인한다.
- B2: 등록 확인·멱등성·ambiguous recovery 증거를 확인한다.
- B2 checkpoint는 R-12~R-15의 정책 정합성, 결과 조회 계약 또는 명시적 부재 경로, cancel·revise 종결, claim+budget 원자성을 각각 독립 증거로 포함한다.
- B3: 허용 patch·`If-Match`·충돌 복구 증거를 확인한다.
- B3 checkpoint는 R-16~R-18의 저장소·migration 소유권, retirement 순서·부분 실패 처리, C-02 version/cutover 결정이 코드·migration·계약 테스트에서 일치하는지 각각 확인한다.
- B4: 전체 suite, 80% coverage, network·secret 0건, README를 확인한다.
- 각 체크포인트는 동일한 사람 승인 Construction verification command를 사용한다.

## Alternatives Rejected

- **Value-first만 사용:** 현재 순서는 사용자 가치뿐 아니라 공통 경계·데이터 무결성 위험 감소를 명시해야 한다.
- **WSJF 점수화:** 검증된 수치 입력이 없어 점수가 정밀한 근거처럼 보일 위험이 있다.
- **U2·U3 병렬 실행:** 기술적으로 가능하지만 단일 팀의 WIP를 늘리고 U1 공통 계약 학습을 두 흐름에 동시에 전파한다.
- **U2·U3 묶음 Bolt:** 등록 멱등성과 수정 충돌의 실패 범위 및 checkpoint evidence가 섞인다.
- **U1 추가 분할:** 공통 기반만으로는 실행 가능한 end-to-end skeleton을 증명하지 못한다.

## Assumptions & Open Questions

- R-12~R-18은 Contract Design 승인 시 수용된 열린 위험이다. Delivery Planning은 이를 CP-01~CP-04와 Bolt별 완료 조건으로 승격하며, 문서화되지 않은 결과 조회 endpoint나 미결 소유권·version 선택을 가정하지 않는다.
