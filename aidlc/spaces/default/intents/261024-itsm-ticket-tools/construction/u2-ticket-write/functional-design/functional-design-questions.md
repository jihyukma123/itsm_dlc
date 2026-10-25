# U2 Ticket Write 기능 설계 질문

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`
- `construction/u1-ticket-read-skeleton/functional-design/functional-design-questions.md`

승인된 상위 산출물과 U1 기능 설계에서 등록 필드, 카탈로그 해석, 발생 시각, 명시적 확인, 확인 만료, durable 멱등 원장, 재시도 상한, 오류 정제와 표시 계약을 이미 구현 가능한 수준으로 확정했다. U2 기능 설계에서 새로 판단받아야 할 미해결 항목은 없다.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U2는 U1의 요청 범위 capability, 단일 시도 gateway, 공개 `PendingMutationRepositoryV1` 연산(`put`, `get`, `confirm`, `consume_once`, `invalidate`), tool registry와 presentation mapper registry만 사용한다. U1 공통 migration·registry 구현을 수정하거나 새 cross-owner transaction port를 추가하지 않는다.
- `ticket_write`의 `prepare`와 `revise`는 허용된 등록 필드만 검증하고, 서비스·컴포넌트·모델을 유일한 활성 정규화 일치로 해석하며, 시간대가 있는 발생 시각 또는 명시적 “지금”을 한 번 UTC로 고정한다.
- `prepare`와 `revise`는 사용자에게 확인 요약을 공개하기 전에 U2 소유 `ticket_create_attempts`에 canonical request bytes, serialization version·hash, 예측 불가능한 Idempotency-Key와 `prepared` 상태를 먼저 저장한다. 그 다음 같은 payload hash에 결합된 U1 pending confirmation을 저장한다. 별도 pre-confirm table은 만들지 않는다.
- 등록 확인은 사용자·세션·대화·operation·전체 canonical payload hash에 결합한다. 같은 대화의 create 확인은 최신 하나만 유지하고 15분 또는 lifecycle·본문 변경 중 먼저 발생한 시점에 만료한다. 수정·취소된 이전 pending은 무효화하고 대응하는 미확인 ledger row는 실행 권한이 없는 종료 상태로 남긴다.
- `confirm`은 서버가 보존한 현재 raw 사용자 turn이 독립 명령 `확인` 또는 `confirm`과 정확히 일치하고 모든 binding이 일치할 때만 진행한다. U1 공개 `consume_once`가 성공했거나 같은 mutation의 이미-consumed 결과가 입증된 뒤에만 U2 ledger의 실행 claim을 시도한다.
- 확인 시 `retained_until`을 서버 확인 시각 기준 최소 24시간 뒤까지 단조 증가시킨다. 그 뒤 `prepared` 또는 재조정 가능한 `ambiguous` row를 `in_flight`로 바꾸고 `attempt_count`를 증가시키는 조건부 claim을 원자적으로 수행한다. claim 승자만 POST할 수 있고 동시 요청의 패자는 저장된 상태를 반환해 추가 POST를 보내지 않는다.
- ledger 저장과 U1 pending 공개 사이의 중단은 실행 권한 없는 orphan `prepared` row만 남긴다. U1 consume 뒤 claim 전 중단은 동일 mutation·ledger 결합으로 복구하고, claim 뒤 중단은 결과 불명확 상태로 조정한다. 어떤 복구도 새 key나 다른 bytes를 만들지 않는다.
- 등록 재조정은 저장된 동일 key와 byte-identical body만 사용하고 token 갱신과 불명확 결과 복구를 포함해 최초 시도까지 최대 두 번으로 제한한다. 429에서는 기다리거나 자동 재시도하지 않고, 최종 불명확 상태를 성공으로 표시하지 않는다.
- 성공은 생성 응답 또는 `Idempotent-Replayed` 응답에서 티켓 ID가 확인된 경우에만 성립한다. 결과·오류·로그·presentation에는 credential, 원본 problem detail과 허용되지 않은 header를 포함하지 않는다.
- U2는 기존 C-04의 `ticket_tools_create_v1.ticket_create_attempts`, `ticket_write` plugin과 create presentation mapper만 소유하며, U1의 `ticket_tools_state_v1`·`ticket_tools_history_v1`을 변경하지 않는다. 설계 추적은 AC2.1.1~AC2.1.6, AC4.1.2~AC4.1.6의 create 경로, AC5.1.2와 AC5.1.4의 create 경로를 모두 포함한다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct

## Reviewer Follow-up

### Q1. Ledger 생성 시점에 관한 상위 설계를 어떤 방향으로 정렬할까요?

A. Domain Design부터 다시 열어 ledger-first를 상위 기준으로 확정한다 (Recommended) — `TicketCreateAttemptV1`을 확인 전 `prepared`로 생성하는 수명주기를 component·Unit·contract에 명시하고, 기존 table과 U1 공개 port만 사용하는 방향을 유지한다.
B. 상위의 post-confirm ledger 기준을 유지한다 — Functional Design의 ledger-first를 철회하고, 확인 전에 exact bytes를 보존할 별도 schema 또는 공유 계약을 Units Generation·Contract Design에서 정식으로 추가한다.
X. Other (please specify)

[Answer]: A. Domain Design부터 다시 열어 ledger-first를 상위 기준으로 확정한다 (Recommended)
