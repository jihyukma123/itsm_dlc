# U1 Ticket Read Skeleton — 보안 및 교차 품질 요구사항

## Sources

- `construction/u1-ticket-read-skeleton/functional-design/functional-spec.md` — 신원, 조회, 복구, 확인, presentation, lifecycle 흐름
- `construction/u1-ticket-read-skeleton/functional-design/rules.md` — BR1.1–BR6.2 안전 불변식
- `inception/requirements-analysis/requirements.md` — NFR1–NFR9와 FR5–FR7
- `inception/contract-design/contract-summary.md` — C-01, C-02, C-03, C-03A, C-06, C-07 V1 계약
- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md` — 기존 runtime, 저장소, 테스트, 설정 경계
- `construction/u1-ticket-read-skeleton/nfr-requirements/nfr-requirements-questions.md` — 확인된 NFR 해석

## 적용 범위와 자산

U1은 기존 서버 세션과 Agent 대화 안에서 `ticket_read`를 제공하고 U2·U3가 사용할 공통 capability, gateway, cursor, confirmation, registry, presentation-history 경계를 소유한다. 보호 대상은 다음과 같다.

| 자산 | 보호 목표 | 신뢰 원천 |
|---|---|---|
| 현재 사용자 신원·권한 | 모델이나 외부 텍스트로 변경 불가 | HttpOnly 세션으로 복원한 서버 사용자 |
| 서버 세션 레코드 | 기존 인증·사용자·권한·위임 credential 의미 보존과 절대 만료 강제 | 기존 ServerSession schema에 additive하게 저장한 `session_expires_at` |
| 사용자 위임 credential | 티켓 outbound 경계 밖 노출 0건 | 서버 전용 request capability |
| 티켓 데이터 | 권한 범위 보존, 허용 필드만 노출 | ITSM API v2 |
| continuation state | 사용자·세션·대화·정확한 query에 결합 | U1 cursor repository |
| pending mutation state와 소비 증거 | 정확한 actor·operation·payload·target·version에 결합하고 `confirm`과 `consume_once`를 분리하며 증거를 한 번만 발급 | U1 confirmation repository |
| U2 durable create-attempt ledger | U1 lifecycle cleanup으로 삭제·재작성되지 않으며 소비 증거만으로 POST 권한이 생기지 않음 | U2 `ticket_tools_create_v1` namespace와 C-01/C-04 계약 |
| assistant presentation metadata | 저장된 assistant message와 정확히 상관 | 기존 conversation history와 U1 companion repository |
| 로그·오류·테스트 출력 | 비밀과 원본 upstream detail 비노출 | 서버 소유 allowlist와 redaction |

## 상세 요구사항

| ID | 요구사항 | 측정 가능한 합격 기준 | 검증 방법 |
|---|---|---|---|
| NFR1.1 | access token, client secret, OpenAI API key, `Authorization` 값은 model input, function-tool schema·result, presentation, application log, HTTP error response, 테스트 실패 stdout·stderr·traceback·assertion diff 또는 pending/cursor/history/create/update persistence row에 들어가지 않아야 한다. 사용자 위임 credential의 유일한 허용 persistence 경계는 기존 접근 제한된 ServerSession의 `itsm_token` field이며 IdentitySession만 복원·원자 교체할 수 있다. | 허용된 ServerSession credential field 밖 모든 관찰 경계와 수집한 실패 출력의 비밀 canary 발견 0건; session row 안 credential 복제 field 0건; refresh 성공 응답 전에 기존 field 원자 교체율 100% | 경계별 고유 canary를 주입해 schema serialization, 비-session 기록 row, captured log, HTTP body를 검사하고, canary가 포함된 의도적 실패를 격리 실행해 stdout, stderr, traceback, assertion diff를 수집·자동 검색한다. 별도 session contract test는 credential field가 IdentitySession 경계에서만 읽히고 refresh transaction에서 원자 교체되며 다른 row로 복제되지 않음을 검사한다. |
| NFR1.2 | 예외 문자열, raw problem detail, raw response body와 header는 gateway 밖으로 전달하지 않고 `SafeErrorV1`의 정확한 allowlist만 사용해야 한다. | 허용되지 않은 field·원문 발견 0건; 모든 실패 결과가 V1 schema 검증 통과 | 악의적 problem body와 header를 MockTransport로 주입하고 tool/API/log 결과를 검사한다. |
| NFR1.3 | ITSM 제목·설명·서비스·영향 문구는 100% `itsm_untrusted` 데이터로 취급하고 최종 목적지에서 text node로 escape해야 한다. | 외부 문자열의 trust 표기 누락 0건; HTML/Markdown 제어 문자열의 실행·구조 변경 0건 | 지시문·markup payload를 목록·상세·presentation·history 복원 경로에 주입한다. |
| NFR1.4 | 외부 텍스트와 model/tool argument는 현재 사용자, 권한, confirmation, registry 선택, system/developer instruction을 바꾸지 못해야 한다. | 공격 fixture로 인한 신원·권한·확인·도구 호출 변화 0건 | 정상 control case와 공격 case의 server-derived context 및 outbound request를 비교한다. |
| NFR2.1 | 모든 티켓 endpoint 호출은 현재 서버 세션 사용자의 위임 token을 사용해야 한다. | 관찰된 티켓 요청 중 위임 token 사용률 100% | 각 요청의 credential-kind marker를 MockTransport에서 판정한다. token 값 자체는 출력하지 않는다. |
| NFR2.2 | service token은 티켓 list/detail endpoint에 사용하지 않아야 한다. | service-token 티켓 호출 0건 | service-token canary가 티켓 요청에 나타나면 테스트를 실패시킨다. |
| NFR2.3 | user/session/conversation은 server capability에서만 오고 model text나 tool input의 동일 이름 field를 무시해야 한다. | forged identity가 outbound subject·repository binding을 바꾸는 사례 0건 | 다른 사용자 ID·role을 tool/ITSM text에 주입하고 실제 binding을 검사한다. |
| NFR2.4 | 목록 누락이나 detail 404는 보이지 않는 티켓의 존재를 추론할 수 없게 해야 한다. | 404 응답 표현이 absent와 invisible fixture 사이에서 의미상 동일; 숨은 record 수·ID 노출 0건 | 두 원인 fixture가 같은 `failed/not_found` safe result와 message key를 내는지 비교한다. |
| NFR2.5 | 보호 요청은 persisted `session_expires_at`이 현재 서버 시각보다 미래인 세션에만 capability를 발급해야 한다. 생성 시각부터 8시간인 절대 만료는 활동이나 token refresh로 연장하지 않고, 만료 경계에서는 revocable state 정리와 세션 삭제를 Runner·ITSM보다 먼저 완료해야 한다. | `now < session_expires_at`에서만 capability 발급; 정확한 만료 시각과 이후의 capability·Runner·ITSM 호출 0건; restart 후 deadline 연장 0건 | just-before·exact·just-after clock fixture, token refresh·activity, restart, cleanup failure와 idempotent retry를 검증한다. |
| NFR2.6 | 같은 conversation의 Runner 실행, SDK history 접근, presentation commit과 user switch·logout·conversation clear·session expiry cleanup은 하나의 application conversation lock으로 직렬화해야 한다. 각 lifecycle event는 lock 획득 뒤 expected user/session/conversation을 재검증하고 presentation을 history보다 먼저 지운 뒤 revocable-state cleanup과 terminal lifecycle commit까지 lock을 유지한다. Runner 직후에는 원래 actor scope와 persisted expiry를 response 또는 presentation 결정 전에 다시 검증하며, 바뀌었거나 만료됐으면 old-scope 결과를 폐기한다. | 네 lifecycle event 모두 Runner와 history DB 동시 접근 0건; post-Runner actor 변경·만료 뒤 old-scope 성공 response·presentation publication 0건; lifecycle commit 뒤 old-scope SDK message/session과 presentation companion 재생성 0건; session-expiry cleanup 뒤 pending/cursor/server-session row 0건 | user switch, logout, conversation clear, session expiry 각각에 대해 Runner history write barrier를 교차 실행한다. event가 같은 lock에서 대기하고 lock 뒤 actor scope를 재검증하며 presentation-before-history 순서와 terminal commit까지 lock 보유를 관찰한다. commit 뒤 old-scope message·metadata가 0이고, expiry에서는 모든 revocable/session row와 성공 publication도 0인지 검증한다. |
| NFR2.7 | `CredentialRefreshPortV1`은 U2가 durable하게 사용 처리하고 단 한 번 invocation claim한 `CredentialRefreshReservationV1`만 받아야 한다. U2는 create-attempt·user·session·conversation·used-at·nonce를 server-authenticated opaque `refresh_reservation_id`에 결합하고, U1은 U2 storage를 읽지 않은 채 authenticity와 현재 capability binding을 검증한다. 한 호출은 token exchange 최대 1회이며 성공은 기존 ServerSession credential의 원자 commit 뒤에만 반환한다. | user/session/conversation/create-attempt/deadline mismatch의 exchange 0회; restart replay와 같은 attempt의 두 번째 U1 invocation 0회; accepted invocation당 exchange 1회 이하; 성공 반환 전 credential commit 누락 0건; pre/post-commit crash 뒤 second exchange 0회 | U2 durable repository fake와 reservation verifier를 사용해 각 binding mismatch, 변조, expiry, restart replay, pre-commit failure, commit 직후 응답 전 crash를 주입한다. U1의 U2 table 접근 0건, exchange counter, 기존 session row의 atomic replacement, 같은 actor capability와 secret 비노출을 검사한다. |
| NFR3.1 | U1의 server-only `TicketOperationPolicyV1.read_for_update` port는 strong quoted-decimal ETag가 public version과 정확히 일치할 때만 typed `ReadForUpdateResultV1(detail, IfMatchVersion)`을 반환해야 한다. missing·weak·non-decimal·mismatched ETag에서는 ordinary detail 의미를 바꾸지 않으면서 read-for-update만 `SafeErrorV1(code=upstream_unavailable)`로 실패해야 한다. | valid ETag에서 typed `ReadForUpdateResultV1` 외 성공 shape 0건; invalid ETag에서 read-for-update 성공 또는 usable `IfMatch` 생성 0건; 같은 invalid fixture의 ordinary detail 성공률 100%; U3가 typed port를 import·consume하지 못하는 사례 0건 | 동일 response fixture를 ordinary-detail과 read-for-update 두 경로에 적용하는 dual-path contract matrix, U3 import/consumer contract test로 검증한다. 실제 PATCH 성공 무결성은 U3에서 완결한다. |
| NFR3.2 | pending mutation의 `confirm`과 `consume_once`는 별도 원자 연산이어야 한다. `confirm`은 정확히 결합된 `pending` row를 `confirmed`로만 바꾸고 transport 권한을 반환하지 않는다. `consume_once`는 같은 binding을 다시 검증해 `confirmed` row를 `consumed`로 한 번만 바꾸고 정확히 `ConsumedMutationEvidenceV1 { mutation_id, confirmed_at }`만 반환한다. Confirm 직후 crash로 unexpired confirmed update가 남으면 새 prepare·revise를 거부하고 exact consume을 재개하거나 expiry/lifecycle invalidation까지 fail closed해야 한다. 이 증거만으로 POST/PATCH를 호출할 수 없으며, U1 lifecycle cleanup은 U2의 `ticket_tools_create_v1` ledger를 삭제하거나 다시 쓰지 않아야 한다. | mutation당 성공한 `consume_once` 최대 1회; confirm 결과의 transport-authority field 0건; 소비 증거 field 집합이 정확히 `{mutation_id, confirmed_at}`이고 credential·idempotency key·canonical bytes 0건; unexpired confirmed update가 있는 concurrent prepare·revise의 새 pending row와 PATCH 0건; expiry/lifecycle 전 exact-resume 외 상태 전이 0건; user switch·logout·conversation clear·session expiry 전후 U2 ledger row와 key/bytes byte 값 변경 0건; consume 뒤 U2 evidence binding 전 crash에서 POST 0건 및 같은 ledger attempt로 새 confirmation 요구율 100% | repository 상태 전이·동시 consume contract matrix, confirm 직후 fault injection, confirmed-update concurrent prepare/revise와 expiry/lifecycle fixture, crash-before-bind fault injection으로 검증한다. U2 fake ledger를 사용해 row 보존, 동일 attempt/key/bytes, 새 pending review와 재확인 요구를 관찰한다. |
| NFR4.1 | 한 list page는 기본 20, 최소 1, 최대 100으로 제한해야 한다. | limit 1·20·100은 계약대로 전달; 생략은 20; 0·101은 outbound 호출 0건 | 입력 경계와 MockTransport request query를 검증한다. |
| NFR4.2 | 100개를 넘는 결과는 silent truncation하지 않고 server-bound continuation으로 점진 제공해야 한다. `continuation_ref`는 운영체제 암호학적 난수원에서 얻은 최소 128 bit entropy를 가져야 하며 counter·timestamp·query hash만으로 만들지 않는다. | `has_more=true`일 때 valid continuation_ref 존재율 100%; raw cursor 노출 0건; 생성한 100,000개 reference 충돌 0건; 고정 prefix 뒤 순차값·timestamp-only 패턴 0건; 다른 actor가 선택한 임의 reference의 binding 통과 0건 | multi-page serialization, entropy-source seam, 100,000개 collision sample, 순차성 검사, random guessed reference와 cross-actor binding matrix를 검증한다. 통계 표본은 entropy 증명 대신 CSPRNG source contract의 보조 검증으로 사용한다. |
| NFR5.2 | 서버 세션 migration은 `entities.md`의 additive `ServerSession` 계약에 따라 기존 physical field `id`, `user_id`, `username`, `display_name`, `role`, `role_label`, `team`, `permissions`, `conversation_id`, `itsm_token`, `itsm_token_expires_at`, `created_at`의 이름, type, 선택성, 의미, 저장값을 byte-for-byte 보존하고 `session_expires_at`만 추가해야 한다. 논리 `delegated_credential`, `credential_expires_at`, `refresh_credential` 의미와 기존 token-exchange 경로도 유지해야 한다. | migration 전후 열 정의와 기존 field byte 값·session restore 결과 일치율 100%; 기존 refresh·user switch 회귀 통과율 100%; 새 expiry 때문에 fresh session으로 재발급되는 legacy row 0건 | 한 contract test가 migration 전후 PRAGMA schema·전체 legacy row snapshot, session restore, token refresh, user switch, parse 가능한 `created_at + 8시간` backfill과 malformed/missing `created_at` fail-closed backfill을 함께 검증한다. |
| NFR7.1 | read operation의 gateway HTTP 시도는 최초 포함 최대 2회이며 각 시도에 `ITSM_TIMEOUT_SECONDS`를 적용해야 한다. | operation당 HTTP 요청 수 2 이하; timeout 설정 누락 0건 | timeout·transport·500·502·503·504·401 조합을 가상 clock과 request counter로 검증한다. |
| NFR7.2 | retry 허용 오류만 250ms 뒤 한 번 재호출하고 429에는 sleep과 retry를 모두 하지 않아야 한다. | 허용 retry delay 정확히 0.25초; 429 sleep 0회·추가 HTTP 0회 | fake sleeper와 MockTransport를 사용한다. |
| NFR7.3 | 성공 evidence가 없는 결과를 성공·empty로 표시하지 않아야 한다. | malformed, exhausted, auth failure, rate limit 결과의 false-success 0건 | typed outcome matrix에서 top-level `state`와 nested error를 검사한다. |
| NFR7.4 | 한 read operation의 사용자 관찰 자동 정책 경과시간은 credential refresh를 포함해 `2 × ITSM_TIMEOUT_SECONDS + 0.25초`를 넘지 않아야 한다. refresh에 시간이 쓰이면 남은 read deadline을 줄여 상한을 보존한다. | timeout 설정 기본 10초일 때 최악 경로의 경과시간 20.25초 이하; 다른 설정에서도 공식 그대로 충족; 정책 밖 추가 sleep 0회 | 가상 monotonic clock으로 첫 timeout+retry+둘째 timeout, 첫 401+refresh+남은 deadline 안의 마지막 attempt, pre-call refresh, transient 뒤 terminal error, 429 경로를 각각 측정한다. |
| NFR9.1 | loading, succeeded, empty, failed, continuation과 다음 행동은 색·아이콘·위치에 의존하지 않는 텍스트로 제공해야 한다. | 각 상태 fixture에 상태 의미와 다음 행동 text 존재율 100% | response/presentation snapshot과 기존 live-announcement 회귀 테스트로 확인한다. |
| NFR9.2 | optional presentation이 없거나 손상돼도 기존 keyboard·screen-reader 사용 가능한 assistant text가 남아야 한다. | metadata missing·unknown·commit failure에서 text-only fallback 성공률 100% | history와 current response의 fallback 및 `announce=false` 복원 동작을 검증한다. |

## 위협과 통제

| 위협 | 공격 경로 | 예방 통제 | 탐지·검증 |
|---|---|---|---|
| 신원 혼동 | 사용자 문장이나 ITSM 텍스트가 다른 user/role을 주장 | server-session-only capability, binding exact match | forged identity fixture와 outbound subject 비교 |
| credential 유출 | schema, repr, exception, header, log, test failure | non-serializable capability, SafeError allowlist, redaction | 경계별 고유 canary 0건 assertion |
| prompt injection | 제목·설명에 confirmation 생략·추가 도구 호출 지시 | untrusted structured data, server-owned labels/actions | 공격 문자열 전후 control state 비교 |
| cursor 탈취·변조 | 다른 actor가 continuation_ref 재사용 | unpredictable reference + actor/conversation/query hash exact binding + once-only resolution | cross-user/session/conversation, tamper, replay matrix |
| confirmation 재사용 또는 소비 증거 오용 | 오래되거나 다른 payload/target/version의 pending_ref를 confirm/consume하거나 최소 증거만으로 transport를 실행 | 15분 expiry, same-operation replacement invalidation, server current-turn evidence, 분리된 `confirm`/`consume_once`, exact binding 재검증, one-time minimal evidence, downstream 실행 전제 | replay·concurrent consume·expiry·lifecycle·binding mismatch에서 증거와 mutation call 0건; 증거 field allowlist 검사 |
| confirmed update와 새 review 경합 | confirm 직후 crash 뒤 prepare/revise가 새 pending update를 게시 | unexpired confirmed update publication block, exact consume resume, expiry/lifecycle fail-closed release | confirm 직후 fault injection과 concurrent prepare/revise에서 새 pending row·PATCH 0건 |
| refresh reservation 위조·재사용 | 다른 actor/create attempt reservation 또는 restart replay로 token exchange 반복 | U2 durable one-invocation claim, authenticated opaque envelope, U1 exact binding verification, one-exchange port | 모든 mismatch·tamper·replay·crash fixture의 허용 밖 exchange와 second exchange 0건 |
| revocable cleanup이 durable create state를 손상 | logout·switch·clear·expiry가 U2 ledger를 pending state와 함께 삭제하거나 다시 씀 | U1 namespace 한정 cleanup과 `ticket_tools_create_v1` preservation contract | 네 lifecycle fixture 전후 U2 ledger row와 key/bytes snapshot 동일성 검사 |
| history 잘못 결합 | 동시 chat에서 sequence가 엇갈림 | conversation lock, persisted-message correlation, atomic commit/readback | concurrent completion과 hash mismatch fixture |
| lifecycle cleanup과 Runner 경쟁 | switch·logout·clear·expiry 요청이 Runner의 SQLite history write 도중 history를 삭제하거나 Runner가 terminal commit 뒤 old-scope row를 다시 생성 | 네 event 모두 같은 conversation lock 유지, lock 뒤 actor scope 재검증, presentation-before-history cleanup, terminal commit, post-Runner old-scope 결과 폐기 | 네 lifecycle barrier에서 lock 대기, cleanup 순서, old-scope message·metadata 재생성 0건과 expiry zero-row terminal state를 검사 |
| 존재 여부 열거 | 404 문구 차이 또는 hidden count | one safe `not_found` semantics, no inferred data | absent/invisible 결과 동등성 검사 |
| retry amplification | gateway/tool/mapper가 각각 재시도 | TicketOperations 단일 policy owner, gateway one-attempt contract | 전체 operation request counter 2 이하 |
| 세션 만료 우회 또는 schema 회귀 | restart·token refresh로 deadline이 늘어나거나 migration이 기존 인증 field를 덮어씀 | persisted absolute expiry, additive column migration, pre-capability cleanup | 경계 시각·restart·legacy row와 기존 session 회귀 matrix |

## 저장·수명주기 요구사항

- 사용자 위임 credential은 기존 접근 제한된 ServerSession `itsm_token` field에만 저장하고 IdentitySession만 복원·원자 교체한다. 그 밖의 pending/cursor/presentation/history/create/update row에는 credential, Authorization, raw upstream cursor, raw ticket body, raw problem detail을 저장하지 않는다.
- `ServerSession.session_expires_at`은 기존 세션 row에 additive하게 저장하며 `created_at + 8시간`으로 한 번 정해진 뒤 활동·token refresh·restart로 바꾸지 않는다. 기존 인증·사용자·권한·위임 credential field는 그대로 보존한다.
- legacy session은 parse 가능한 기존 `created_at + 8시간`으로 backfill하고, `created_at`이 없거나 malformed면 이미 만료된 값으로 backfill해 다음 보호 요청에서 fail closed cleanup한다.
- pending mutation은 operation별 최신 하나만 유지한다. Create는 기존 pending/confirmed create를 원자적으로 교체할 수 있고, update revise는 정확한 expected pending row만 교체한다. Unexpired confirmed update는 새 prepare·revise를 차단하며 exact consume 재개, expiry 또는 lifecycle invalidation으로만 해소한다.
- `confirm`은 `pending → confirmed`, `consume_once`는 `confirmed → consumed`만 원자적으로 수행한다. 소비 증거는 `mutation_id`와 `confirmed_at`만 포함하고 같은 row에서 최대 한 번 반환되며, 반복·불일치 호출은 증거와 transport 권한 없이 거부된다.
- U1 lifecycle cleanup은 revocable pending/cursor/presentation/history/session state만 정리하고 U2의 `ticket_tools_create_v1` durable ledger row, idempotency key, canonical request bytes를 삭제하거나 다시 쓰지 않는다. consume 뒤 downstream binding 전에 crash가 나면 같은 U2 attempt를 보존하고 새 confirmation을 요구하며, 결합되지 않은 증거로 POST하지 않는다.
- cursor binding은 session expiry, user switch, conversation clear, logout, upstream invalid cursor 중 먼저 발생한 경계에서 idempotent하게 제거한다.
- presentation companion은 matching conversation history와 같은 수명만 가지며, user switch·logout·conversation clear에서 SDK history보다 먼저 지운다.
- 같은 conversation의 Runner와 user switch·logout·conversation clear·session-expiry cleanup은 동일한 application conversation lock을 사용한다. 각 event는 lock 획득 뒤 expected actor scope를 다시 읽고 presentation을 SDK history보다 먼저 지우며 terminal lifecycle commit까지 lock을 유지한다. Runner 뒤 actor 변경 또는 만료가 확인되면 어떤 response/presentation 결정이나 commit보다 먼저 old-scope 결과를 폐기한다.
- U2는 refresh reservation을 durable하게 단 한 번 invocation claim하고 authenticated opaque envelope로 actor/create-attempt binding을 제공한다. U1은 U2 storage에 접근하지 않고 이를 검증해 exchange 최대 1회와 기존 session credential atomic commit만 수행하며 failure·restart·crash 뒤 second exchange를 허용하지 않는다.
- storage와 history write가 실패하면 권한이나 성공을 추측하지 않는다. presentation 실패는 text-only fallback으로, confirmation·cursor 저장 실패는 해당 기능의 safe failure로 끝낸다.

## 보안 검증 게이트

U1 완료를 주장하려면 다음 조건을 모두 만족해야 한다.

1. FakeModel과 MockTransport만 사용하며 예상하지 않은 OpenAI·ITSM network call은 0건이다.
2. secret canary, service-token misuse, raw cursor/header/problem detail 노출은 모두 0건이다.
3. identity, visibility, prompt-injection, cursor binding, 분리된 confirm/consume_once와 confirmed-update publication block, one-time evidence, U2 ledger preservation, authenticated refresh reservation, retry ceiling, presentation correlation 공격 matrix가 모두 통과한다.
4. 기존 login, user switch, session, conversation history/clear, API response와 text fallback 회귀가 통과한다.
5. Runner history write와 user switch·logout·conversation clear·session expiry를 각각 barrier로 교차 실행한 테스트에서 terminal commit 뒤 old-scope SDK message/session과 presentation companion 재생성이 0건이다. Expiry에서는 pending/cursor/server-session row와 성공 response·presentation publication도 모두 0건이다.
6. U1에서 새로 만들거나 변경한 application code의 line coverage는 80% 이상이다.

## 범위 밖과 후속 소유권

- create idempotency ledger의 최대 1개 생성 보장은 U2가 완결한다. U1은 그 ledger를 lifecycle cleanup에서 보존하고, 정확히 한 번 소비된 최소 증거가 downstream 실행 전제를 대체하지 못하게 하는 공통 경계를 책임진다.
- PATCH `If-Match` 적용·충돌·불명확 결과 보장은 U3가 완결한다.
- 최종 정확히 세 tool, 전체 suite·coverage, README, 사용자 성과 측정은 U4가 검증한다.
- 새 WAF, KMS, secrets manager, network appliance, cloud IAM 또는 배포 인프라는 이 Unit에서 추가하지 않는다.
