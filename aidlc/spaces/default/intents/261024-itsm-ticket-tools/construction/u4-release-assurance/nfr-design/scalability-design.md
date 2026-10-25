# U4 Scalability Design

## Sources

- `../nfr-requirements/scalability-requirements.md`
- `../nfr-requirements/tech-stack-decisions.md`
- `inception/contract-design/contract-summary.md`

## Scaling Position

U4는 기존 단일-process FastAPI 배포와 두 SQLite persistence boundary를 유지한다. 새 service, queue, cache, worker, load balancer, auto-scaling rule 또는 cloud resource를 만들지 않는다. 승인된 throughput·concurrent-user 목표가 없으므로 이를 추측하지 않는다.

## Bounded-Load Patterns

| Pattern | Design | Covers |
|---|---|---|
| Page bound | server-side limit validation 1~100, default 20 | NFR4.1, NFR4.3 |
| Cursor indirection | upstream cursor와 canonical query를 server repository에 저장하고 model에는 opaque reference만 제공 | NFR4.2, NFR4.4 |
| Conversation isolation | 현재 단일 process에서 per-conversation serialization로 shared history/session mutation을 제한 | NFR3.4, NFR4.5 |
| Evidence minimization | payload 대신 stable ID, status, numeric counts, digest만 저장 | NFR1.5, NFR4.6 |

## Capacity Boundaries

- ticket list는 page당 최대 100건이다.
- release catalog는 C-03 15 + C-04 25 + C-05 27 + release check 7개의 유한 집합이다. Automation completeness는 문서 check를 제외한 73개 evidence를 판정하고 `REL.07`을 final predicate에서 별도 결합한다.
- performance trial은 method 2 × scenario 3 × measured trial 3 = 18개 record와 method/scenario별 warm-up 1회로 고정한다.
- evidence에는 ticket body, canonical mutation bytes, credential, Authorization을 저장하지 않는다.

## Failure Domain and Future Trigger

단일 process를 여러 process/instance로 바꾸면 in-memory conversation serialization과 SQLite arbitration 가정이 더 이상 충분하지 않을 수 있다. 그 변화는 이번 U4의 자동 확장이 아니라 새 architecture review trigger이며 shared lock 또는 동등한 transaction coordination을 설계해야 한다.

## Tradeoffs

- horizontal scaling을 지금 설계하지 않아 기존 배포와 일정은 유지하지만 향후 topology 변경에는 재설계가 필요하다.
- server-bound cursor record가 local state를 늘리지만 raw cursor 노출과 query tampering을 막는다.

## Assumptions & Open Questions

None.

