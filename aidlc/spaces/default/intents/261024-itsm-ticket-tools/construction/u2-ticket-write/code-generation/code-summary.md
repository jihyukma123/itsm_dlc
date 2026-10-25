# U2 Ticket Write — Code Summary

## 구현 결과

기존 U1 공개 포트와 안전 경계 위에 ledger-first `ticket_write` 생성 흐름을 구현했다. 생성 요청은 strict 입력 검증, catalog 정규화, `prepared` ledger 선행 commit, 현재 turn의 명시적 확인, durable send claim, 동일 idempotency key·canonical bytes 재사용, 최대 2회의 전체 POST budget을 거쳐 실행된다.

이번 Unit 재진입에서는 승인된 13개 계획 step을 현재 application·test source와 다시 대조했다. 구현 수정은 필요하지 않았으며, 아래 결과는 현재 workspace에서 다시 실행한 검증 evidence다.

| 영역 | 결과 |
|---|---|
| 입력·정규화 | catalog 기반 selector·관계 검증, timezone 포함 due date, deterministic compact UTF-8 request body와 hash |
| 확인 | U1 공개 `get`/`confirm`/`consume_once` 포트만 사용하고 actor·payload·현재 turn·만료를 검증 |
| 전송 통제 | 모든 POST 전에 send `claim_id`를 CAS로 획득하고 transport·reconciliation 결과를 같은 claim으로 fence |
| 복구 | reconciliation은 기존 send `claim_id`를 보존하고, refresh recovery는 process-local active registry와 signed creator boot를 함께 사용해 다른 boot의 실제 restart에서만 generation CAS 허용 |
| credential | 승인된 C-01 `CredentialRefreshPortV1.refresh_delegated_capability_once(capability, reservation, remaining_deadline)`만 호출하고 `Result[TicketRequestCapability, SafeErrorV1]`로 success/safe failure를 반환 |
| 키 관리 | 전용 환경 키링, envelope-safe ASCII current/previous `kid`, verification-only 이전 키, 24시간 이상 7일 이하 검증 수명, production secret 기본값 없음 |
| 세션 영속성 | token·expiry·credential generation을 한 SQLite transaction에서 atomic commit하고 restart 시 저장된 generation으로 capability 재구성 |
| 예약 envelope | `r1.<kid>.<payload>.<mac>`, domain-separated actor binding, base credential generation, creator boot ID를 포함하고 signer/verifier 권한을 분리 |
| 보존·표시 | confirmed/orphan ledger를 최소 24시간 보존하고 text-first review/success/error/ambiguous 결과를 기존 registry/presentation에 연결 |
| 격리 | 실제 OpenAI·ITSM 호출 없이 FakeModel, MockTransport, process-level network deny를 사용 |

키링 설정은 `TICKET_REFRESH_KEYS_JSON`, `TICKET_REFRESH_CURRENT_KID`, `TICKET_REFRESH_VERIFICATION_SECONDS`를 모두 요구한다. 누락·malformed·unknown/weak key·범위 밖 수명과 dotted/non-ASCII/64자 초과 `kid`는 refresh 활성화 전에 fail closed하며 기존 chat/read 경로는 유지한다. Raw key bytes는 operations, runtime context, model/tool/API 응답에 전달하지 않는다.

## 생성·수정 파일

새 application 및 검증 도구:

- `app/ticketing/create_models.py`
- `app/ticketing/create_repository.py`
- `app/ticketing/create_operations.py`
- `app/ticketing/create_tools.py`
- `app/ticketing/create_presentation.py`
- `scripts/changed_line_coverage.py`

새 테스트:

- `tests/test_ticket_create_models.py`
- `tests/test_ticket_create_repository.py`
- `tests/test_ticket_create_operations.py`
- `tests/test_ticket_write_tool.py`
- `tests/test_ticket_write_integration.py`
- `tests/test_ticket_create_security.py`
- `tests/test_changed_line_coverage.py`

기존 application·테스트 변경:

- `app/config.py`, `app/db.py`, `app/session.py`, `app/itsm_auth.py`
- `app/ticketing/gateway.py`, `app/ticketing/capability.py`, `app/ticketing/tools.py`
- `app/agent/assistant.py`, `app/agent/service.py`
- `tests/conftest.py`, `tests/test_ticket_gateway.py`, `tests/test_ticket_repositories.py`
- `tests/test_ticket_registry.py`, `tests/test_ticket_lifecycle.py`
- `tests/test_agent.py`, `tests/test_session.py`

## 주요 구현 결정

- U1 pending review를 공개하기 전에 canonical bytes, request hash, serialization version, CSPRNG idempotency key를 U2 ledger에 `prepared`로 commit한다.
- U2 create-attempt schema는 additive refresh reservation/generation 필드를 포함하지만 `claim_kind`, `claim_started_at`, 별도 recovery claim identity에는 의존하지 않는다. 기존 DB에 남은 legacy column은 destructive migration 없이 무시한다.
- 모든 POST는 durable send claim 획득 뒤에만 실행한다. Active claim은 deadline 전에 탈취하지 않고, reconciliation과 late outcome도 동일한 `claim_id`로 fence한다.
- initial send, refresh retry, reconciliation retry를 합친 POST 수는 최대 2회다. `created` 또는 `Idempotent-Replayed` 응답에 authoritative ticket ID가 없으면 success를 만들지 않는다.
- authoritative no-apply `token_expired` 401에서만 refresh reservation을 network 호출 전에 durable commit한다. 이미 refresh가 사용된 뒤 다시 401이면 같은 claim fence로 terminal authentication failure를 기록하며 추가 refresh·claim·POST를 허용하지 않는다.
- C-01 provider/consumer는 같은 fixture로 contract-defined reservation schema와 typed `Result[TicketRequestCapability, SafeErrorV1]` 성공·실패를 검증한다. `operation_deadline`과 `creator_boot_id`는 opaque signed payload 내부 claim이며 외부 `CredentialRefreshReservationV1` 필수 field가 아니다. `create_operations.py`는 capability 내부 메서드를 직접 호출하지 않고 승인된 refresh port만 호출한다.
- Reservation signer는 current key로만 서명하고 verifier는 current/previous key를 검증한다. Unknown·retired·tampered key와 수명·boot/generation/actor binding 불일치는 fail closed한다.
- Refresh reservation CAS 승자는 즉시 application-lifetime active registry에 등록되고 durable outcome 뒤 제거된다. Same-boot observer는 registry entry가 없더라도 signed creator boot 때문에 write·recovery·refresh를 수행하지 않으며, owner cancellation 뒤에도 실제 다른 boot의 restart만 stored generation을 비교한다.
- Session refresh는 SQLite `UPDATE ... RETURNING`으로 token, expiry, generation 증가를 atomic commit한다. Commit 뒤 응답 손실이나 process restart가 발생해도 저장된 higher generation으로 기존 reservation을 완료하고 두 번째 credential exchange를 하지 않는다.
- Missing/invalid refresh key configuration은 create refresh만 차단한다. 기존 chat, history, ticket read 경로의 조립과 동작은 유지한다.

## 테스트와 품질 결과

| 검증 | 실행 명령/범위 | 결과 |
|---|---|---|
| Brownfield baseline | U1 contract와 기존 runner readiness exact-file 명령 | **99 passed** |
| 계층별 테스트 | `unit-test-instructions.md`의 models, repository, gateway, operations, tool/registry/presentation, integration/lifecycle, security/network/helper 명령 | 모두 통과 |
| U2 exact suite | 승인된 15개 exact-file pytest 명령 | **249 passed**, skip 0, xfail 0 |
| U2 coverage suite | branch coverage를 수집하는 승인된 U2 app-source pytest 명령 | **228 passed**, skip 0, xfail 0 |
| Manifest-bound changed-line coverage | U2 source manifest + U1·현재 workspace의 선행 U3/U4 manifest + 승인 계획 + stage-entry source baseline + `--include 'app/**/*.py' --fail-under 80` | U2 changed executable lines **1447/1649**, **87.75%**, threshold 통과 |
| 전체 회귀 | `.venv/bin/python -m pytest -q` | **679 passed**, skip 0, xfail 0 |
| Construction Verification Command | `.venv/bin/python -m coverage run --source=app -m pytest -q && .venv/bin/python -m coverage report --fail-under=80` | **679 passed**, 전체 application line coverage **90%**, threshold 통과 |
| 작업 트리 검사 | `git diff --check` | 통과 |

Coverage threshold, source scope, branch mode를 낮추지 않았고 skip/xfail을 추가하지 않았다. Network default-deny와 MockTransport/FakeModel 경계를 유지해 실제 OpenAI·ITSM network call은 0건이며 secret canary 노출도 0건이었다.

## 수선 중 실패와 복구

- 첫 focused 실행은 shared C-01 fixture의 고정 시각과 pending repository의 실제 시각이 달라 consumer 확인이 만료되어 `89 passed, 1 failed`였다. Fixture 시각을 test 시작 시 UTC로 capture하도록 맞춘 뒤 동일 focused command가 `90 passed`로 통과했다.
- 첫 restart focused 실행은 typed port failure를 곧바로 durable `failed`로 기록해 commit-before-response-loss reservation을 조기에 닫았고 `41 passed, 1 failed`였다. Port가 credential commit 여부를 구분할 수 없는 failure에서는 reservation을 `reserved`로 유지하고 다른 boot가 session generation으로 판정하도록 고친 뒤 `42 passed`로 통과했다.
- Manifest-bound coverage는 merge-base 전체 `app/**/*.py`를 분모로 쓰지 않는다. Engine stage-entry content-hash baseline과 선행 U1 source manifest로 prior-unit/pre-stage path를 분리한 뒤, 이번 stage에 변경된 U2 source manifest claim과 승인 계획 Planned Source Set의 교집합만 측정한다. 승인 경로 누락·승인 밖 claim·선행 Unit에도 없는 승인 밖 stage 변경은 실패시키며, 공유 파일은 baseline 원문이 없으므로 merge-base 이후 executable lines 전체를 보수적으로 분모에 둔다.
- 이번 재진입에서 `unit-test-instructions.md`의 기존 changed-line 명령을 그대로 실행하면 U1만 선행 manifest로 전달하므로, 이미 workspace에 존재하는 U3/U4 source를 승인 밖 변경으로 정확히 탐지해 실패했다. U3/U4 manifest를 선행 evidence로 함께 전달한 동일 helper 판정은 U2 **1447/1649 (87.75%)**로 통과했다. 이는 U2 source 결함이 아니라 직렬 Unit 재진입 이전에 후속 Unit source가 이미 존재하는 workspace 상태 차이다.

## 미실행 테스트

작성된 U2 자동화 테스트는 모두 exact suite 또는 전체 회귀에 포함되어 실행되었다. 실제 OpenAI와 실제 ITSM을 사용하는 live-service 검증은 Testing Contract가 금지하므로 실행하지 않았고, 승인된 FakeModel·MockTransport·network deny 검증으로 대체했다. 원격 CI promotion job 자체는 이 Code Generation 단계에서 실행하지 않았으며, 로컬 construction verification evidence를 후속 Build and Test가 재사용·재검증한다.

## 계획 차이와 남은 경계

- 현재 승인된 계획과 Planned Source Set 대비 구현 이탈은 없다. 이번 재진입에서는 application·test source를 수정하지 않았고 계획의 완료 상태만 검증했다.
- `.coverage`와 `coverage.json`은 검증 중 생성된 측정 산출물이므로 source manifest에 포함하지 않았다.
- U1의 state/history schema와 registry 구현, static UI, U3 update behavior, 새 infrastructure는 변경하지 않았다.
- NFR8.1의 동일 환경 3회 사용자 성과 측정은 계획대로 `u4-release-assurance` evidence에 남겨 두었다.
