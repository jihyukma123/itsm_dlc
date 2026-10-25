# U3 Ticket Update 단위 테스트 지침

## Test Strategy and Ordering

- 전략은 `standard`, 방법론은 `test-after`다. 각 테스트 가능한 계층을 구현한 직후 그 계층의 pytest를 작성·실행하고 다음 계층으로 이동한다.
- 각 논리 구성요소는 5~8개 수준의 집중 테스트를 기본으로 하며, 상태·오류·동시성 parameter matrix는 이 수를 넘을 수 있다.
- Unit 테스트는 실제 OpenAI API나 실제 ITSM API를 호출하지 않는다. FakeModel, `httpx.MockTransport`, temporary SQLite, injected UTC/monotonic clock과 controllable barrier만 사용한다.
- U3가 새로 만들거나 변경한 애플리케이션 executable line의 coverage는 80% 이상이어야 한다. Threshold를 낮추거나 skip/xfail/coverage exclusion으로 결과를 맞추지 않는다.
- 이 파일의 모든 실행 명령은 U3가 소유하거나 U3 consumer/provider 경계를 검증하는 정확한 테스트 파일 집합으로 제한한다. Repository-wide regression과 production data-at-rest evidence는 다음 검증 단계의 별도 공통 gate가 실행한다.

## Framework Setup and Runner Readiness

- Interpreter: repository의 `.venv/bin/python`만 사용한다.
- Runner: pinned `pytest==9.1.1`; discovery는 기존 `pytest.ini`의 `testpaths = tests`를 유지한다.
- Coverage: pinned `coverage==7.17.0`과 기존 `scripts/changed_line_coverage.py`를 재사용한다.
- 별도 formatter, linter, type checker, test plugin 또는 live-service credential을 추가하지 않는다.

Application code를 변경하기 전에 U3가 소비하는 현재 U1 provider/gateway/registry 경계가 실행 가능한지 다음 정확한 prerequisite set으로 확인한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_operations.py tests/test_ticket_repositories.py tests/test_ticket_gateway.py tests/test_ticket_registry.py
```

실패가 있으면 U3 변경과 분리해 test ID와 기존 상태를 기록한다. 승인된 C-02 contract를 additive하게 구현할 수 없는 provider drift는 구현으로 우회하지 않고 중단한다.

## Layer Commands

### Models and canonicalization

`update_models.py`와 complete C-02 provider DTO를 구현한 직후 실행한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_update_models.py tests/test_ticket_update_u1_contract.py
```

최소 검증 범위:

- 여덟 허용 필드의 정상값·경계값, unknown/forbidden field 거부
- omitted와 explicit `null` 구분, empty/no-op의 안전 실패
- serialization version 1 fixed-key-order compact UTF-8 bytes와 SHA-256 안정성
- `TicketUpdateToolInputV1` action별 required/forbidden 조합
- public schema/result에서 credential, canonical bytes와 raw `IfMatchVersion` 부재
- complete `UpdatePendingReplacementV1` field/const/row-count invariant

### Migration and repository

U3 migration과 execution repository를 구현한 직후 실행한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_update_migration.py tests/test_ticket_update_repository.py tests/test_ticket_update_u1_contract.py
```

최소 검증 범위:

- U1 state migration 뒤/U3 plugin 전 ordering, repeated startup no-op, forced rollback
- schema/index/marker fingerprint와 actor-scope active partial unique index
- staged/active/retired round-trip, exact old retire + new promote의 단일 transaction
- U1 replacement failure 때 이전 review 유지와 staged orphan cleanup
- exact actor/session/conversation/ticket locator cardinality 0 또는 1
- hash/ticket/version/actor tamper와 truncated row의 PATCH authority 0
- one-shot refresh reservation, generation recovery, repeated cleanup의 부작용 0

### U1 provider and transport boundaries

Atomic confirm+consume provider, one-attempt PATCH와 update refresh port를 구현한 직후 실행한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_update_u1_contract.py tests/test_ticket_update_operations.py
```

최소 검증 범위:

- prepare/revise exact-old replacement의 committed/affected-row evidence
- validation·insert failure rollback, stale expected-old와 actor mismatch
- current-turn/full-binding 검증과 confirmed intermediate state 없는 atomic consume
- U2 create의 기존 분리 `confirm`/`consume_once` behavior 보존
- exact delegated bearer category, canonical PATCH bytes와 stored `If-Match`
- gateway method당 HTTP attempt 1회, raw body/header/problem/exception 비노출
- durable reservation 전 refresh port 호출 0, execution당 호출/exchange 최대 1
- credential commit 후 response loss에서 higher generation recovery와 second refresh 0

### Business operations

Prepare/revise/confirm/PATCH/reconciliation policy를 구현한 직후 실행한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_update_operations.py tests/test_ticket_update_repository.py
```

최소 검증 범위:

- strong quoted-decimal ETag와 body version exact match만 review 허용
- invalid ETag, empty/no-op, confirm 전·binding mismatch·expiry에서 PATCH 0
- read attempt 최대 2, 허용 outcome만 250ms 뒤 second call, deadline 밖 호출 0
- 일반 PATCH 최대 1; authoritative no-apply `token_expired`만 동일 bytes/version second/final call
- 412·428·timeout·transport·untyped/second 401·429의 hidden PATCH retry 0
- 완전 적용 + version 증가만 success; partial/different/no-read는 new review 또는 ambiguous
- deterministic concurrent confirm/revise winner 1, loser consume/PATCH 0

### Tool, integration, lifecycle and security

Tool/plugin/presentation/runtime/lifecycle를 연결한 직후 실행한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_update_tool.py tests/test_ticket_update_integration.py tests/test_ticket_update_lifecycle.py tests/test_ticket_update_security.py
```

최소 검증 범위:

- model-visible schema는 action/ticket/patch/pending만 포함하고 server context는 숨김
- cumulative runtime tool 이름은 `ticket_read`, `ticket_write`, `ticket_update`이고 U1 checkpoint seam은 그대로 유지
- FakeModel/MockTransport prepare→review→confirm→success와 cancel/revise/conflict/ambiguous 흐름
- active 후 response loss + restart에서 같은 actor/ticket pending만 복구하고 duplicate pending 0
- switch/logout/clear/session expiry를 같은 conversation lock 아래 처리하고 U2 ledger는 보존
- review, confirmation, cancel, success, auth error, conflict, rate limit, ambiguous, invalidated, unavailable의 plain-text label과 next action
- credential/Authorization/patch/`IfMatch`/raw problem canary leak 0, malicious external text의 instruction effect 0
- process-level DNS/TCP default-deny와 deliberate bypass probe

## Exact U3 Unit Command

모든 U3 layer 구현 뒤 다음 exact file set을 한 번 실행한다.

```bash
.venv/bin/python -m pytest -q tests/test_ticket_update_models.py tests/test_ticket_update_migration.py tests/test_ticket_update_repository.py tests/test_ticket_update_u1_contract.py tests/test_ticket_update_operations.py tests/test_ticket_update_tool.py tests/test_ticket_update_integration.py tests/test_ticket_update_lifecycle.py tests/test_ticket_update_security.py
```

Expected result: 모든 수집된 U3 테스트가 통과하고, 예상하지 않은 live network attempt·secret canary match·authority 없는 success publication이 각각 0이다.

## U3 Changed-Line Coverage Command

동일 `HEAD`, 동일 `.venv` interpreter와 동일 U3 test run으로 coverage JSON을 만들고 changed application executable lines에 80% floor를 적용한다.

```bash
aidlc_cov_base=$(git merge-base HEAD main) && \
  .venv/bin/python -m coverage erase && \
  .venv/bin/python -m coverage run --branch --source=app -m pytest -q tests/test_ticket_update_models.py tests/test_ticket_update_migration.py tests/test_ticket_update_repository.py tests/test_ticket_update_u1_contract.py tests/test_ticket_update_operations.py tests/test_ticket_update_tool.py tests/test_ticket_update_integration.py tests/test_ticket_update_lifecycle.py tests/test_ticket_update_security.py && \
  .venv/bin/python -m coverage json -o coverage.json && \
  .venv/bin/python scripts/changed_line_coverage.py --base "$aidlc_cov_base" --coverage-json coverage.json --source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/code-generation/source-manifest.json --prior-source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/code-generation/source-manifest.json --prior-source-manifest aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/code-generation/source-manifest.json --approved-plan aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/code-generation/code-generation-plan.md --source-baseline aidlc/spaces/default/intents/261024-itsm-ticket-tools/.aidlc-engine/source-review/code-generation/baseline-6532efa31d44.tsv --include 'app/**/*.py' --fail-under 80
```

Evidence에는 base commit, tested `HEAD`, included changed files, covered/total executable changed lines, percentage, threshold와 각 command exit code를 기록한다. `coverage.json`이나 실패 출력에 canonical patch bytes, raw `IfMatchVersion`, credential 또는 Authorization을 남기지 않는다.

## Mocking and Failure Injection

- `httpx.MockTransport` handler는 요청 method/path, delegated-token source category, body digest, `If-Match`, call count와 monotonic timestamp만 캡처한다. Secret/header 원문과 canonical bytes는 failure message에 출력하지 않는다.
- FakeModel은 tool call과 text fallback을 결정적으로 반환하며 model input capture에서 current user identity와 safe business fields만 검사한다.
- UTC clock은 expiry, retention과 credential generation recovery에 주입한다. Monotonic clock/sleeper는 read 250ms delay, operation deadline과 NFR8 instrumentation contract의 단위 동작을 검증한다.
- SQLite fixture는 empty DB, U1-migrated DB, U3-migrated DB, staged/active/retired rows와 commit-boundary failure를 각각 독립 temporary path에서 만든다.
- Concurrency는 wall-clock sleep 대신 barrier/event와 직접 row/counter snapshot으로 순서를 고정한다.
- Restart test는 연결과 service/repository instance를 닫고 같은 temporary DB로 새 instance를 만들며 process memory state를 재사용하지 않는다.

## Test Data Management

- Fixture는 승인된 Pydantic schema와 repository DTO로 만들고 raw JSON을 사용할 때는 즉시 해당 schema로 validate한다.
- Opaque ticket ID, pending reference, mutation ID, actor/session/conversation ID는 테스트마다 새 deterministic fixture 값을 사용하며 제품 코드나 지침에 샘플·실제 ticket ID를 하드코딩하지 않는다.
- Patch data는 valid baseline에서 시작해 한 번에 한 field만 바꾸는 방식으로 invalid case를 만든다. Omitted field는 key 자체를 빼고 explicit null은 key와 `null`을 함께 둔다.
- Secret, patch, header, external-text canary는 서로 다른 고유값을 사용해 어느 경계에서 유출됐는지 식별하되 assertion message에는 원문을 출력하지 않는다.
- 각 테스트는 독립 temporary database와 독립 mutable state를 사용한다. 공유 module singleton이나 실제 user/session DB에 의존하지 않는다.

## Coverage and Completion Expectations

- 각 U3 논리 구성요소는 happy path와 최소 두 error/edge case를 갖고, Standard 전략의 5~8개 수준을 충족한다.
- Repository/operations는 publication·confirmation·refresh·reconciliation의 모든 committed boundary와 race를 결정적으로 다룬다.
- U3 changed application executable lines coverage는 80% 이상이다. Empty denominator는 U3 application code가 실제로 변경되지 않은 경우에만 허용되며 이 Unit의 예상 구현에는 해당하지 않는다.
- Unit command의 passed/failed/skipped count, network/canary/PATCH/refresh/consume/active-row/success-publication counters와 coverage 결과를 `code-summary.md`에 기록한다.
- 작성했지만 실행하지 못한 테스트가 있으면 파일·테스트·이유를 정확히 기록한다. CI가 없거나 이 계획이 CI Pipeline을 실행하지 않는다는 이유로 실행했다고 주장하지 않는다.
