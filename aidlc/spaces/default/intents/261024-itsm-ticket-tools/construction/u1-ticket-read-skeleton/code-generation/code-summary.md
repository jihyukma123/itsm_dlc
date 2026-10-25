# U1 Ticket Read Skeleton — Code Summary

## 구현 결과

기존 FastAPI·OpenAI Agents SDK 애플리케이션에 `ticket_read` walking skeleton을 추가했다. 새 Agent나 별도 서비스 없이 현재 서버 세션, `Runner`, `SQLiteSession`, 사용자 위임 토큰, chat/history API와 화면을 확장했다.

| 영역 | 결과 |
|---|---|
| Tool 표면 | `build_u1_registry`/`build_u1_agent` review seam은 정확히 `ticket_read` 하나만 노출; 현재 누적 runtime의 후속 Unit plugin 조합과 명시적으로 분리 |
| 신원·credential | server-derived `TicketRequestCapability`에 user/session/conversation과 operation당 1회 refresh budget을 결합; `TicketOperations`가 정확한 60초 preflight를 소유하고 raw credential은 gateway만 outbound 직전에 접근 |
| ITSM 연동 | API v2 list/detail typed adapter, delegated bearer, 시도별 timeout, safe error allowlist |
| 조회 연산 | 전체 허용 filter, 반복 query, limit 1~100, canonical query, binding 검증 뒤 atomic once-only opaque continuation, list/detail safe projection |
| 복구 정책 | monotonic operation deadline 안에서 최초 포함 최대 2회, 1회 refresh, 허용 transient 오류만 250ms 뒤 1회, 429 자동 대기·재시도 0회 |
| 저장소 | `ticket_tools_state_v1`의 분리된 confirm/consume CAS와 정확히 두 필드인 소비 증거, once-only cursor, `ticket_tools_history_v1` presentation companion schema·repository; U1 cleanup은 U2 ledger를 보존 |
| 대화 원자성 | conversation lock을 Runner 호출 전에 획득하고 persisted assistant correlation·presentation commit/readback 후 해제 |
| 호환 UI/API | 기존 reply/text를 authoritative fallback으로 유지하고 optional V1 presentation을 text node로 표시 |
| R-08 수정 선행 조회 | exported server-only `read_for_update`가 public version과 같은 canonical strong ETag에서만 `ReadForUpdateResultV1` 반환; 나머지는 `upstream_unavailable` |
| R-09 세션 수명 | 기존 physical session schema에 `session_expires_at`만 additive migration; 생성 시각 +8시간의 절대 만료와 pre-Runner 원자적 권한 정리 |
| R-10 continuation 품질 | OS CSPRNG 256-bit reference boundary와 injected-source 강도 검증; 100,000건 충돌 0 |
| R-11 in-flight 만료 | conversation lock 대기 뒤 persisted session을 Runner 직전에 재검증하고, 모든 gateway credential access에서 절대 만료를 재검사·정리 |
| R-12 오류 비노출 | auth/directory/me/transport/health 실패를 server-owned code·message로만 변환하고 raw detail/reason·upstream code를 폐기 |
| R-13 추적성 | current `rules.md`의 41개 BR 전부를 upstream/coverage에 정확히 한 번 연결하고 source manifest path 존재를 자동 검증 |
| R-14 모델 오류 비노출 | OpenAI status 오류의 raw message/body를 폐기하고 allowlisted category, HTTP status, 안전한 request ID만 API·로그에 남김 |
| R-15 만료 retention 정리 | 만료 session의 presentation companion, SDK message/session history를 conversation ID로 먼저 제거한 뒤 lifecycle state를 commit |
| R-16 동시 만료 멱등성 | 이미 삭제된 session은 같은 transaction에서 active pending/cursor authority 부재를 확인한 경우에만 terminal success로 처리 |
| R-17/R-19 lifecycle 직렬화 | switch, logout, clear, expiry가 application-lifetime conversation lock을 공유하고 persisted actor를 재검증; presentation/history/revocable cleanup부터 session delete, 새 identity 또는 clear generation commit까지 lock 유지 |
| BR1.8 delegated refresh reservation | HMAC 인증 opaque reservation을 create-attempt·actor·생성시각·signed operation deadline에 결합하고 exact expected deadline/positive remaining budget에서만 정확히 한 번 exchange/commit하도록 U1 refresh port 제공 |
| PIPE-U1-13 책임 분리 재검증 | durable same-process second invocation·restart replay는 U2 claim에서 U1 port 호출 전 거부하고, 최초 tamper·expiry·actor/create-attempt mismatch는 U1 verifier 1회 뒤 exchange·session credential mutation 0회로 거부함을 명시적으로 계측 |
| BR5.9 update pending 교체 | `save_review`는 create-only로 제한; 모든 update publication은 confirmed-update 차단, exact-old 조건과 old invalidation/new insert를 한 transaction으로 보장하는 `replace_update_pending`만 사용 |
| 네트워크 격리 | autouse process-level default-deny fixture가 미등록 DNS/TCP와 raw socket 우회를 OS I/O 전에 `UnexpectedNetworkError`로 차단 |

## 생성·수정 파일

새 application package:

- `app/ticketing/__init__.py`
- `app/ticketing/models.py`
- `app/ticketing/capability.py`
- `app/ticketing/gateway.py`
- `app/ticketing/operations.py`
- `app/ticketing/repositories.py`
- `app/ticketing/lifecycle.py`
- `app/ticketing/registry.py`
- `app/ticketing/tools.py`
- `app/ticketing/presentation.py`

기존 application·browser·dependency 변경:

- `app/agent/assistant.py`, `app/agent/context.py`, `app/agent/routes.py`, `app/agent/service.py`
- `app/db.py`, `app/itsm_auth.py`, `app/main.py`, `app/schemas.py`, `app/session.py`
- `static/app.js`, `static/index.html`, `static/style.css`
- `requirements.in`, `requirements.txt`
- `vendor/wheels/.gitignore`, `vendor/wheels/coverage-7.17.0-cp313-cp313-macosx_11_0_arm64.whl`

테스트 변경·추가:

- `tests/conftest.py`, `tests/test_agent.py`, `tests/test_session.py`
- `tests/test_ticket_models.py`, `tests/test_ticket_repositories.py`
- `tests/test_ticket_gateway.py`, `tests/test_ticket_operations.py`
- `tests/test_ticket_registry.py`, `tests/test_ticket_presentation.py`
- `tests/test_ticket_read_integration.py`, `tests/test_ticket_lifecycle.py`
- `tests/test_network_isolation.py`

## 주요 구현 결정

- Public Pydantic V1 models는 unknown field를 거부하고 credential, Authorization, raw header/problem/cursor를 직렬화하지 않는다.
- `ItsmAuthClient`는 명시된 attempt timeout으로 티켓 endpoint를 한 번만 호출한다. `TicketOperations`는 raw token을 받지 않는 expiry port로 `credential_expires_at <= server UTC now + 60초`를 먼저 판정하고 operation당 한 번의 refresh budget을 reactive 401과 공유한다. Gateway는 refresh 정책 없이 raw credential을 outbound 직전에만 꺼낸다.
- U2 durable reservation은 U1의 256-bit server secret으로 HMAC 인증한 opaque envelope로 검증한다. create-attempt ID, user/session/conversation, outer `used_at`, envelope 생성시각, 15분 age window와 signed operation deadline이 모두 일치하고 expected deadline이 정확히 같으며 remaining budget이 signed budget 이내일 때만 refresh provider를 정확히 한 번 호출한다. U2 durable claim fake의 same-process second invocation과 restart replay는 U1 port 호출 0회이며, 최초 tamper·expiry·actor/create-attempt mismatch는 U1 verifier 호출 1회, exchange 0회, session credential mutation 0회다.
- Pending mutation은 exact current-turn evidence와 actor/operation/payload/target/version/expiry binding을 검사해 `pending → confirmed` CAS를 수행하고 `confirmed_at`을 고정한다. 별도 `consume_once` CAS는 정확히 `ConsumedMutationEvidenceV1 {mutation_id, confirmed_at}`만 한 번 반환하며 credential, idempotency key, canonical bytes 또는 POST/PATCH 권한을 담지 않는다.
- `save_review`는 runtime에서 update input을 거부하는 create-only port다. Update pending prepare/revise는 `BEGIN IMMEDIATE` transaction 안에서 동일 actor scope의 unexpired confirmed update를 먼저 검사한다. prepare는 pending 부재, revise는 exact old pending ID를 요구하며, revise 성공은 old invalidation과 new pending insert를 원자적으로 수행하고 insert 충돌 시 전부 rollback한다.
- 대화 초기화, 사용자 전환, 로그아웃, 세션 만료와 consume-before-bind crash fixture는 U2 `ticket_create_attempts` row, idempotency key와 canonical request bytes를 byte-for-byte 보존한다. 소비 증거가 U2에 결합되기 전에는 POST/PATCH가 0회이고 새 review와 새 명시적 confirmation이 필요하다.
- Continuation reference는 암호학적 난수로 발급하고 user/session/conversation/query에 결합한다. 한 transaction에서 binding을 먼저 검증한 뒤 성공한 owner만 원자적으로 소비하므로 공격자의 mismatch가 정상 continuation을 삭제하지 못한다. upstream cursor는 server state 밖으로 나가지 않는다.
- 상세 ETag는 strong quoted-decimal이며 public version과 일치할 때만 server-only update evidence로 보존한다.
- 일반 detail 조회는 ETag가 없거나 잘못되어도 safe public projection이 유효하면 계속 성공한다. U3 전용 `read_for_update`만 missing, weak, non-decimal, leading-zero, signed, whitespace, version mismatch를 모두 fail closed로 거부하며, 거부 후 review/PATCH 관찰 횟수는 0이다.
- 새 세션은 한 UTC 시각에서 `created_at`과 정확히 8시간 뒤 `session_expires_at`을 함께 저장한다. 활동·credential refresh·재시작은 이를 연장하지 않는다. legacy의 parseable creation time은 +8시간으로 backfill하고, 빈 값·malformed 값은 epoch expiry로 fail closed 처리한다.
- session migration은 `session_expires_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z'`를 additive하게 추가한다. 직전 release의 12-column create/restore/token-write/logout 경로는 그대로 동작하며, 구버전이 default epoch로 쓴 row는 forward redeploy 후 fail closed되고 U2 ledger는 바뀌지 않는다.
- 보호 API는 capability나 Runner를 만들기 전에 `now >= session_expires_at`을 검사하고 pending invalidation, cursor deletion, session deletion을 한 transaction으로 commit한다. 정리 실패는 rollback 후 503으로 닫히며 Runner/티켓 ITSM 호출은 0이다.
- Chat은 dependency 검증 후에도 같은 conversation lock 안에서 persisted session을 다시 읽는다. 이 재검증과 capability 생성은 Runner 직전에 수행되며, lock 대기 중 만료된 두 번째 요청은 Runner 호출 없이 authority state를 정리한다.
- Capability는 credential provider 호출 전·후와 refresh 후 각각 absolute session expiry를 검사한다. Runner가 tool 호출을 만들기 전에 만료된 경우 expiry handler가 pending/cursor/session을 정리하고 ticket HTTP를 0건으로 유지한다.
- Session/auth 오류 adapter와 health endpoint는 raw `ItsmApiError.detail`, `ItsmUnavailableError.reason`, upstream code 또는 transport exception text를 API·로그에 포함하지 않는다.
- OpenAI status 오류 adapter는 exception message/body를 읽거나 기록하지 않고 server-owned 분류와 safe request ID만 노출한다. credential 형식 canary를 API body, log 및 의도적 실패 subprocess 전체 출력에서 검사한다.
- 절대 만료 정리는 presentation companion을 먼저 삭제하고 matching SDK message/session history를 지운 뒤 application lifecycle transaction을 commit한다. 재시작 뒤에도 만료 conversation retention row는 0이다.
- 동시 만료 요청은 session 삭제 rowcount가 0이어도 같은 transaction에서 session 및 active pending/cursor authority가 모두 없을 때만 성공한다. 일부 authority가 남으면 기존 rollback/fail-closed 503을 유지한다.
- 보호 chat, history read와 expiry cleanup은 `AgentService`가 소유하고 application state에 공유한 하나의 per-conversation lock provider를 사용한다. chat은 lock을 얻은 직후 Runner 전에 persisted session을 재검증하고, Runner의 SDK history write 직후 correlation·mapping·text fallback·presentation·응답 결정 전에 다시 재검증한다.
- Switch, logout, clear도 같은 lifecycle coordinator를 사용한다. cleanup 후 terminal commit 전 대기 중인 old-scope 요청은 captured lifecycle generation 또는 삭제된 session/actor 검증에 실패하며 Runner를 실행하지 않는다. Clear는 session을 유지하되 generation을 lock 해제 전에 증가시킨다.
- post-Runner session이 missing/expired이면 생성된 결과를 폐기하고 같은 lock 안에서 presentation companion, SDK message/session history, pending mutation, cursor binding, server session을 모두 삭제한다. 경쟁 expiry 요청은 lock에서 기다린 뒤 이미 비어 있는 terminal state를 멱등하게 처리하고 history나 metadata를 재생성하지 않는다.
- Continuation reference generator는 production에서 OS `secrets.token_bytes`를 사용하고 256 bits를 URL-safe opaque 값으로 인코딩한다. 128 bits 미만, 강도를 보증하지 않은 injected source, 잘못된 byte sample은 거부한다.
- 현재 turn의 raw chat text는 mutation authority가 아니며, server-held current-turn evidence로만 취급한다.
- Optional presentation은 exact assistant sequence와 text SHA-256으로 결합한다. metadata가 없거나 손상·미지원·불일치하면 기존 text-only reply/history가 그대로 남는다. 복원된 history는 live region 밖에서 렌더링하고 현재 상태·응답만 별도 live status로 알린다.
- `TicketToolRegistry`와 presentation mapper registry는 중복과 미지원 항목을 fail closed로 거부해 U2/U3가 공통 구현을 수정하지 않고 확장하게 한다.
- 모든 pytest process에는 DNS resolution, TCP connect/create_connection/connect_ex와 raw-socket sendto를 차단하는 autouse fixture가 적용된다. 명시적 `httpx.MockTransport`와 in-process ASGI transport만 사용하며 fresh `httpx.AsyncClient`와 raw socket 우회 probe는 실제 I/O 전에 차단된다.

## 테스트와 품질 결과

### 승인 계획 재개 시 기준선 불일치

- **Baseline command:** `.venv/bin/python -m pytest -q`
- **Result:** `1 failed, 158 passed in 2.61s`
- **Failing node:** `tests/test_ticket_models.py::test_every_current_business_rule_has_one_manifest_backed_coverage_row`
- **Safe failure category:** `traceability baseline mismatch`
- **Cause:** 현재 Functional Design의 `BR5.8`이 Code Generation `traceability.json.upstream_ids`에 없어 기대 횟수 1 대비 실제 횟수가 0이었다.
- **Production code edits:** `0`
- 승인된 baseline 불일치 중단 조건에 따라 구현을 시작하지 않았으며, `traceability.json`과 계획 체크박스는 변경하지 않았다.

이후 사용자가 `BR5.8`을 최신 설계 규칙으로 인한 예상된 Code Generation 범위로 명시했다. `traceability.json.upstream_ids`와 `coverage`에 `BR5.8`을 각각 정확히 한 번 추가하고 실제 구현·테스트 대상에 연결한 뒤 같은 기준선 명령을 다시 실행해 `159 passed in 2.51s`를 확인했다. 이 정상화 이후에만 production 변경을 재개했다.

| 검증 | 명령 | 결과 |
|---|---|---|
| 변경 전 기준선 | `.venv/bin/python -m pytest -q` | 37 passed |
| Models/repositories | `.venv/bin/python -m pytest -q tests/test_ticket_models.py tests/test_ticket_repositories.py` | 51 passed |
| Gateway/operations | `.venv/bin/python -m pytest -q tests/test_ticket_gateway.py tests/test_ticket_operations.py` | 49 passed |
| Registry/presentation | `.venv/bin/python -m pytest -q tests/test_ticket_registry.py tests/test_ticket_presentation.py` | 10 passed |
| R-14~R-16 focused | `.venv/bin/python -m pytest -q tests/test_session.py tests/test_ticket_lifecycle.py tests/test_agent.py` | 55 passed |
| Runner/lifecycle | `.venv/bin/python -m pytest -q tests/test_ticket_read_integration.py tests/test_ticket_lifecycle.py` | 19 passed |
| Session/auth errors | `.venv/bin/python -m pytest -q tests/test_session.py` | 23 passed |
| Network isolation | `.venv/bin/python -m pytest -q tests/test_network_isolation.py` | 2 passed; fresh AsyncClient DNS 1회와 raw socket connect 1회 모두 OS I/O 전에 차단 |
| BR1.8/BR5.9 focused | `.venv/bin/python -m pytest -q tests/test_ticket_gateway.py tests/test_ticket_repositories.py` | 70 passed |
| U1 exact suite | `.venv/bin/python -m pytest -q tests/test_ticket_models.py tests/test_ticket_repositories.py tests/test_ticket_gateway.py tests/test_ticket_operations.py tests/test_ticket_registry.py tests/test_ticket_presentation.py tests/test_ticket_read_integration.py tests/test_ticket_lifecycle.py tests/test_network_isolation.py` | 159 passed in 1.52s |
| 전체 회귀 | `.venv/bin/python -m pytest -q` | 270 passed in 3.79s |
| Coverage run | `.venv/bin/python -m coverage run --source=app -m pytest -q` | 270 passed in 4.48s |
| Changed-source coverage JSON | `.venv/bin/python -m coverage json --include='app/ticketing/*,app/db.py,app/session.py,app/itsm_auth.py,app/agent/*,app/main.py,app/schemas.py' --fail-under=80 -o coverage.json` | 2325/2564 lines, 90.679%, exit 0; 80% floor 충족 |
| Canonical traceability sensor | `aidlc engine sensor-traceability --output-path aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/code-generation/traceability.json --stage-slug code-generation` | pass=true, invalid_targets=0, findings_count=0 |
| Traceability integrity | U1 exact suite의 `tests/test_ticket_models.py` 및 manifest/target 존재 검사 | passed; manifest 38 paths, upstream ID 105개 unique, current BR 41개와 BR1.8·BR5.9·NFR2.7·PIPE-U1-13 각 1행 |
| Patch whitespace | `git diff --check` | passed |
| PIPE-U1-13 focused 재검증 | `.venv/bin/python -m pytest -q tests/test_ticket_gateway.py` | 32 passed in 0.05s; same-process second invocation·restart replay U1 port call 0, first-call mismatch verifier call 1, 모든 거부의 exchange·credential mutation 0 |
| U1 exact 재검증 | `.venv/bin/python -m pytest -q tests/test_ticket_models.py tests/test_ticket_repositories.py tests/test_ticket_gateway.py tests/test_ticket_operations.py tests/test_ticket_registry.py tests/test_ticket_presentation.py tests/test_ticket_read_integration.py tests/test_ticket_lifecycle.py tests/test_network_isolation.py` | 161 passed in 1.63s |
| 현재 전체 회귀·coverage 재검증 | `.venv/bin/python -m coverage run --source=app -m pytest -q && .venv/bin/python -m coverage report --fail-under=80` | 679 passed in 8.83s; app 4455 statements 중 4006 covered, total 90%, exit 0 |

- 모든 model 동작은 FakeModel, 모든 ITSM 동작은 `httpx.MockTransport`를 사용했다. 실제 OpenAI·ITSM 호출은 없었다.
- 이번 Infrastructure Design R-10 downstream 재검증에서는 production code를 변경하지 않았다. 기존 구현이 수정된 책임 분리를 이미 충족했으며 `tests/test_ticket_gateway.py`에 verifier/port/exchange/session-mutation counter assertion만 강화했다.
- credential preflight의 정확한 60초 및 +1µs 경계가 통과했다. preflight refresh 실패의 ticket HTTP는 0건이고, preflight가 budget을 소비한 뒤 401이 와도 refresh는 총 1회·HTTP는 1회에 그쳤다. 비임박 credential의 첫 401은 refresh 1회와 최종 attempt 1회만 수행했다.
- concurrent `consume_once` 두 호출 중 증거는 정확히 한 건만 반환됐다. 모든 성공 증거의 field 집합은 `{mutation_id, confirmed_at}`이고 반복·mismatch·expiry는 증거와 mutation transport가 0건이었다.
- clear, switch, logout, expiry 전후 U2 ledger row/key/canonical bytes snapshot은 동일했다. consume-before-bind crash 후 기존 증거는 재발급되지 않았고 동일 attempt를 보존한 채 새 review/confirmation을 요구했으며 POST/PATCH는 0건이었다.
- prior-release session create/restore/token update/logout SQL은 migrated DB에서 통과했고, epoch-default row의 forward-redeploy 보호 요청은 `authentication_required`로 fail closed되며 U2 ledger는 동일했다.
- 첫 focused 실행(`tests/test_agent.py tests/test_ticket_lifecycle.py`)은 isolated subprocess fixture가 아직 생성되지 않은 하위 DB 디렉터리를 가리켜 31 passed, 1 failed였다. fixture를 pytest가 보장한 기존 `tmp_path`로 고친 뒤 focused 55개와 모든 후속 검증이 통과했다. application 동작이나 threshold는 변경하지 않았다.
- 테스트에서 티켓 요청의 delegated bearer 사용을 확인했고 service-token 티켓 요청은 0건이었다.
- strict ETag matrix의 rejected form마다 update review/PATCH 관찰 횟수는 0건이었다.
- 100,000개 OS-CSPRNG continuation reference의 고유값은 100,000개로 충돌 0건이었고 raw cursor 포함·숫자 전용 순차/시각 형태는 0건이었다.
- exact expiry boundary와 재시작·legacy migration·cleanup rollback에서 만료 뒤 Runner/티켓 ITSM 호출은 0건이었다. 동시 요청에서 persisted message/presentation mismatch는 0건이고 companion commit 시 lock-held 관찰은 모두 true였다.
- lock 대기 중 만료 fixture에서 두 번째 Runner 호출은 0건, tool credential access 직전 만료 fixture에서 ticket HTTP는 0건이었으며 두 경우 모두 pending/cursor/session stale authority가 남지 않았다.
- 악의적 token-exchange, directory, `/me`, transport 실패 canary는 API body·application log·health body에서 0건이었고, 의도적으로 실패한 isolated subprocess의 stdout·stderr·traceback·assertion diff에서도 0건이었다.
- 악의적 OpenAI model error body와 여러 credential-format canary는 API body·application log에서 0건이었고, 의도적으로 실패한 isolated subprocess의 stdout·stderr·traceback·assertion diff에서도 0건이었다. 안전한 request ID만 유지됐다.
- 재시작 후 만료 cleanup에서 presentation companion, SDK message 및 SDK session row는 모두 0건이었다. 동일 만료 cookie 동시 요청 2건은 cleanup failure 없이 모두 `session_expired`로 끝났고 Runner/티켓 ITSM 호출 및 active pending/cursor authority는 0건이었다. 이후 process-restart retry는 `no_session` terminal state를 확인했다.
- R-17 barrier regression은 Runner의 assistant SDK history write가 완료된 지점에서 실행을 멈추고 경쟁 expiry history 요청을 시작했다. 경쟁 요청은 shared lock에서 대기했고, post-Runner expiry 검사는 correlation·presentation publication보다 먼저 실행됐다. 두 요청은 모두 `authentication_required`였고 성공 reply/presentation publication은 0건, cleanup 후 SDK message·SDK session·presentation companion·pending·cursor·server session row는 모두 0건, 후속 history/metadata 재생성도 0건이었다.
- 최신 Functional Design 반영 전 U1 exact suite는 `BR1.8`·`BR5.9` traceability 행 부재로 1건 실패했다. 두 규칙과 `NFR2.7`·`PIPE-U1-13`을 실제 구현·테스트 대상에 연결한 뒤 같은 suite를 재실행해 152개 전부 통과했다.
- Traceability integrity test는 current BR 41개가 각각 upstream과 coverage에 정확히 1회 존재하며 모든 concrete target path가 source manifest에 포함됨을 확인했다. `BR1.8`은 capability/gateway 테스트, `BR5.9`는 repository 테스트에 연결됐다.
- Reviewer repair 후 switch/logout/clear 각각에서 Runner가 assistant history를 쓴 직후 정지하고 lifecycle cleanup을 교차했다. cleanup 완료와 terminal commit 사이에 캡처된 old-scope chat은 lock에서 대기했고, commit 후 세 요청 모두 401로 거부됐다. Expiry barrier를 포함한 네 이벤트 모두 terminal commit 뒤 old-scope SDK message/session·presentation row가 0건이었다.
- U1 review seam은 `U1_REGISTRY.tool_names == ('ticket_read',)`와 `build_u1_agent(...).tools == ['ticket_read']`를 직접 검증한다. `REGISTRY`의 `ticket_write`는 이미 존재하는 후속 Unit 누적 runtime 조합이며 U1 완료 범위나 manifest 소유로 주장하지 않는다.
- OpenAI key, client secret, delegated token, refresh credential과 Authorization canary를 model input, tool result, API response, persistence row, log, repr, 그리고 의도적으로 실패한 격리 subprocess의 stdout·stderr·traceback·assertion diff에서 검사했으며 발견은 0건이었다.
- 계획한 테스트는 모두 실행했다. 실행하지 않은 U1 테스트는 `None.`

## 계획 차이와 제한

- 현 sandbox가 전역 uv cache 내부의 `.git` 접근과 network를 막아 전체 `uv pip compile`은 완료하지 못했다. `requirements.in`과 `requirements.txt`는 동일한 `coverage==7.17.0` direct pin으로 동기화했다.
- 같은 버전의 CPython 3.13 macOS arm64 wheel을 `vendor/wheels/`에 보존하고 project-local cache로 `.venv`에 offline 설치했다. 별도 `PYTHONPATH` 없이 `.venv/bin/python -m coverage --version`과 필수 결합 명령이 동작한다. 다른 platform은 정상 package resolution 또는 해당 platform의 같은 버전 wheel을 사용해야 한다.
- `app/ticketing/lifecycle.py`는 계획의 current-turn evidence 책임을 별도 모듈로 명확히 하기 위해 추가했다. 이는 계획의 lifecycle 경계 내 구조적 세분화이며 기능 범위 증가는 아니다.
- U1은 최종 세 tool assembly, create/update mutation 동작, README 완결과 NFR8 사용자 성과 측정을 주장하지 않는다. 이 항목은 U2, U3, U4에 남아 있다.
- Source manifest는 이번 repair가 실제 수정한 shared runtime/test 경로를 포함한 기존 38개 누적 U1 경로를 유지한다. 변경하지 않은 U2 `create_*` source/test는 U1 소유로 추가하지 않았고, U1-only factory seam으로 독립 검토 가능성을 확보했다.

## 후속 Unit 확장점

- U2는 `PendingTicketMutationV1` create variant와 registry factory/mapper를 사용하고 자체 durable create-attempt namespace를 추가한다.
- U3는 U1 detail의 server-only version/ETag evidence와 update variant binding을 사용한다.
- U4는 `ticket_read`, `ticket_write`, `ticket_update` 정확히 세 개의 최종 assembly, 전체 회귀·coverage, README와 사용자 성과 측정을 완결한다.
