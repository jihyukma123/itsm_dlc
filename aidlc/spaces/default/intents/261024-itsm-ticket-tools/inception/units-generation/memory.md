<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-25T00:00:00Z — 팀이 확정한 walking skeleton은 `ticket_read`의 서버 세션 → function tool → 사용자 위임 ITSM HTTP → 정제 결과 → FakeModel/MockTransport 경로이므로 첫 Unit은 계층이 아니라 실행 가능한 수직 조각이어야 한다.
- 2026-10-25T00:00:00Z — 도메인 설계의 여섯 컴포넌트는 모두 기존 단일 FastAPI 배포 안의 논리 경계이며, Unit을 독립 서비스로 해석하면 승인된 범위를 위반한다.
- 2026-10-25T00:00:00Z — 사용자는 추천한 수직 기능·4개 Unit·병렬 가능 topology·내부 Python/SQLite 계약·단일 배포안을 모두 선택하고 분해 계획을 승인했다.
- 2026-10-25T09:08:21Z — Domain Design의 ledger-first 결정을 Unit 경계에 투영했다. U1은 공개 pending-review·`consume_once`만 소유하고 U2가 create ledger, confirmation evidence, 전역 attempt budget과 CAS 복구를 단독 소유한다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->
- 2026-10-25T04:17:14Z — 첫 검토의 R-01을 반영해 공통 confirmation-store schema와 registry extension contract를 U2가 아니라 U1 소유로 옮겨 U2·U3의 병렬 topology를 실제 구현 경계와 맞췄다.
- 2026-10-25T04:17:14Z — 첫 검토의 R-02를 반영해 통합 assurance 책임과 맞지 않는 U4의 `packaging` kind를 제거하고 full design-artifact matrix를 적용했다.
- 2026-10-25T09:08:21Z — 이전의 "공유 SQLite schema" 표현을 owner-scoped versioned schema로 좁혔다. U2는 U1 migration을 수정하거나 cross-owner transaction을 추가하지 않는다.

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-25T00:00:00Z — 등록과 수정은 공통 조회·세션·오류 경계에는 의존하지만 서로의 업무 동작에는 직접 의존하지 않으므로, 조회 skeleton 뒤 병렬 가능한 topology와 최종 통합 검증 Unit을 추천한다.
- 2026-10-25T00:00:00Z — 출시 검증·README·coverage 확인은 독립 runtime이 아니므로 `packaging` Unit으로 표현하되, 계층별 테스트는 각 기능 Unit 안에서 함께 작성·실행하는 경계를 유지한다.
- 2026-10-25T00:00:00Z — U1이 최종 세 도구를 모두 완성하지 않아도 실제 read 경로를 독립 실행하는 walking skeleton이 되도록 했고, 정확히 세 도구인 최종 Agent 조립은 U2·U3 이후 U4의 출시 검증에서 판정한다.
- 2026-10-25T09:08:21Z — U2가 ledger-first persistence와 crash recovery 복잡도를 부담하는 대신 U1·U2 사이 transaction 결합을 피하고 U2·U3의 병렬 topology를 유지한다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
