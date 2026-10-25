# U2 Ticket Write — 보안·품질 비기능 요구사항

## Sources

- `construction/u2-ticket-write/functional-design/functional-spec.md` — 등록 확인, ledger-first 실행, 복구 흐름과 남은 계약 경계
- `construction/u2-ticket-write/functional-design/rules.md` — 입력 검증, confirmation, 멱등성, 위임 인증과 안전한 결과 규칙
- `inception/requirements-analysis/requirements.md` — NFR1~NFR9 및 FR3·FR5·FR6의 수치화된 기준
- `inception/contract-design/contract-summary.md` — C-01, C-03A, C-04, C-06, C-07의 V1 타입·저장·호출 상한
- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md` — 기존 Python/FastAPI/Agents SDK/httpx/SQLite/pytest 경계
- `construction/u2-ticket-write/nfr-requirements/nfr-requirements-questions.md` — 확인된 계약 호환·테스트·운영 기준

## 보안과 신뢰 경계 요구사항

| ID | 요구사항 | 측정 기준 | 검증 방법 |
|---|---|---|---|
| NFR1.1 | 액세스 토큰, client secret, OpenAI API key와 Authorization 값은 모든 U2 durable state에도 저장하지 않아야 한다. Idempotency key와 canonical request bytes는 접근 통제된 server-only create ledger에만 보존하고 모델 입력, function-tool schema·결과, 사용자 응답, history, 애플리케이션 로그, metric, 테스트 실패 출력과 HTTP 오류 응답에 나타나지 않아야 한다. | credential durable 저장 0건, 관찰 가능 경계별 key·bytes·credential canary 노출 0건 | schema snapshot, FakeModel capture, log/error/metric capture, server-only/public persistence projection 비교, presentation contract test |
| NFR1.2 | 제목·설명·카탈로그 label·문제 응답 등 ITSM-origin 문자열은 구조화되고 escape된 비신뢰 데이터로만 취급해야 한다. | 외부 문자열로 신원·권한·confirmation·도구 선택·retry 정책이 달라지는 사례 0건 | 지시문·HTML·Markdown 제어문자·가짜 confirm 문자열 주입 테스트 |
| NFR1.3 | raw exception, unrestricted upstream body, problem detail, 요청·응답 header는 `SafeErrorV1` 또는 shared mutation result 경계를 통과하지 않아야 한다. | 허용 목록 밖 field 노출 0건 | 401/403/409/422/429/5xx, timeout, malformed response 매핑 테스트 |
| NFR2.1 | 모든 ticket-create POST는 현재 HttpOnly server session에서 복원한 현재 사용자의 delegated capability를 사용해야 한다. | delegated token 사용 100%, service token을 사용한 ticket POST 0건 | transport authorization canary와 사용자 전환 fixture |
| NFR2.2 | user, session, conversation, operation, payload hash, 15분 expiry와 current raw user turn 중 하나라도 맞지 않으면 실행할 수 없어야 한다. | 불일치·만료·quoted/embedded/model-generated confirm에서 POST 0회 | fake clock, actor switch, clear/logout/expiry, current-turn decision contract test |
| NFR2.3 | pre-confirm ledger row와 idempotency key는 서버 전용이며 possession 자체가 권한이 아니다. U1 pending binding과 successful consume evidence 없이는 execution claim을 얻을 수 없어야 한다. | 미확인·취소·교체·만료·고아 ledger row에서 POST 0회 | orphan/replacement/cancel/restart/concurrent-confirm test |

## 데이터 무결성과 계약 정합성 요구사항

| ID | 요구사항 | 측정 기준 | 검증 방법 |
|---|---|---|---|
| NFR3.1 | U2 create의 유일한 authoritative flow는 승인된 `ticket_tools_create_v1.ticket_create_attempts`와 U1 공개 `put`·`get`·`confirm`·`consume_once`·`invalidate`만 사용하는 ledger-first/public-port-only 흐름이어야 한다. | 승인되지 않은 U2 table 0개, C-01 외 U1 repository 호출 0개, 서로 배타적인 create flow 0개 | migration inventory, repository interface contract test, Functional Design fingerprint와 review receipt |
| NFR3.2 | Prepare/revise는 독립 `create_attempt_id`, actor binding, payload hash, serialization version, canonical bytes·hash, 하나의 CSPRNG key를 가진 `prepared` row를 U1 pending review보다 먼저 저장해야 한다. U1 consume이 반환한 `mutation_id`·`confirmed_at`을 같은 actor·payload row에 idempotent하게 결합하기 전에는 실행 권한이 없어야 한다. | pending review가 있으나 matching ledger가 없는 committed 상태 0건, evidence 없는 row의 POST 0회, 다른 mutation 재결합 성공 0건 | write-failure injection, evidence-binding CAS, direct row assertions |
| NFR3.3 | Revise/새 review는 이전 evidence 없는 `prepared` row를 expected-state CAS로 먼저 terminalize하고 이전 U1 pending을 invalidate한 뒤에만 새 ledger·pending을 공개해야 한다. 이전 confirm이 evidence를 먼저 결합했거나 claim을 얻으면 revise는 실패해야 한다. | actor scope당 실행 가능한 prepared row ≤1, stale review POST 0회, confirm/revise race의 승자 1개 | deterministic barrier at terminalize/invalidate/evidence-bind boundaries, affected-row count, POST counter |
| NFR3.4 | 모든 POST는 bound confirmation evidence와 `attempt_count < 2`를 전제로 unique `claim_id`·`claim_deadline_at`·`in_flight`·증가된 count를 network I/O 전에 한 CAS로 commit한 승자만 수행해야 한다. Deadline 전 active claim takeover는 0회다. | 동시 execution claim 1개 이하, count 없는 POST 0회, active-claim takeover 0회 | deterministic concurrency barrier, fake clock, affected-row count, transport counter |
| NFR3.5 | 최초·credential-refresh recall·restart reconciliation은 하나의 key와 byte-identical stored body만 사용하고 총 POST 시도는 2회를 넘지 않아야 한다. | 같은 key·body로 생성 티켓 최대 1개, 다른 body 재사용 성공 0건, POST ≤2 | MockTransport byte comparison, key capture, global attempt-count assertions |
| NFR3.6 | 변경 미적용이 보장된 token-expired 401은 `retryable_no_apply`, 불명확 결과는 reconciliation 뒤에만 `retryable_after_reconcile`로 기록해야 한다. Transport outcome write는 expected `in_flight`와 send `claim_id`를 비교한다. Ambiguous 또는 deadline이 지난 `in_flight`의 reconciliation owner는 Functional Design의 `begin_stale_claim_reconciliation` expected-state/기존 `claim_id` CAS로 하나만 획득하며, `record_reconciliation`도 같은 기존 `claim_id`와 해당 reconciliation 대상 상태를 비교해야 한다. 별도 recovery claim field나 identity는 추가하지 않는다. | ambiguous 직접 재POST 0회, stale transport/reconciliation overwrite 0건, 같은 기존 claim에 대한 recovery owner 1개 이하 | fake clock claim expiry, late-response barrier, restart snapshot, existing-claim transport/reconciliation CAS matrix |
| NFR3.7 | Created 또는 `Idempotent-Replayed` 응답의 ticket ID가 없으면 `completed` 또는 사용자-visible success가 될 수 없다. 두 번째 불명확 결과는 추가 POST가 금지된 terminal `ambiguous`다. | authoritative evidence 없는 성공 표시 0건, third POST 0회 | response-loss, malformed-success, replay evidence, exhausted-budget tests |
| NFR3.8 | successful evidence binding 시 `retained_until`을 `max(existing, confirmed_at + 24h)`로 단조 연장해야 한다. Confirmed row는 lifecycle 변화와 restart를 넘어 그 경계까지 유지되고, 미확인 orphan은 실행 권한 없이 최초 `created_at + 24h` 뒤 정리할 수 있다. | confirmed row마다 `retained_until >= confirmed_at + 24h`, unconfirmed row마다 `retained_until >= created_at + 24h`, 경계 전 삭제 0건 | fake clock, repeated bind, lifecycle cleanup, restart persistence test |
| NFR3.9 | 첫 POST 전 만료·만료 임박 또는 `retryable_no_apply`에서 credential refresh 권한은 ledger의 one-shot reservation을 expected-state CAS로 선점한 한 caller에게만 부여해야 한다. Reservation은 base credential generation, `refresh_used_at`, 상태 `reserved`를 refresh port 호출 전에 durable commit한다. 같은 process의 경쟁 caller는 `reserved`를 current state로 관찰할 뿐 실패·복구 write나 refresh 호출을 하지 않는다. `recover_refresh_after_restart`는 실제 process restart 경계에서만 실행하고, same-actor session generation이 base보다 크면 `committed`, 같거나 작으면 `failed`와 `terminal_failure`로 한 번 전이하며 refresh port는 다시 호출하지 않는다. 별도 refresh deadline field는 추가하지 않는다. | create attempt당 refresh invocation ≤1, concurrent refresh owner ≤1, live same-process observer의 recovery write 0건, restart 뒤 두 번째 refresh 0회 | deterministic refresh barrier, process-restart snapshot, generation-advance/no-advance recovery, concurrent-caller tests |
| NFR3.10 | Refresh reservation이 이미 사용된 attempt의 counted POST가 다시 authoritative no-apply 401을 반환하면 FD-U2-03 step 9의 terminal authentication failure로 끝나야 한다. Functional Design의 기존 `record_definitive_outcome` expected `in_flight`·current `claim_id` fence와 one-shot refresh guard를 사용하며, 새 repository operation이나 별도 terminal transition을 발명하지 않는다. 중간 구현 상태가 `retryable_no_apply`를 거치더라도 외부 실행 권한을 다시 만들거나 refresh·send claim을 추가로 허용할 수 없다. | second refresh 0회, second-401 뒤 추가 claim·POST 0회, stale claimant terminal overwrite 0건 | proactive-refresh-then-401, 401-refresh-then-401, late-old-claim response와 expected-claim-ID matrix |

## 복구·회귀·검증 요구사항

| ID | 요구사항 | 측정 기준 | 검증 방법 |
|---|---|---|---|
| NFR5.1 | U2 추가 후 기존 37개 테스트와 신규 테스트는 모두 통과하고, 고정 model·reasoning·tracing, 사용자 전환, session, conversation history/clear, 기존 UI·API 계약의 승인되지 않은 변경이 없어야 한다. | 전체 테스트 통과율 100%, 승인되지 않은 회귀 0건 | 기준선과 완료본의 동일 명령 회귀, response snapshot, Agent config assertion |
| NFR6.1 | U2가 새로 만들거나 변경한 애플리케이션 코드의 line coverage는 80% 이상이어야 하며 각 계층 구현 직후 해당 pytest를 실행해야 한다. | changed-code line coverage ≥80% | 문서화된 coverage 명령과 계층별 pytest evidence |
| NFR6.2 | 자동화 테스트는 FakeModel과 `httpx.MockTransport`만 사용하고 예상하지 않은 실제 OpenAI·ITSM 네트워크를 차단해야 한다. | 실제 외부 호출 0건 | network-deny fixture와 unexpected-call failure assertion |
| NFR7.1 | 모든 ticket POST는 시도별 `ITSM_TIMEOUT_SECONDS`를 사용하고 최초 포함 총 2회 상한을 공유한다. Token refresh invocation은 create attempt당 최대 1회이고, 같은 process의 `reserved` observer는 owner를 방해하지 않으며 restart 복구는 durable generation evidence만 사용한다. Refresh 뒤 POST도 같은 상한을 소비하고 429 자동 sleep·retry는 0회다. | POST ≤2, refresh ≤1, same-process refresh takeover 0회, 429 후 추가 호출 0회 | fake clock, transport·refresh counters, deterministic refresh barrier, restart generation cases, validated Retry-After cases |
| NFR7.2 | timeout·connection loss·response loss·불완전 success는 성공으로 추측하지 않고 ambiguous를 보존해야 한다. 두 번째 시도도 동일 key·bytes만 사용할 수 있다. | unknown outcome의 성공 표시 0건, 새 key reconciliation 0건 | ambiguity matrix와 restart/replay contract tests |
| NFR8.1 | U2 등록 시나리오는 동일 계정·환경·network·warm cache·생성형 일회용 데이터로 기존 ITSM 화면과 각각 3회 측정 가능해야 한다. Assistant 중앙 완료 시간은 기존 방식보다 짧고 외부 화면 전환은 0회여야 한다. | 방식별 유효 trial 3회, Assistant 외부 화면 전환 0회, median 개선 | NFR8 측정 schema와 U4 실행 evidence |
| NFR9.1 | 입력 수정, 전체 review, confirmation 선택, success, auth error, rate limit, ambiguous, unavailable 상태와 다음 행동은 plain text로 제공되어야 한다. | 색상·아이콘·위치에만 의존하는 상태 0건 | keyboard-only·screen-reader text snapshot·live announcement regression |

NFR4의 목록 기본 20·최대 100과 cursor 응답 범위는 read Unit 책임이며 U2 ticket-create에는 적용되지 않는다.

## 위협과 통제 매트릭스

| 위협·실패 | 예방 통제 | 탐지·회복 통제 | Fail-closed 결과 |
|---|---|---|---|
| 모델 또는 외부 텍스트가 다른 사용자·confirm을 주장 | server session identity, raw-current-turn evidence, structured untrusted data | actor/payload binding tests and safe audit category | POST 0회, 새 review 요구 |
| 비밀·key·canonical bytes가 결과나 로그로 유출 | server-only types, allowlisted projections, redaction boundary | canary sweep over model/result/log/error/test output | safe generic error and no raw detail |
| prepare 중단으로 ledger-only row가 남음 | ledger row alone has no authority; U1 pending is published second | expiry/lifecycle orphan scan and deterministic cleanup | POST 0회 |
| Revise와 이전 confirm이 경쟁 | 이전 prepared terminalization과 evidence binding의 expected-state CAS | deterministic barrier와 affected-row count | 한 경로만 승리, stale POST 0회 |
| 두 confirm이 경쟁 | U1 consume-once plus ledger CAS execution claim | affected-row count and transport call counter | 한 caller만 실행, 나머지는 durable state 관찰 |
| claim 직후 process 중단 | count, claim ID/deadline, `in_flight` commit before I/O | deadline 전 takeover 차단, 이후 단일 reconciliation owner | same-key reconciliation only |
| Ambiguous 또는 stale claim 조정 경쟁 | expected state·기존 claim ID CAS로 단일 reconciliation owner 획득 | 같은 claim의 recovery owner와 reconciliation outcome writer 1개 이하 | loser는 current state만 관찰 |
| Refresh 경쟁 또는 reservation 뒤 crash | base generation을 포함한 durable reservation을 호출 전에 사용 처리 | same-process observer no-op, 실제 restart에서 session generation 비교, refresh invocation counter와 restart row snapshot | live owner 조기 실패 0건, refresh 최대 1회, restart에서 불확실하면 fail closed |
| 이미 사용된 refresh 뒤 다시 no-apply 401 | expected send claim-ID fence와 one-shot refresh guard | second-refresh·second-retry counter | FD-U2-03 terminal authentication failure, 추가 refresh·POST 0회 |
| 늦은 이전 claimant 응답 | 모든 outcome write의 expected claim-ID fence | late-response barrier | 최신 claim 상태 유지, stale write 0건 |
| response loss 또는 malformed success | evidence-gated completion | durable ambiguous state and at most one reconciliation | 성공 표시 금지 |
| key/body 변조 또는 storage corruption | stored-byte hash and immutable version/key binding | pre-send rehash and mismatch alert category | network I/O 전 terminal safe failure |
| lifecycle cleanup이 ledger를 조기 삭제 | minimum retention boundary | fake-clock cleanup assertions | retention 전 삭제 건너뜀 |

## 검증 증거와 차단 조건

- Contract tests must prove ledger-first ordering, fail-closed review replacement, U1 evidence binding, 기존 send claim identity·deadline을 재사용하는 reconciliation ownership, state-specific outcome fencing, durable one-shot refresh reservation의 same-process noninterference와 restart generation recovery, 이미 사용된 refresh 뒤 401의 terminal authentication result, byte-identical attempts, and shared V1 result compatibility.
- Deterministic failure injection must cover every committed boundary between ledger creation, U1 pending publication, confirm/consume, execution claim, gateway return, and terminal ledger update.
- Security tests must capture every human/model/log/error boundary and search for unique credential, key, and canonical-body canaries.
- Code Generation must stop rather than invent a new table, cross-owner transaction API, ambiguous direct-retry path, or unfenced outcome write.
- A test failure, missing reproducible 80% changed-code coverage evidence, unexpected network call, unbounded attempt path, live same-process refresh owner에 대한 recovery write, second refresh, stale-claim overwrite, or contract mismatch blocks Unit completion.

## 잔여 위험과 후속 설계 의무

기능 설계는 ledger-first/public-port-only 흐름으로 정렬되고 재검토됐다. 후속 NFR Design은 기존 send `claim_id`를 보존하는 stale-claim reconciliation ownership, 같은 process의 reserved-refresh observer no-op, 실제 restart에서의 credential-generation recovery, 이미 사용된 refresh 뒤의 terminal authentication result, `retryable_no_apply`와 `retryable_after_reconcile`의 CAS predicate, 늦은 claimant outcome fencing을 구체적인 테스트 계약으로 확정해야 한다. 다중 process coordination은 현재 단일-process 범위 밖이며, 배포 모델이 바뀌면 shared lock 또는 transactional arbitration을 다시 설계한다.
