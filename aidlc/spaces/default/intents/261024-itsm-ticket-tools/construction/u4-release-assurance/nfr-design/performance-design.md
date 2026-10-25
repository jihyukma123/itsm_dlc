# U4 Performance Design

## Sources

- `../nfr-requirements/performance-requirements.md`
- `../nfr-requirements/tech-stack-decisions.md`
- `../../functional-design/functional-spec.md`

## Runtime Performance Patterns

| Pattern | Design | Covers |
|---|---|---|
| Bounded pagination | 기존 ticket list adapter가 limit 1~100을 검증하고 기본값 20을 materialize한다. 응답에는 raw cursor 대신 server-bound continuation reference만 둔다. | NFR4.1, NFR4.2 |
| Policy-owned retry budget | gateway는 호출당 한 번만 전송하고 TicketOperations가 read/create/update별 전체 예산과 fake-clock delay를 소유한다. | NFR7.1, NFR7.2, NFR7.3, NFR7.4 |
| No added cache | ITSM이 권위 source이므로 U4는 ticket/catalog cache를 추가하지 않는다. 측정 절차의 warm cache는 양쪽 사용자 방식의 동일 조건일 뿐 새 application cache가 아니다. | NFR4.1, NFR4.2, NFR8.4 |
| Shared client lifecycle | 기존 app-scoped asynchronous HTTP client와 설정된 per-attempt timeout을 그대로 재사용한다. 별도 connection pool이나 worker를 만들지 않는다. | NFR7.1 |

## Retry and Latency Budget

```text
read/list = attempt(ITSM_TIMEOUT_SECONDS)
          + optional fixed delay(0.25s)
          + optional final attempt(ITSM_TIMEOUT_SECONDS)
maximum = 2 * ITSM_TIMEOUT_SECONDS + 0.25s
```

- create의 preflight refresh와 no-apply 401 복구는 별도 POST 예산을 만들지 않는다.
- update는 첫 PATCH와 권위 있는 no-apply 401 뒤 최종 PATCH만 허용한다. ambiguity, 412, 428은 최신 detail과 새 확인으로 돌아간다.
- 429는 어떤 operation에서도 sleep 또는 automatic retry를 예약하지 않는다.

## NFR8 Measurement Design

`PerformanceMeasurementRecorder`는 production request path가 아니라 별도 실제 환경 절차의 record boundary다.

1. source revision, deployment, account role, browser/device/network fingerprint를 고정한다.
2. read/create/update마다 방식별 warm-up 1회를 제외한다.
3. 방식·시나리오별 trial 번호 1·2·3을 사전 생성하고 unique key로 잠근다.
4. monotonic start/end와 UTC observation time을 함께 기록한다.
5. 정상 조건 실패는 `not_met`, 미실행은 `not_measured`, 조건 위반은 session `invalid`로 분리한다.
6. 세 trial이 모두 성공한 경우만 중앙값을 계산하고 Assistant의 화면 전환 count가 모두 0인지 확인한다.

## Budget Verification

| Signal | Pass condition |
|---|---|
| read HTTP count | <= 2 |
| read retry delay | exactly 0.25s when retry occurs |
| create POST count | <= 2 across every recovery cause |
| update PATCH count | <= 1 normally; <= 2 only for authoritative no-apply 401 |
| 429 sleep count | 0 |
| raw cursor model exposure | 0 |
| list item count | <= 100 |

## Tradeoffs

- 새 cache나 async queue를 추가하지 않아 성능 최적화 폭은 제한되지만 권위 data freshness와 기존 배포를 보존한다.
- NFR8은 자동 test timing으로 대체하지 않아 실행 비용이 들지만 사용자 성과 주장의 타당성을 유지한다.

## Assumptions & Open Questions

None.

