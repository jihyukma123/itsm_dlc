# Test Results

## Sources

- `build-instructions.md`
- `integration-test-instructions.md`
- `performance-test-instructions.md`
- `security-test-instructions.md`
- U1~U4 `unit-test-instructions.md`
- U1~U4 `code-summary.md`

## Build Results

| Command | Result |
|---|---|
| `.venv/bin/python -m compileall -q app scripts` | PASS, exit 0 |
| `git diff --check` | PASS, exit 0 |

## Unit and Integration Results

| Scope | Result |
|---|---|
| U1 exact suite | PASS — 161 passed in 1.86s |
| U2 exact suite | PASS — 249 passed in 3.86s |
| U3 exact suite | PASS — 233 passed in 3.62s |
| U4 exact suite | PASS — 168 passed in 1.35s |
| Full regression under coverage | PASS — 679 passed in 8.67s |

실패, skip, xfail은 관찰되지 않았다. Unit exact 명령 사이의 test overlap은 각 Unit의 계약 경계를 독립 검증하는 것이며 전체 회귀 수와 합산하지 않는다.

## Coverage Results

```text
TOTAL 4455 statements, 449 missed, 90% covered
required floor: 80%
verdict: PASS
```

U4가 Code Generation에서 고정한 manifest-union evidence는 3838/4462 lines, 86.02%이며 finalized bundle에 보존돼 있다. 이번 Build and Test는 현재 workspace의 전체 application coverage를 새로 실행해 90%를 확인했다.

## Security and Network Results

- 실제 OpenAI·ITSM network call: 0
- unexpected network attempt: 0
- deliberate bypass blocked: 1 이상
- secret canary exposure: 0
- service-token ticket call: 0
- unauthorized mutation, hidden overwrite, duplicate create, second refresh: 0

근거는 U1~U4 exact suite와 finalized `evidence/security-network.json`이다.

## Performance Results

- automated retry/page/attempt budget: PASS
- NFR8 real-environment trials: `not_measured`
- Owning stage: `performance-validation`
- Verdict: `Unverified`

실제 환경, 테스트 사용자, credential, 생성 데이터와 cleanup 절차가 필요하며 사용자가 후속 Performance Validation에서 실행하도록 선택했다.

## Traceability Results

`aidlc engine sensor-traceability --stage build-and-test`는 `pass=false`와 uncovered 19개를 반환했다. 상세는 `cross-unit-traceability.md`에 기록한다.

## Final Stage Result

자동화 build/test와 80% coverage floor는 통과했다. 그러나 NFR8 실제 성과가 `Unverified`이고 cross-unit traceability가 `Not Met`이므로 Build and Test의 전체 결과는 **FAIL**이다. 정의된 품질 목표를 낮추거나 `Met`으로 추정하지 않았다.
