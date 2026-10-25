# U3 Ticket Update — 보안·품질 비기능 요구사항

## Sources

- `construction/u3-ticket-update/functional-design/functional-spec.md` — 수정 확인, optimistic lock, 충돌·불명확 결과 조정과 durable publication 초안
- `construction/u3-ticket-update/functional-design/rules.md` — patch 검증, confirmation, 위임 인증과 안전한 결과 규칙
- `inception/requirements-analysis/requirements.md` — NFR1~NFR9 및 FR4~FR7의 수치화된 기준
- `inception/contract-design/contract-summary.md` — C-02, C-03A, C-05, C-06, C-07의 승인된 V1 타입·port·호출 상한
- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md` — 기존 Python/FastAPI/Agents SDK/httpx/SQLite/pytest 경계
- `construction/u3-ticket-update/nfr-requirements/nfr-requirements-questions.md` — 확인된 fail-closed, durable publication과 복구 조건

## 보안과 신뢰 경계 요구사항

| ID | 요구사항 | 측정 기준 | 검증 방법 |
|---|---|---|---|
| NFR1.1 | 액세스 토큰, client secret, OpenAI API key, Authorization 값, raw header/problem/exception, canonical patch bytes와 server-only `IfMatchVersion`은 모델 입력, function-tool schema·결과, 사용자 응답, 애플리케이션 로그, 테스트 실패 출력과 HTTP 오류 응답에 나타나지 않아야 한다. | 경계별 고유 canary 노출 0건 | schema snapshot, FakeModel capture, log/error capture, persistence projection, presentation contract test |
| NFR1.2 | 제목·설명·impact note·catalog label·문제 응답 등 ITSM-origin 문자열은 구조화되고 escape된 비신뢰 데이터로만 취급해야 한다. | 외부 문자열로 신원·권한·confirmation·tool argument·retry 정책이 달라지는 사례 0건 | 지시문·HTML·Markdown 제어문자·가짜 confirm 문자열 주입 테스트 |
| NFR1.3 | `SafeErrorV1`, `SafeUpdateTransportResultV1`, `TicketMutationToolResultV1`은 allowlist 필드만 통과시키고 malformed 또는 알 수 없는 응답은 fail closed해야 한다. | 허용 목록 밖 field 노출 0건, 불완전 성공의 success 표시 0건 | 401/403/404/412/422/428/429/5xx, timeout, malformed response 매핑 테스트 |
| NFR2.1 | 모든 update 상세 조회와 PATCH는 현재 HttpOnly server session에서 복원한 현재 사용자의 delegated capability를 사용해야 한다. | delegated token 사용 100%, service token을 사용한 ticket 호출 0건 | transport authorization canary와 사용자 전환 fixture |
| NFR2.2 | tool input ticket ID, user, session, conversation, operation, mutation ID, normalized patch hash, base version, 15분 expiry와 current raw user turn 중 하나라도 맞지 않으면 consume과 PATCH를 실행할 수 없어야 한다. | 불일치·만료·quoted/embedded/model-generated confirm에서 consume/PATCH 0회 | fake clock, target mismatch, actor switch, clear/logout/expiry, current-turn decision contract test |
| NFR2.3 | pending reference나 저장 record의 possession 자체는 권한이 아니다. Exact matching active U3 execution, exact matching U1 pending, 현재 turn의 명시적 확인과 U1의 원자적 confirm+`consume_once` evidence를 모두 요구해야 한다. | 미확인·취소·교체·만료·staged·retired·고아 record에서 PATCH 0회 | orphan/replacement/cancel/restart/concurrent-confirm test |

## 데이터 무결성과 계약 정합성 요구사항

| ID | 요구사항 | 측정 기준 | 검증 방법 |
|---|---|---|---|
| NFR3.1 | Update review는 최신 상세 body의 public version과 정확히 같은 strong quoted-decimal ETag에서 U1 adapter가 만든 server-only `IfMatchVersion`에만 기반해야 한다. | missing·weak·non-decimal·version-mismatch ETag의 review/PATCH 0회 | ETag/version 조합 matrix와 exact header capture |
| NFR3.2 | PATCH body는 허용된 여덟 field의 실제 diff만 포함하며 omitted와 explicit null을 구분해야 한다. Empty/no-op 또는 금지 field 입력은 전체 요청을 거부한다. | 허용 밖 field 전송 0건, empty/no-op PATCH 0회 | Pydantic extra-forbid, omit/null snapshots, current-value comparison tests |
| NFR3.3 | Confirm은 현재 raw turn의 독립 `확인` 또는 `confirm`, tool target과 full pending/execution binding, 동일 mutation의 canonical patch·validated `IfMatchVersion` 복원 증거를 모두 요구한다. U1은 binding 검증, confirmed 표시와 `consume_once`를 한 transaction으로 완료해 evidence를 반환하며 관찰 가능한 confirmed 중간 상태를 남기지 않는다. | 증거 하나라도 없거나 불일치하면 consume/PATCH 0회, mutation당 execution owner ≤1 | binding matrix, hash revalidation, transaction crash injection, deterministic concurrent-confirm barrier |
| NFR3.4 | PATCH는 저장된 validated `IfMatchVersion`을 변형·재구성하지 않고 `If-Match`에 넣는다. U3 `TicketOperationPolicyV1`이 confirmation execution별 단일 in-memory `patch_attempt_count`를 소유하며 기본 상한은 1이다. NFR3.6의 authoritative no-apply `token_expired` 401에서만 같은 patch/version으로 추가 1회를 허용해 절대 상한은 2가 된다. Gateway, tool wrapper와 reconciliation은 이 밖의 hidden retry를 수행하지 않는다. | 일반 outcome에서 PATCH ≤1, typed no-apply 401 경로에서만 PATCH ≤2, wire body와 `If-Match` exact match 100% | MockTransport request counter/header/body assertion, 401/timeout/5xx matrix |
| NFR3.5 | 412·428·timeout·transport error 또는 적용 여부가 불명확한 401 뒤에는 PATCH를 재전송하지 않고 최신 상세를 읽어야 한다. 모든 기대 변경과 `new_version > base_version`이 확인될 때만 success가 된다. | conflict/ambiguous 뒤 추가 PATCH 0회, 권위 증거 없는 success 0건 | post-outcome detail fixtures, partial/different/no-read cases |
| NFR3.6 | 첫 PATCH가 authoritative 계약상 미적용이 보장된 `token_expired` 401일 때만 U3 execution에 one-shot refresh reservation을 durable하게 소비하고 U1 `UpdateCredentialRefreshPortV1`을 최대 1회 호출한 뒤 동일 patch/version으로 두 번째이자 마지막 PATCH를 호출할 수 있다. 두 번째 PATCH의 모든 outcome, 그 외 401, 이미 `patch_attempt_count = 2`인 상태는 추가 호출 없이 ambiguous 또는 안전 오류가 된다. 429는 검증된 `Retry-After`만 반환하고 기다리거나 재시도하지 않는다. | execution별 refresh port invocation ≤1, PATCH 총계 ≤2, crash 뒤 second refresh 0회, non-guaranteed/second 401 recall 0회, 429 sleep/retry 0회 | durable reservation/generation recovery, shared operation-policy counter, refresh counter, fake clock, two-401 and mixed-outcome classification tests |
| NFR3.7 | revise는 새 U3 execution을 `staged`로 저장한 뒤 U1 `replace_update_pending(expected_old, replacement)`의 exact-old transaction을 사용하고, 성공 후 exact-binding expected-state CAS로 `active` 승격해야 한다. 검증·replacement 실패는 이전 review를 보존한다. | invalid/stale revise와 publication failure에서 이전 review 보존 100%, actor scope당 실행 가능한 update review ≤1 | write-failure injection, exact-old affected-row assertion, CAS transitions, confirm/revise race |
| NFR3.8 | U3는 기존 server-session SQLite 안의 `ticket_tools_update_v1.pending_update_executions`와 migration을 단독 소유해야 한다. Migration은 U1 `ticket_tools_state_v1` 뒤/U3 plugin 활성화 전에 적용하며 U1·U2 namespace를 수정하지 않는다. | migration 순서 위반 0건, cross-owner write 0건, 미적용 migration에서 plugin/PATCH 활성화 0건 | migration inventory/order test, namespace write spy, startup activation test |
| NFR3.9 | 접근·startup·lifecycle 경계에서 unmatched·expired staged row와 terminal/missing U1 pending의 execution을 멱등 retire/cleanup해야 한다. 저장 corruption, actor·patch hash·ticket·base version 불일치 또는 crash recovery 판정 불가에서는 authority를 복원하지 않는다. | mismatch/corruption/orphan 뒤 PATCH 0회, 동일 cleanup 반복의 추가 부작용 0건 | tamper, truncated row, staged/active/retired restart, repeated cleanup tests |
| NFR3.10 | active 승격 뒤 review 응답 유실 시 U3 내부 locator는 exact user/session/conversation/ticket 범위의 active row를 최대 하나만 반환하고 U1 pending과 모든 binding을 재검증해야 한다. Version이 같으면 같은 pending reference와 review를 복구하고, 다르면 PATCH 없이 conflict와 revise/cancel을 안내한다. | 다른 actor·ticket 또는 staged/retired row 반환 0건, 응답 유실 뒤 중복 pending 생성 0건 | response-loss/restart, actor isolation, ticket mismatch, version-drift recovery tests |

## 복구·회귀·검증 요구사항

| ID | 요구사항 | 측정 기준 | 검증 방법 |
|---|---|---|---|
| NFR5.1 | U3 추가 후 기존 37개 테스트와 신규 테스트는 모두 통과하고, 고정 model·reasoning·tracing, 사용자 전환, session, conversation history/clear, 기존 UI·API 계약의 승인되지 않은 변경이 없어야 한다. | 전체 테스트 통과율 100%, 승인되지 않은 회귀 0건 | 기준선과 완료본의 동일 명령 회귀, response snapshot, Agent config assertion |
| NFR6.1 | U3가 새로 만들거나 변경한 애플리케이션 코드의 line coverage는 80% 이상이어야 하며 각 테스트 가능한 계층 구현 직후 해당 pytest를 실행해야 한다. | changed-code line coverage ≥80% | repository changed-line coverage script와 계층별 pytest evidence |
| NFR6.2 | 자동화 테스트는 FakeModel과 `httpx.MockTransport`만 사용하고 예상하지 않은 실제 OpenAI·ITSM 네트워크를 차단해야 한다. | 실제 외부 호출 0건 | network-deny fixture와 unexpected-call failure assertion |
| NFR7.1 | Update용 상세 조회는 시도별 `ITSM_TIMEOUT_SECONDS`, 최초 포함 최대 2회와 250ms 고정 지연을 사용한다. PATCH는 기본 1회이며 authoritative no-apply `token_expired` 401의 one-shot refresh continuation만 총 2회까지 허용한다. Conflict·ambiguous·429·그 밖의 outcome에 의한 PATCH 자동 재전송은 0회이고 429 자동 대기도 0회다. | 상세 조회 ≤2회, PATCH 총계 ≤2이면서 예외 밖 재전송 0회, refresh ≤1, 429 wait 0초 | fake clock, shared operation-policy counters, validated Retry-After and two-attempt boundary cases |
| NFR7.2 | process restart와 모든 crash point에서도 확인되지 않은 변경을 성공으로 추측하지 않아야 한다. Canonical 실행 자료나 authority의 복원이 불완전하면 ambiguous 또는 failed로 종료한다. | 판정 불가 outcome의 success 표시 0건 | restart snapshots and failure injection at stage/replacement/activation/consume/network boundaries |
| NFR8.1 | U3 수정 시나리오는 동일 계정·환경·network·warm cache·동일 기준 version의 생성형 데이터로 기존 ITSM 화면과 각각 3회 측정 가능해야 한다. Assistant 중앙 완료 시간은 기존 방식보다 짧고 외부 화면 전환은 0회여야 한다. | 방식별 유효 trial 3회, Assistant 외부 화면 전환 0회, median 개선 | NFR8 측정 schema와 U4 실행 evidence |
| NFR9.1 | 변경 전후 review, confirmation, cancel, success, auth error, conflict, rate limit, ambiguous, invalidated와 unavailable 상태 및 다음 행동은 plain text로 제공되어야 한다. | 색상·아이콘·위치에만 의존하는 상태 0건 | keyboard-only·screen-reader text snapshot·live announcement regression |

NFR4의 목록 기본 20·최대 100과 cursor 응답 범위는 read Unit 책임이며 U3 ticket-update에는 적용되지 않는다.

## 위협과 통제 매트릭스

| 위협·실패 | 예방 통제 | 탐지·회복 통제 | Fail-closed 결과 |
|---|---|---|---|
| 모델 또는 외부 텍스트가 다른 사용자·confirm을 주장 | server session identity, raw-current-turn evidence, structured untrusted data | actor/target/patch/version binding tests | PATCH 0회, 같은 review 또는 새 prepare 안내 |
| 비밀·canonical patch·`IfMatchVersion`이 결과나 로그로 유출 | server-only types, allowlisted projections, redaction boundary | canary sweep over model/result/log/error/test output | safe generic error and no raw detail |
| stale detail이나 forged ETag로 덮어쓰기 | body version과 strong ETag exact validation | header capture and 412/428 reconciliation | review/PATCH 금지 또는 새 review |
| 두 confirm이 경쟁 | U1 consume-once plus one execution authority | deterministic barrier and transport call counter | 한 caller만 execution을 소유하며 그 owner만 NFR3.6 상한 안에서 PATCH, 나머지는 current state 관찰 |
| revise와 이전 confirm이 경쟁 | U1 exact-old replacement transaction과 U3 expected-state CAS | affected-row count, deterministic barrier and crash matrix | 한 경로만 승리; loser는 PATCH 0회 |
| PATCH response loss | automatic resend forbidden | latest authoritative detail comparison | 완전 적용 증거 전 success 금지 |
| durable execution row corruption | exact mutation/actor/ticket/hash/version match and rehash | startup/access integrity scan | authority 복원 금지, PATCH 0회 |
| review 응답 유실 뒤 다른 row 재발견 | exact actor/session/conversation/ticket locator와 U1 재결합 | response-loss/restart isolation test | 같은 pending만 복구하거나 fail closed |
| migration 또는 namespace 소유권 위반 | U1 뒤/U3 activation 전 migration과 owner별 write boundary | migration order와 write-spy test | plugin/PATCH 활성화 중단 |

## 검증 증거와 차단 조건

- Contract tests must prove exact ETag/version derivation, full confirmation binding, consume-once ownership, zero automatic PATCH retries, authoritative reconciliation and safe presentation.
- Deterministic failure injection must cover every committed boundary between detail read, review publication, confirmation consumption, PATCH invocation, reconciliation and terminal result.
- Security tests must capture every human/model/log/error boundary and search for unique credential, patch, header and external-text canaries.
- Code Generation must implement the approved C-02/C-05 exact-old replacement, U3 store/migration, cleanup and verification contracts without weakening or replacing them with selector invalidation or in-memory authority.
- A contract mismatch, migration-order or owner violation, unexpected network call, missing reproducible 80% changed-code coverage evidence, extra PATCH, stale success, or canary leak blocks Unit completion.

## 잔여 위험과 후속 설계 의무

기존 R-02와 R-05 차단 항목은 최신 C-02/C-05 및 기능 설계에서 해결됐다. 남은 위험은 단일-process SQLite와 application lock 경계 밖의 다중-process 동시성으로, 이번 Unit은 기존 배포 형태를 유지하며 이를 확장하지 않는다. 구현은 exact-old affected-row 결과, U3 CAS, actor-scoped locator와 deterministic crash/restart evidence를 완료 조건으로 삼고, 향후 다중 process 배포가 도입되면 shared lock 또는 동등한 transaction 경계를 별도 설계해야 한다.
