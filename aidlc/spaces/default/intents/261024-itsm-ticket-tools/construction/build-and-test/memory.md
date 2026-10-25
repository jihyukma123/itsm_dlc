<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

- 2026-10-25T20:26:05Z — 실제 환경 NFR8 측정은 사용자의 선택에 따라 예정된 Performance Validation이 소유한다; Build and Test에서는 자동화 timing을 성과 evidence로 대체하지 않고 `Unverified`로 유지했다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

- 2026-10-25T20:26:05Z — U4의 고정 manifest-union coverage evidence를 보존하면서 현재 workspace 전체 application coverage를 새로 실행했다; 이전 86.02% evidence와 현재 90% 결과를 각각 출처와 범위가 다른 증거로 유지했다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->

- 2026-10-25T20:26:05Z — U4 traceability target 네 개가 여러 path와 설명을 한 문자열에 결합해 cross-unit sensor가 19개 상위 요소를 uncovered로 판정했다; U4 traceability를 단일 실제 path 행으로 정규화해야 한다.
