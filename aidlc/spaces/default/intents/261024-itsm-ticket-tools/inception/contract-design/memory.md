<!-- INVARIANT: examples are single-line HTML comments so a fresh template parses to total=0 (MEMORY_EMPTY). Do NOT un-comment or split across lines. t100 guards this. -->
> This file is kept up to date automatically while the stage runs. Add observations at the review step, not by editing here directly.

## Interpretations
<!-- example: 2026-05-29T10:14:32Z — chose REST over GraphQL; the consuming team only needs CRUD, revisit if subscriptions land -->
- 2026-10-25T04:30:00Z — 이번 stage의 external surface는 새 티켓 API가 아니라 기존 chat API의 하위 호환 응답 계약이며, ITSM API v2는 Assistant가 소비하는 outbound provider 계약으로 다룬다.
- 2026-10-25T04:30:00Z — U2와 U3의 병렬성을 유지하려면 공통 schema의 필드뿐 아니라 extension 등록 방식, 오류 taxonomy와 호환 규칙까지 U1 계약으로 고정해야 한다.
- 2026-10-25T09:13:52Z — 등록 결과 조정 조회가 실패하거나 존재 여부를 확정하지 못해도 전역 attempt count가 2 미만이면 같은 key·bytes로 마지막 CAS claim·POST를 허용하고, 두 번째 불명확 결과는 terminal ambiguous로 종료한다. 이는 AC2.1.5와 24시간 멱등 계약을 계약 경계에서 확정한 선택이다.

## Deviations
<!-- example: 2026-05-29T10:14:32Z — skipped the optional caching layer the stage prose suggested; the dataset is small enough that it adds risk -->

## Tradeoffs
<!-- example: 2026-05-29T10:14:32Z — picked TDD over BDD this run; the team is unit-first and the domain is well-understood -->
- 2026-10-25T04:30:00Z — 같은 프로세스 안의 Unit 경계에는 내부 HTTP나 event bus보다 typed Python port와 shared schema가 단순하고 테스트 가능하며, 새 서비스 금지와 기존 배포 유지 조건에도 맞는다.

## Open questions
<!-- example: 2026-05-29T10:14:32Z — confirm the retention window with compliance before the next stage hardens the schema -->
- 2026-10-25T09:13:12Z — 등록 결과 조정 조회가 실패하거나 존재 여부를 확정하지 못한 경우의 마지막 POST 정책; Domain Design의 fail-closed 문구와 AC2.1.5의 same-key/same-bytes 제한 재시도 요구가 충돌하므로 Contract Design에서 사람의 선택으로 해소해야 한다.
## Interpretation

- 2026-10-25: U3 Functional Design과 NFR review에서 발견된 구현 차단 조건을 Contract Design으로 되돌렸다. U3는 별도 `ticket_tools_update_v1` storage를 소유하고 U1은 자기 confirmation namespace 안의 exact-old atomic replacement만 소유하도록 경계를 분리했다.

## Tradeoff

- 2026-10-25: U1 table에 canonical patch를 넣는 단순안 대신 U3 staged-first record를 선택했다. migration과 cleanup 표면은 늘지만 U1 confirmation authority와 U3 실행 payload ownership을 분리하고 이전 review 보존·restart 복구를 명시적으로 검증할 수 있다.
