# Integration Test Instructions

## Sources

- U1~U4의 `code-generation-plan.md`, `unit-test-instructions.md`, `code-summary.md`
- U1~U4의 `nfr-requirements/` 및 `nfr-design/` 산출물
- `construction/u4-release-assurance/code-generation/traceability.json`

## Scope

Standard 전략의 핵심 경계를 재검증한다. 기존 FastAPI session에서 Agent/Runner와 정확히 세 function tool을 거쳐 MockTransport ITSM v2 adapter, SQLite state, presentation/history로 이어지는 누적 경로가 대상이다.

## Commands

각 Unit exact command를 해당 `unit-test-instructions.md` 그대로 실행한다. 중복 file이 있어도 각 Unit command는 독립 계약 검증이므로 유지하되, 전체 회귀는 마지막에 한 번만 실행한다.

```bash
.venv/bin/python -m pytest -q
```

## Required Scenarios

- `ticket_read`: list/detail, continuation binding, visibility-safe 404, retry·429·refresh budget
- `ticket_write`: ledger-first review/confirm, same key·bytes, 최대 두 POST, crash/restart와 ambiguous recovery
- `ticket_update`: strong ETag/`If-Match`, atomic confirm+consume, conflict·ambiguity와 refresh ceiling
- lifecycle: clear, switch, logout, expiry가 Runner/history와 같은 conversation lock을 사용
- release assurance: 73 automation selector, documentation evidence, immutable bundle, coverage input freeze
- compatibility: 기존 reply/history/API/UI와 model·reasoning·tracing 설정 유지

## Test Data and Isolation

- 각 테스트는 독립 temporary SQLite DB와 생성된 opaque ID를 사용한다.
- 실제 또는 샘플 운영 티켓 ID를 사용하지 않는다.
- 시간과 경쟁 순서는 fake UTC/monotonic clock 및 controllable barrier로 고정한다.
- 실패 출력에는 credential, Authorization, canonical mutation bytes, raw provider detail을 남기지 않는다.

## Pass Criteria

- 전체 suite failed 0, skipped 0
- 정확히 세 tool 조립과 모든 actor/authority binding test 통과
- hidden retry, duplicate mutation, stale publication, cross-user authority 각각 0
- 실제 외부 network call 0
