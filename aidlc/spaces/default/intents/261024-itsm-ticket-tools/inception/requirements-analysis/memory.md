<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations

- 2026-10-25T03:05:53Z — 승인된 상위 산출물과 ITSM API 계약이 조회 범위, 변경 전 확인, 권한·가시성, 멱등성, 충돌, 비밀정보 비노출과 회귀 기준을 이미 확정했다. 따라서 Requirements Analysis 질문은 이전 결정을 반복하지 않고 확인 결합 범위, 카탈로그 식별, 발생 시각, 토큰 만료, 재시도처럼 테스트 결과를 바꾸는 남은 경계에만 집중한다.
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs

- 2026-10-25T03:08:42Z — 위임 토큰 만료를 곧바로 재로그인으로 처리하는 이전 UX 표현 대신, 사용자가 선택한 대로 유효한 서버 세션에서는 기존 갱신 경로를 한 번 사용하고 갱신할 수 없을 때만 변경 미실행과 재로그인을 요구한다. 이는 기존 세션 동작을 보존하면서 서비스 토큰 대체와 만료 토큰 사용을 금지한다.
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
