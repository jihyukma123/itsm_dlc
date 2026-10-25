# U2 Ticket Write — 보안·신뢰성 설계

## Sources

- `construction/u2-ticket-write/nfr-requirements/security-requirements.md`
- `construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md`
- `construction/u2-ticket-write/functional-design/functional-spec.md`
- `construction/u2-ticket-write/functional-design/rules.md`
- `inception/contract-design/contract-summary.md`
- `construction/u1-ticket-read-skeleton/nfr-design/security-design.md`
- `construction/u2-ticket-write/nfr-design/nfr-design-questions.md`

## Scope and Posture

U2는 기존 FastAPI process에 포함되는 library Unit이다. 새 service, queue, cache, distributed lock, database를 추가하지 않고 U1이 소유한 server session, per-conversation lock, confirmation repository, `ItsmGatewayV1`, registry를 공개 port로만 사용한다. U2가 소유하는 durable authority는 기존 Server Session SQLite의 `ticket_tools_create_v1.ticket_create_attempts`다.

보호 대상은 현재 사용자의 delegated credential, 확인된 create intent, exact canonical request bytes, idempotency key, POST/reconciliation/refresh의 한번씩 소유권, authoritative ticket ID evidence이다. ITSM API v2가 권한·가시성을 판정하며, Assistant는 불명확한 결과를 성공으로 추측하지 않는다.

## Security and Reliability Decisions

| ID | 결정 | 강제 경계 | Fail-closed 결과 |
|---|---|---|---|
| SEC-U2-01 | `ticket_write` input은 strict V1 schema로 검증하고 catalog label·ITSM text는 구조화된 비신뢰 data로만 다룬다. | Tool adapter → create policy | invalid·ambiguous selector에서 ledger/pending/POST 0회 |
| SEC-U2-02 | Canonical UTF-8 bytes, SHA-256 hash, serialization version, CSPRNG key를 U1 pending 공개 전 `prepared` ledger에 먼저 commit한다. | Canonical serializer → create-attempt repository | ledger commit 실패 시 review/POST 0회 |
| SEC-U2-03 | U1 `consume_once` evidence는 동일 actor·payload attempt에 idempotent CAS로 결합하고 `retained_until`을 `confirmed_at + 24h` 이상으로 단조 증가시킨다. | U1 public confirmation port → U2 ledger | unbound·mismatched evidence에서 POST 0회 |
| SEC-U2-04 | 모든 POST 전에 send claim을 CAS로 선점한다. CAS는 `status`, evidence, refresh guard, `attempt_count < 2`를 비교하고 새 `claim_id`, `claim_deadline_at`, 증가한 count, `in_flight`를 한 transaction에 쓴다. | Create policy → repository → U1 gateway | CAS loser·active claim은 현재 state만 반환, POST 0회 |
| SEC-U2-05 | Send claim deadline은 `claim_started_at + ITSM_TIMEOUT_SECONDS + 1초`다. Gateway timeout은 `min(ITSM_TIMEOUT_SECONDS, remaining_claim_time - 1초)`로 제한하며 deadline 전 takeover를 금지한다. | Injected UTC/monotonic clock, repository CAS | 남은 시간이 없으면 network 호출 없이 ambiguous/safe failure |
| SEC-U2-06 | Transport outcome write는 `status=in_flight`와 exact send `claim_id`를 함께 비교한다. | Gateway result → repository | late sender의 update 0건, 최신 owner state 보존 |
| SEC-U2-07 | 현재 계약에는 authoritative result lookup이 없으므로 `begin_stale_claim_reconciliation`은 외부 I/O를 시작하지 않는다. 하나의 CAS가 expected state, 기존 send `claim_id`, 그리고 `in_flight`일 때 만료된 deadline을 비교하고 같은 transaction에서 `last_outcome.reconciliation_phase=lookup_unavailable_finalized`와 `retryable_after_reconcile`(attempt count < 2) 또는 terminal `ambiguous`(count = 2)를 기록한다. | Recovery coordinator → repository | active sender takeover 0회, 중간 `started` owner 0개, crash로 고착되는 reconciliation 0건 |
| SEC-U2-08 | Reconciliation finalization은 동일한 기존 send `claim_id`로 fence되고 POST를 수행하지 않는다. 향후 authoritative lookup을 추가하려면 먼저 C-01/C-04에 crash-safe ownership schema와 idempotent lookup contract를 추가하며, 현재 V1은 그 경로를 추측해 구현하지 않는다. | Recovery coordinator → repository | `ambiguous` 직접 POST 0회, stale write 0건, 새 recovery identity 0개 |
| SEC-U2-09 | 첫 POST 전 만료·만료 임박 또는 no-apply가 보장된 token-expired 401에서는 `refresh_state=unused` row만 CAS한다. 승자는 기존 server-secret primitive의 signer로 actor·attempt·generation·creator boot를 인증한 opaque `refresh_reservation_id`를 만들고, 이를 `refresh_used_at`, base credential generation, `refresh_state=reserved`와 함께 refresh 호출 전에 durable하게 쓴다. | Create policy → authenticated envelope codec → ledger → versioned U1 refresh port | live 경쟁 caller의 write·refresh 0회, create attempt당 refresh ≤1 |
| SEC-U2-10 | C-01의 정확한 `refresh_delegated_capability_once(TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline)`만 호출한다. U1은 envelope를 검증한 뒤 token exchange를 한 번만 수행하고 성공 credential을 기존 server-session identity store에 원자적으로 commit한 후에만 동일 actor binding의 더 큰 generation capability를 반환한다. 같은 process의 `reserved` observer는 관찰만 하고, 다른 process boot에서만 generation recovery를 한 번 수행한다. | C-01 `CredentialRefreshPortV1` → U2 refresh evidence → claim CAS | commit 전 crash는 fail closed, commit 후 response loss는 generation으로 복원, 두 번째 refresh 0회 |
| SEC-U2-11 | Refresh reservation을 이미 사용한 attempt의 counted POST가 다시 authoritative no-apply 401을 반환하면 기존 `record_definitive_outcome(expected in_flight, current claim_id)`과 one-shot guard로 terminal authentication failure를 기록한다. | Gateway result → existing repository operation | 추가 refresh·claim·POST 0회, 새 terminal transition API 0개 |
| SEC-U2-12 | Authoritative created/replayed response에 ticket ID가 있을 때만 `completed`와 success projection을 허용한다. | Gateway adapter result → completion mapper | missing/malformed evidence는 ambiguous 또는 safe failure |
| SEC-U2-13 | Credential, Authorization, key, canonical bytes, raw body/header/exception은 model, result, API, browser, log, metric, test diagnostics에 나가지 않는다. | Typed port·allowlist serializer·redaction | 원문 대신 allowlisted error code/message key만 반환 |

새 recovery identity, `claim_kind`, `claim_started_at`, refresh deadline field는 추가하지 않는다. C-04에 이미 선언된 `claim_id`, `claim_deadline_at`, `last_outcome`, `refresh_reservation_id`, `refresh_used_at`, `refresh_state`, credential-generation field만 사용하며 기존 required field의 의미를 바꾸지 않는다.

## Claim and Recovery State Design

| Operation | CAS predicate | Atomic writes | Network authority |
|---|---|---|---|
| Initial/second send claim | bound evidence, `status in {prepared, retryable_no_apply, retryable_after_reconcile}`, `attempt_count < 2`, refresh guard 충족 | new `claim_id`, deadline, `attempt_count += 1`, `status=in_flight` | 승자에게 exact bytes POST 1회 |
| Ambiguous reconciliation finalization | `status=ambiguous`, expected existing send `claim_id`, `last_outcome`이 아직 unreconciled | 같은 `claim_id`를 유지하고 `lookup_unavailable_finalized`와 retryable 또는 terminal state를 한 CAS로 기록 | 외부 I/O와 직접 POST 금지 |
| Stale-send reconciliation finalization | `status=in_flight`, `server_now >= claim_deadline_at`, expected existing send `claim_id` | 같은 `claim_id`, `lookup_unavailable_finalized`와 retryable 또는 terminal state를 한 CAS로 기록 | 외부 I/O와 새 recovery ID 금지 |
| Transport outcome | `status=in_flight`, exact send `claim_id` | completed/retryable_no_apply/ambiguous/terminal_failure 중 하나 | 추가 호출 권한 없음 |
| Reconciliation outcome | current V1에서는 별도 outcome write가 없음 | ownership과 final state가 위 단일 no-I/O CAS에서 함께 확정됨 | `retryable_after_reconcile` 후에만 별도 send claim 가능 |

Send claim deadline은 `claim_started_at`을 별도 저장하지 않고 CAS 시점의 server UTC `now + ITSM_TIMEOUT_SECONDS + 1초`로 계산한다. 권위 있는 result lookup operation이 없는 현재 계약에서는 `begin_stale_claim_reconciliation` 자체가 lookup-unavailable와 final state를 같은 transaction에 기록한다. 따라서 process가 어느 instruction 사이에서 중단되어도 durable `started` 상태가 남지 않으며, 전이는 POST를 수행하지 않는다.

### Authenticated Refresh Reservation Envelope

`refresh_reservation_id`는 V1 field를 늘리지 않는 `r1.<kid>.<payload_b64url>.<mac_b64url>` opaque 값이다. Payload는 compact canonical JSON으로 `create_attempt_id`, `user_binding`, `session_binding`, `conversation_binding`, `refresh_used_at`, `base_credential_generation`, `creator_boot_id`, `operation_deadline_utc`, 128-bit CSPRNG `nonce`를 고정 순서로 담는다. 세 actor binding 값은 원문 identifier가 아니라 동일 server key로 domain-separated HMAC한 값이다. MAC은 `HMAC-SHA256(key[kid], "ticket-tools-refresh-v1" || kid || payload_b64url)`이며 비교는 constant-time이다.

- Existing server-secret primitive가 raw key를 노출하지 않는 signer/verifier adapter를 제공한다. U2는 signer만, U1 `IdentitySession`은 verifier만 주입받는다. U1 provider는 outer `create_attempt_id`, `refresh_used_at`, `base_credential_generation`, current capability의 actor binding/generation, positive remaining deadline과 signed operation deadline을 모두 직접 비교하며 U2 repository를 읽지 않는다.
- `kid`는 기존 server key ring과 rotation policy를 따른다. Current signer key와 verification-only previous key는 create-attempt 최대 retention(최소 24시간) 동안 유지한다. 알 수 없거나 만료된 key, malformed payload, binding/deadline mismatch는 exchange와 session mutation 0건으로 fail closed한다.
- `creator_boot_id`는 application start마다 OS CSPRNG로 새로 만들고 memory에만 둔다. Reservation CAS가 commit되면 winner가 같은 boot의 process-local active-reservation registry에 ID를 등록하고 port 결과를 durable하게 기록한 뒤 제거한다. Registry는 refresh 권한이 아니라 관찰 정보다.
- `reserved` observer는 envelope MAC을 검증한다. `creator_boot_id == current_boot_id`이면 registry 포함 여부와 무관하게 live-process state로 보고 write·recovery·refresh를 모두 금지한다. 이는 commit과 registry 등록 사이 race 및 owner coroutine 중단도 fail closed한다.
- `creator_boot_id != current_boot_id`이고 current registry에 ID가 없을 때만 actual-restart recovery 후보가 된다. Repository의 immutable actor binding과 envelope claims를 다시 비교한 뒤, 같은 actor의 current session credential generation이 base보다 크면 `committed`, 아니면 `failed`와 terminal authentication failure를 exact reservation CAS로 한 번 기록한다. 어느 경우에도 refresh port를 다시 호출하지 않는다.

## Authentication, Authorization, and Confirmation

- Current user, session, conversation, delegated credential은 U1의 `TicketRequestCapability`에서만 온다. Model/tool argument가 주장하는 identity는 authority가 없다.
- Ticket POST는 delegated user token만 사용한다. Service token은 catalog 계약 이외의 ticket operation에 금지된다.
- Credential refresh는 C-01 `CredentialRefreshPortV1.refresh_delegated_capability_once(TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline)`로만 요청한다. U1 read-flow의 내부 `ReadCredentialRefreshPortV1.refresh_once`와는 다른 port다. Output은 raw token이 아닌 same-binding higher-generation capability 또는 `SafeErrorV1`이다.
- `CurrentTurnEvidenceV1`의 exact `확인`/`confirm`만 U1 `confirm`/`consume_once`를 진행한다. Quoted, embedded, historical, model-generated text는 실행 권한이 아니다.
- Pending reference, create-attempt ID, idempotency key possession은 권한이 아니다. Actor binding, payload hash, U1 consume evidence, U2 evidence binding, send claim이 모두 필요하다.
- Consume 후 evidence bind 전 crash에서는 기존 attempt/key/bytes를 유지한 새 review와 새 explicit confirmation을 요구한다.

## Data Protection and Secret Containment

| Boundary | Allowed | Forbidden | Verification |
|---|---|---|---|
| Model/tool schema | validated business fields, non-authority pending ref | credential, key, canonical bytes, claim IDs | schema snapshot, FakeModel capture |
| Ledger | actor binding, hashes, exact bytes, key, claims, safe outcome | credential, Authorization, raw problem detail | direct SQLite row assertion |
| Gateway | one request의 delegated Authorization, exact bytes/key | repository state, retry/refresh policy | MockTransport request capture |
| Tool/API/presentation | allowlisted review/result/error, escaped text | raw header/body/exception, key/bytes | response snapshot and canary scan |
| Logs/test diagnostics | operation, safe code, opaque request ID, counts | secret-bearing repr/assert diff | captured output canary scan |

At-rest encryption은 기존 Server Session SQLite와 배포 파일 보호를 상속한다. U2는 credential을 ledger에 복사하지 않고 confirmed row를 최소 24시간 보존한다. Unconfirmed orphan은 `created_at + 24h` 전에 삭제하지 않으며 언제나 실행 권한이 없다.

## Failure and Degradation Design

| Failure | Durable result | Automatic action | User-visible outcome |
|---|---|---|---|
| Validation/catalog mismatch | no ledger/pending | none | input correction |
| Pending publish after ledger commit fails | orphan `prepared` | cleanup after retention | safe unavailable; POST 0 |
| Confirmation/revise race | one expected-state CAS winner | loser observes current state | new review 또는 confirmed path 중 하나 |
| Timeout/connection loss/5xx uncertainty | `ambiguous` under existing send claim | same-claim reconciliation ownership, then optional remaining-budget state | result unknown; never success |
| Active claim observed | state unchanged | wait/return current state | processing/unknown text |
| No-apply token-expired 401 | `retryable_no_apply` | durable refresh reservation once, then optional send claim | final result or login required |
| Live refresh reservation 경쟁 | `reserved` 유지 | loser는 관찰만, write·refresh 0 | 처리 중 또는 현재 safe state |
| Refresh reservation owner crash | reservation remains used | 실제 restart에서 generation 비교 1회, refresh retry 0 | higher generation이면 commit 복원, 아니면 authentication failure |
| Refresh 사용 뒤 두 번째 no-apply 401 | current send claim으로 terminal outcome 기록 | refresh·claim·POST 0 | authentication required |
| 429 | safe non-success outcome | sleep 0, retry 0 | validated retry guidance only |
| Missing ticket ID in success-like response | ambiguous/terminal safe failure | only reconciliation within budget | never success |
| Second ambiguous POST outcome | terminal `ambiguous` | third POST 0 | result remains unknown |

Global circuit breaker, background retry, queue, stale result cache는 사용자 간 failure state를 공유하고 추가 운영 의존성을 만들기 때문에 추가하지 않는다.

## Deterministic Verification Design

| Control | Test seam | Pass condition |
|---|---|---|
| Ledger-first ordering | repository failure injection between ledger and pending writes | pending without matching ledger 0건 |
| Review replacement | barriers at prior-row terminalize, pending invalidate, evidence bind | executable prior rows 0건, race winner 1개 |
| Send claims | fake UTC/monotonic clock, concurrent CAS, transport counter | active owner 1개, deadline-before takeover 0, uncounted POST 0 |
| Reconciliation finalization | ambiguous/stale-send existing-claim CAS matrix, crash-before/after-CAS barrier, late result barrier | no-I/O CAS winner 1개, durable `started` 0개, 새 recovery identity 0개, stale write 0 |
| Refresh reservation and provider port | shared C-01 fixture, actor/attempt/time/generation/deadline tamper matrix, commit-before-registry barrier, same-boot missing-registry case, different-boot restart snapshot, provider exchange/commit probes | consumer invocation ≤1, live observer write 0, mismatch exchange 0, provider exchange ≤1, second refresh 0 |
| Refresh-used second 401 | proactive-refresh/401-refresh 후 두 번째 no-apply 401, late old-claim barrier | terminal authentication failure 1건, 추가 refresh·claim·POST 0 |
| Bytes and budget | MockTransport exact-body/key capture | body/key identical, POST ≤2, third POST 0 |
| Success evidence | created/replayed/malformed/response-loss matrix | ticket ID evidence 없는 success 0 |
| Secret containment | unique canary per secret class across every boundary | exposure 0 |
| Regression/coverage | FakeModel, network deny, coverage 7.17.0 | 전체 suite 100%, real network 0, changed app line coverage ≥80% |
| Accessibility | text snapshots for review/success/error/ambiguous states | color·icon·position-only state 0 |

## NFR Allocation

| NFR | Primary design |
|---|---|
| NFR1.1–NFR1.3 | SEC-U2-01, SEC-U2-13, typed allowlist and canary boundaries |
| NFR2.1–NFR2.3 | delegated capability, exact current-turn confirmation, SEC-U2-03 |
| NFR3.1–NFR3.3 | ledger-first/public-port-only prepare, evidence binding, replacement CAS |
| NFR3.4–NFR3.8 | SEC-U2-04–SEC-U2-08, byte identity, success evidence, retention |
| NFR3.9 | SEC-U2-09–SEC-U2-10 durable one-shot refresh reservation |
| NFR3.10 | SEC-U2-11 existing send-claim fence plus one-shot refresh guard |
| NFR5.1 | existing Agent/Runner/session/UI compatibility and full regression |
| NFR6.1–NFR6.2 | deterministic verification harness, network deny, changed-code coverage |
| NFR7.1–NFR7.2 | quantified deadlines, global two-POST budget, no 429 retry, ambiguity preservation |
| NFR8.1 | U4-consumable three-trial measurement evidence schema |
| NFR9.1 | text-first create presentation mapper and fallback |

## Residual Risks and Handoff

- 현재 per-conversation lock과 SQLite CAS 조합은 single-process 배포를 전제로 한다. Multi-process로 변경하면 shared lock 또는 database transaction arbitration을 재설계해야 한다.
- ITSM 계약에 create-result lookup operation이 추가되기 전에는 reconciliation이 동일한 기존 send `claim_id` 아래 lookup-unavailable를 안전하게 기록한 뒤, budget이 남은 경우에만 same-key/same-bytes 최종 시도를 허용한다.
- Refresh reservation 이후 credential commit 전 crash는 실제 restart에서 generation이 증가하지 않았음을 확인한 뒤 자동 회복보다 중복 refresh 방지를 우선해 authentication failure로 닫는다.
- Functional Design의 `begin_stale_claim_reconciliation` signature와 already-used refresh 뒤 두 번째 401의 내부 state 표현은 Code Generation 전에 이 문서의 기존-field-only semantics와 일치하도록 확인해야 한다. 새 repository operation, recovery identity 또는 renewed execution authority로 우회하면 안 된다.
- Infrastructure Design은 새 배포 component 없이 기존 SQLite migration/permission/TLS/single-process assumption과 deterministic test seam만 유지해야 한다.

## Outcome

U2는 confirmation, send, reconciliation, refresh를 서로 다른 durable 전제조건으로 분리하되 reconciliation은 기존 send `claim_id`를 그대로 보존한다. Refresh는 live 경쟁 caller가 owner를 방해하지 않고 실제 restart에서만 generation evidence로 복구한다. 각 외부 효과는 한 번만 시작되며, 늦은 결과나 restart가 최신 state를 덮어쓰지 못하고, 권위 있는 ticket ID 증거 없이는 성공이 될 수 없다.
