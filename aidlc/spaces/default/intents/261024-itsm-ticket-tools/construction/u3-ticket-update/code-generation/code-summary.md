# U3 Ticket Update — Code Summary

## 구현 결과

기존 U1/U2 경계를 보존하면서 durable `ticket_update` prepare/revise/confirm/cancel 흐름을 누적 Agent runtime에 추가했다. Update review는 U3 execution을 `staged`로 저장한 뒤 U1 exact-old pending replacement가 commit된 경우에만 U3 `active`로 게시된다. Confirm은 현재 raw turn, actor/session/conversation/ticket/hash/base-version, U1 pending과 U3 active execution을 모두 대조하고 U1 atomic confirm+consume 뒤에만 PATCH 권한을 만든다.

PATCH는 저장된 canonical UTF-8 bytes와 strong quoted-decimal `If-Match`를 그대로 한 번 전송한다. 권위 있는 no-apply `token_expired` 401에서만 durable refresh reservation, U1 update refresh port와 byte-identical 마지막 PATCH 한 번을 허용한다. 충돌·timeout·transport·그 밖의 401·429는 PATCH를 재전송하지 않고 latest detail로 조정하며, 전체 expected change와 version 증가가 모두 입증될 때만 성공으로 표시한다.

| 영역 | 구현 |
|---|---|
| 모델 | 8개 허용 patch field, omit/null 구분, fixed-order compact serialization v1, SHA-256, safe review/result |
| 저장소 | additive U3 migration, marker/schema/index fingerprint, staged/active/retired CAS, exact locator, one-shot refresh reservation |
| U1 provider | complete replacement evidence와 observable confirmed 중간 상태가 없는 atomic confirm+consume |
| 전송 | delegated bearer, exact body, allowlisted `If-Match`, HTTP-call당 단일 attempt |
| lifecycle | startup/access recovery, orphan/terminal retire, switch/logout/clear/expiry same-lock cleanup |
| runtime | `ticket_read`, `ticket_write`, `ticket_update` 세 tool 누적 assembly와 text-first presentation/history |
| 안전성 | server-only credential/canonical bytes/`If-Match` 비노출, malicious ITSM text를 untrusted data로 유지 |

## 생성·수정 파일

새 U3 application 파일:

- `app/ticketing/update_models.py`
- `app/ticketing/update_migration.py`
- `app/ticketing/update_repository.py`
- `app/ticketing/update_operations.py`
- `app/ticketing/update_tools.py`
- `app/ticketing/update_presentation.py`

공유 application 경계 변경:

- `app/ticketing/models.py`, `app/ticketing/repositories.py`
- `app/ticketing/gateway.py`, `app/ticketing/capability.py`, `app/itsm_auth.py`
- `app/db.py`, `app/session.py`, `app/ticketing/tools.py`
- `app/agent/assistant.py`, `app/agent/service.py`

새 U3 테스트:

- `tests/test_ticket_update_models.py`
- `tests/test_ticket_update_migration.py`
- `tests/test_ticket_update_repository.py`
- `tests/test_ticket_update_u1_contract.py`
- `tests/test_ticket_update_operations.py`
- `tests/test_ticket_update_tool.py`
- `tests/test_ticket_update_integration.py`
- `tests/test_ticket_update_lifecycle.py`
- `tests/test_ticket_update_security.py`

누적 조립 회귀 변경:

- `tests/test_agent.py`
- `tests/test_ticket_registry.py`

전체 목록은 같은 디렉터리의 `source-manifest.json`에 strict schema로 기록했다.

## 주요 구현 결정

- U3 code는 U1 pending table을 직접 SQL-write하지 않고 `replace_update_pending`, `confirm_and_consume_update`, `cancel_update` provider port만 사용한다.
- `PendingUpdateExecutionV1`은 canonical patch bytes, digest와 raw `IfMatchVersion`을 서버 전용 field로 유지한다. public tool schema/result/presentation에는 포함하지 않는다.
- Active partial unique index가 actor/session/conversation scope의 active execution을 하나로 제한한다. U1 commit 뒤 U3 activation 전 crash는 exact binding staged row만 승격한다.
- Runtime startup은 U3 migration 검증 뒤 repository를 조립한다. Missing marker나 fingerprint mismatch는 plugin activation 전에 fail closed한다.
- Prepare/revise 접근은 exact actor/ticket U1 pending으로 staged execution을 재조정하고, full binding이 일치할 때만 CAS-promote하여 U1 commit 뒤 activation-response loss를 restart 없이 복구한다.
- Migration 검증은 marker뿐 아니라 `sqlite_master.sql`, `table_info`, `index_list`, `index_xinfo`를 canonicalize해 실제 column type/constraint, index columns, unique/partial predicate를 검증한다.
- Update refresh port는 injected durable verifier가 current actor/session/conversation, active execution, exact reservation, consumed U1 binding과 base credential generation을 한 transaction에서 확인한 뒤에만 exchange한다.
- Session lifecycle은 기존 conversation lock 아래 U3 execution을 먼저 retire한 뒤 U1 pending/history/session authority를 제거한다. U2 durable create ledger는 삭제하지 않는다.
- 공유 U1 provider/gateway/session/Agent 파일 전체가 manifest-bound changed-line 분모에 들어가므로, exact U3 test file들이 기존 provider regression test를 재-export해 동일 exact command에서 shared boundary를 실행한다. Coverage exclusion이나 threshold 완화는 사용하지 않았다.

## 테스트와 품질 결과

기준 commit은 `89f48f9372635f443c719b7d64ca6900585bb112`다. 변경 전 전체 baseline은 `294 passed in 3.59s`, prerequisite는 `114 passed in 0.58s`였다.

| 검증 | 결과 |
|---|---|
| 계층별 명령 | prerequisite **114**, models **27**, migration/repository **23**, U1/transport **19**, operations **24**, tool/integration/lifecycle/security **15** passed |
| 최종 exact U3 command | **233 passed in 3.14s**; 최종 coverage 실행에서는 **233 passed in 3.64s** |
| Manifest-bound changed-line coverage | **2002/2284 = 87.65%**, floor 80%, branch collection, exit 0 |
| 전체 회귀 | **527 passed in 6.89s**, skip 0, xfail 0 |
| Construction Verification Command | **527 passed in 8.51s**; 3700 statements, 374 miss, 전체 line coverage **90%**, floor 통과 |
| Compatibility focused evidence | prior reader open, additive namespace row 보존, forced migration rollback, missing marker/fingerprint fail-closed 모두 통과 |
| 작업 트리 whitespace 검사 | `git diff --check` 통과 |

Changed-line 측정 파일별 결과:

| File | Covered / executable changed lines |
|---|---:|
| `app/agent/assistant.py` | 24/25 |
| `app/agent/service.py` | 173/208 |
| `app/db.py` | 45/50 |
| `app/itsm_auth.py` | 10/12 |
| `app/session.py` | 106/126 |
| `app/ticketing/capability.py` | 216/249 |
| `app/ticketing/gateway.py` | 185/206 |
| `app/ticketing/models.py` | 255/276 |
| `app/ticketing/repositories.py` | 332/388 |
| `app/ticketing/tools.py` | 34/35 |
| `app/ticketing/update_migration.py` | 61/62 |
| `app/ticketing/update_models.py` | 181/198 |
| `app/ticketing/update_operations.py` | 176/208 |
| `app/ticketing/update_presentation.py` | 32/35 |
| `app/ticketing/update_repository.py` | 150/179 |
| `app/ticketing/update_tools.py` | 22/27 |

Network default-deny 아래 실제 OpenAI/ITSM network 호출은 0건이다. Deliberate socket bypass 1건은 fixture가 차단했고, credential/Authorization/canonical patch/`If-Match`/raw problem/exception canary leak과 authority 없는 success publication은 각각 0건이었다. 정상 integrated confirm은 PATCH 1회를 관찰했고, policy matrix는 허용된 token-expired recovery 외 hidden PATCH replay가 0임을 검증했다.

## 실패·수선 기록과 계획 차이

- 첫 updated coverage 실행은 exact U3 72개가 통과했지만 shared approved source 전체가 분모에 포함되어 `1543/2220 = 69.50%`로 floor에 미달했다. Exact U3 파일에 기존 U1 provider/gateway/session/lifecycle/Agent regression을 포함하고 startup credential-generation recovery 및 architecture-review repairs를 검증한 뒤 `2002/2284 = 87.65%`로 통과했다. Exclusion, skip/xfail, threshold 변경은 없었다.
- 최초 계획의 Planned Source Set에는 PATCH provider allowlist와 누적 3-tool 회귀 파일 세 개가 빠져 있었다. 승인된 continuation에서 `app/itsm_auth.py`, `tests/test_agent.py`, `tests/test_ticket_registry.py`가 명시적으로 추가되었고 현재 source manifest와 구현이 일치한다.
- 승인 계획의 범위 밖 application, UI, endpoint, infrastructure 변경은 없다. `coverage.json`과 `.coverage`는 측정 산출물이며 source manifest에 포함하지 않았다.

## Architecture Review 수선

- R-01: U1 replacement commit 뒤 U3 activation 실패를 주입했다. 같은 process의 다음 prepare가 exact U1 pending과 staged execution을 찾아 동일 `pending_ref`를 active로 승격하고 review를 재구성하며 PATCH는 0회임을 검증했다.
- R-02: 같은 object 이름을 유지한 채 active index의 unique flag, partial predicate와 table `base_version` type/constraint를 변조했다. Repository/plugin assembly 전에 실제 schema-definition 검증이 모두 거부함을 검증했다.
- R-03: 조작 prefix, 다른 user/session/conversation, missing/failed reservation, missing/retired execution과 unconsumed U1 pending을 durable verifier에 주입했다. 모든 경우 refresh/exchange count는 0이었다.

## 미실행 항목과 잔여 위험

작성된 자동화 테스트는 exact U3 또는 전체 회귀에서 모두 실행했다. Testing Contract가 금지한 실제 OpenAI/실제 ITSM 호출과 원격 CI promotion job은 실행하지 않았다.

Production DB file/parent-directory ACL, disk protection, backup 암호화·접근 주체·retention은 repository에서 증명할 수 없으므로 release gate로 남긴다. 다중-process deployment는 shared lock/database arbitration이 없어 지원 범위 밖이다. NFR8.1은 synthetic test로 완료 처리하지 않았으며 U4 `u4-release-assurance`에서 실제 환경의 3+3 사용자 성과 측정 ledger를 수집한다.
