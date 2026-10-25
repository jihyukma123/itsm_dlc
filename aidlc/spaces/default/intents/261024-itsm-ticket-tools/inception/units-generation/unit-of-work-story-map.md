# ITSM 티켓 도구 Unit Story Map

## Sources

- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-dependency.md`

## Story-to-Unit Map

| Story ID | Implementing Unit ID | Directory | 구현 범위 |
|---|---|---|---|
| US1.1 | U1 | `u1-ticket-read-skeleton` | 검색·목록, cursor·limit·필터, 안전 재시도, 비신뢰 데이터 표시와 walking skeleton |
| US1.2 | U1 | `u1-ticket-read-skeleton` | ID 상세, 허용 projection, 404 비가시성 비구분과 상세 실패 복구 |
| US2.1 | U2 | `u2-ticket-write` | 등록 검증·카탈로그·시각, ledger-first 준비, confirmation evidence, 전역 최대 2회 POST 예산, CAS claim과 불명확 결과 복구 |
| US3.1 | U3 | `u3-ticket-update` | 허용 patch, 최신 version, 확인, `If-Match`, 충돌·불명확 결과 복구 |
| US4.1 | U1; U2; U3; U4 | `u1-ticket-read-skeleton`; `u2-ticket-write`; `u3-ticket-update`; `u4-release-assurance` | 공통 session·credential·safe error 기반, operation별 복구, lifecycle 격리와 최종 cross-tool 회귀 |
| US5.1 | U1; U2; U3; U4 | `u1-ticket-read-skeleton`; `u2-ticket-write`; `u3-ticket-update`; `u4-release-assurance` | Unit별 외부 호출 없는 테스트와 최종 세 도구·전체 회귀·coverage·README·성과 측정 검증 |

## Acceptance-Criteria Allocation

| Story | Unit | Acceptance criteria owned |
|---|---|---|
| US1.1 | U1 | AC1.1.1~AC1.1.6 |
| US1.2 | U1 | AC1.2.1~AC1.2.5 |
| US2.1 | U2 | AC2.1.1~AC2.1.6 |
| US3.1 | U3 | AC3.1.1~AC3.1.6 |
| US4.1 | U1 | AC4.1.1~AC4.1.3의 read·공통 session/capability/error 기반 |
| US4.1 | U2 | AC4.1.2~AC4.1.6의 create 인증·멱등·confirmation·lifecycle 경로 |
| US4.1 | U3 | AC4.1.2~AC4.1.6의 update 인증·충돌·confirmation·lifecycle 경로 |
| US4.1 | U4 | AC4.1.1~AC4.1.6의 cross-tool 사용자 전환·로그아웃·대화 초기화와 비밀 회귀 |
| US5.1 | U1 | AC5.1.2의 read 계약·network 차단과 AC5.1.4 read 경험 |
| US5.1 | U2 | AC5.1.2의 create 계약·공격 경로와 AC5.1.4 write 경험 |
| US5.1 | U3 | AC5.1.2의 update 계약·공격 경로와 AC5.1.4 update 경험 |
| US5.1 | U4 | AC5.1.1, AC5.1.3~AC5.1.6 및 AC5.1.2·AC5.1.4의 전체 통합 판정 |

한 Story가 여러 Unit에 배정된 경우 각 Unit의 Functional Design은 위에 배정된 해당 acceptance criteria를 추적한다. U4는 앞선 Unit의 기능 구현을 중복 소유하지 않고 통합·회귀·문서 acceptance criteria를 소유한다.

## Cross-Cutting Concerns

| Concern | Units | Allocation rule |
|---|---|---|
| 현재 사용자와 delegated token | U1, U2, U3, U4 | U1이 capability 경계를 제공하고 각 operation이 이를 사용하며 U4가 service-token 오용 0건을 통합 검증한다. |
| 비밀정보 비노출·외부 text 격리 | U1, U2, U3, U4 | 각 Unit이 자신의 schema·result·log·error를 테스트하고 U4가 cross-tool canary와 UI 회귀를 수행한다. |
| 확인 lifecycle | U1, U2, U3, U4 | U1이 공개 pending-review·`consume_once`를 제공하고 U2·U3가 operation별 binding을 구현한다. U2는 공개 evidence를 별도 ledger에 결합하며 U4가 사용자·session·conversation 전환과 durable ledger 예외를 통합 검증한다. |
| 기존 UI·API 호환 | U1, U2, U3, U4 | 각 Unit이 필요한 presentation kind를 추가하며 U4가 기존 reply와 접근성 흐름을 최종 검증한다. |
| 테스트·coverage | U1, U2, U3, U4 | test-after에 따라 각 Unit이 계층 테스트를 즉시 실행하고 U4가 전체 100% pass와 변경 코드 80% coverage를 판정한다. |

U1은 US4.1을 위한 범용 confirmation-store schema·repository·invalidation, tool registry와 presentation extension contract까지 소유한다. U2와 U3는 이 공통 acceptance 기반을 소비하되 서로의 operation별 구현에는 의존하지 않는다. U4는 kind를 생략해 통합 조립·lifecycle·회귀 책임에 전체 design-artifact matrix를 적용한다.

## Implementation Order Within Each Unit

### U1 `u1-ticket-read-skeleton`

1. ITSM read DTO·safe error와 MockTransport adapter를 구현·테스트한다.
2. session-bound capability와 read operation의 validation·retry를 구현·테스트한다.
3. 범용 confirmation store와 lifecycle invalidation, tool/presentation extension contract를 구현·계약 테스트한다.
4. 기존 Agent·Runner와 presentation에 `ticket_read`를 연결한다.
5. FakeModel end-to-end와 기존 read/session/UI 회귀를 실행한다.

### U2 `u2-ticket-write`

1. create DTO·카탈로그·시간 정규화와 validation을 구현·테스트한다.
2. U2-owned create-attempt ledger, canonical serialization과 `prepared` 선저장을 구현·테스트한다.
3. U1 pending-review·`consume_once`와 confirmation evidence 결합, 결합 전 crash 재확인과 lifecycle invalidation을 구현·테스트한다.
4. 전역 최대 2회 POST 예산, claim identity·deadline, `retryable_after_reconcile`·`retryable_no_apply`·terminal `ambiguous` 상태 전이를 구현·테스트한다.
5. POST·멱등 재조정·presentation을 연결하고 FakeModel/MockTransport 흐름을 검증한다.

### U3 `u3-ticket-update`

1. typed patch의 허용 필드·omit/null·no-op 검증을 구현·테스트한다.
2. 최신 상세·version과 update confirmation binding을 구현·테스트한다.
3. `If-Match` PATCH, 412·428과 불명확 결과 복구를 구현·테스트한다.
4. presentation을 연결하고 FakeModel/MockTransport 흐름을 검증한다.

### U4 `u4-release-assurance`

1. Agent의 최종 세 도구와 application lifecycle 조립을 검증한다.
2. network 차단·비밀 canary·cross-tool lifecycle·기존 동작 전체 회귀를 실행한다.
3. 변경 application code coverage 80% 이상을 측정하고 누락된 소유 Unit 테스트를 보완한다.
4. README와 분리된 smoke 안내, NFR8 측정 절차·기록 형식을 검증한다.

위 순서는 각 Unit 내부의 구현·test-after 순서다. Unit 사이의 경제적 전달 순서는 이 문서에서 정하지 않으며 Delivery Planning이 DAG를 바탕으로 결정한다.

## Coverage Verification

- Upstream story IDs: US1.1, US1.2, US2.1, US3.1, US4.1, US5.1
- Assigned story IDs: US1.1, US1.2, US2.1, US3.1, US4.1, US5.1
- Unassigned stories: None.
- Units with no story rows: None.
- Every acceptance criterion is assigned to at least one implementing Unit.
- Cross-cutting rows use semicolon-separated Unit IDs and matching directory names; `traceability.json`은 그중 대표 소유 Unit 하나를 target으로 사용한다.

## Assumptions & Open Questions

None.
