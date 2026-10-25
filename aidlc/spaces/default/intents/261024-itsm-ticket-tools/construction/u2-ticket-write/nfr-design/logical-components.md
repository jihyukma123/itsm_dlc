# U2 Ticket Write — Logical Components

## Sources

- `construction/u2-ticket-write/nfr-design/security-design.md`
- `construction/u2-ticket-write/nfr-requirements/security-requirements.md`
- `construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md`
- `construction/u2-ticket-write/functional-design/functional-spec.md`
- `inception/contract-design/contract-summary.md`
- `inception/domain-design/components.md`

## Architectural Context

U2는 기존 modular FastAPI application 안의 library Unit이며 U1 runtime을 확장한다. 아래 구성요소는 deployable service 목록이 아니라 책임, dependency direction, transaction boundary, failure domain을 구분하는 논리 설계다.

## Logical Component Inventory

| ID | Component | Responsibility | Allowed dependencies | Forbidden dependencies | Failure behavior |
|---|---|---|---|---|---|
| LC-U2-01 | Ticket Write Tool Adapter | strict action/draft schema, current-turn evidence forwarding, safe result | LC-U2-02, LC-U2-09, U1 registry/context | credential, raw HTTP, direct repository mutation | safe validation/result only |
| LC-U2-02 | Create Operation Policy | prepare/revise/confirm/send/reconcile/refresh orchestration and total budget | LC-U2-03–08, U1 public ports, clock/random ports | raw SQLite/httpx, hidden retry, UI rendering | unknown state remains non-success |
| LC-U2-03 | Catalog Resolver and Canonical Serializer | active exact catalog resolution, normalized payload, exact V1 bytes/hash | U1 catalog gateway methods, clock | ticket POST, pending repository, credential | invalid input yields zero durable publication |
| LC-U2-04 | Create Attempt Repository | `ticket_tools_create_v1` migration, ledger-first insert, evidence/send-claim/reconciliation/refresh/outcome/retention CAS | existing Server Session SQLite only | U1 migration namespaces, network, credential, 새 recovery identity | transaction rollback and current durable state |
| LC-U2-05 | Confirmation Bridge | U1 public put/get/confirm/consume_once/invalidate usage and evidence transfer | U1 `PendingMutationRepositoryV1`, LC-U2-04 | U1 internals, cross-owner transaction API | no evidence/claim on mismatch or crash |
| LC-U2-06 | Send Claim Executor | exact send claim verification, delegated capability handoff, one gateway call | LC-U2-04, U1 `ItsmGatewayV1` | retry, refresh, sleep, presentation | typed one-attempt outcome only |
| LC-U2-07 | Reconciliation Coordinator | 기존 send `claim_id`를 보존한 stale/ambiguous no-I/O finalization CAS와 retryable transition | LC-U2-04 | 새 recovery ID, 현재 V1에 없는 result lookup, direct ambiguous POST, live-claim takeover | 중간 owner state 없이 retryable 또는 terminal로 원자 확정 |
| LC-U2-08 | Refresh Reservation Coordinator | authenticated durable one-shot reservation, live-observer no-op, boot-bound restart generation recovery, remaining-budget handoff | LC-U2-04, existing server-secret signer/verifier adapter, C-01 `CredentialRefreshPortV1` | raw token/key, independent retry, second reservation, refresh deadline field | fail closed after used reservation |
| LC-U2-09 | Create Result and Presentation Mapper | typed safe result, text-first review/success/error/ambiguous presentation | typed outputs from LC-U2-02, U1 mapper registry | raw gateway/ledger secret fields, HTML trust | existing text fallback |
| LC-U2-10 | Deterministic Verification Harness | FakeModel, MockTransport, fake clocks/randomness, barriers, row/counter/canary evidence | public ports and test-only seams | real OpenAI/ITSM network | unexpected call/leak fails test |

## Dependency Direction

```text
U1 Agent/Runner/Registry
  -> LC-U2-01 Tool Adapter
      -> LC-U2-02 Create Operation Policy
          -> LC-U2-03 Catalog Resolver and Canonical Serializer
          -> LC-U2-05 Confirmation Bridge -> U1 PendingMutationRepositoryV1
          -> LC-U2-04 Create Attempt Repository -> existing Server Session SQLite
          -> LC-U2-06 Send Claim Executor -> U1 ItsmGatewayV1 -> ITSM API v2
          -> LC-U2-07 Reconciliation Coordinator -> LC-U2-04
          -> LC-U2-08 Refresh Reservation Coordinator -> U1 credential refresh port
      -> LC-U2-09 Create Result and Presentation Mapper
```

Dependency는 위에서 아래로만 향한다. Repository, gateway, refresh port, mapper는 operation policy를 역호출하지 않는다. LC-U2-02만 retry·recovery·refresh 정책을 소유하며 gateway 호출 하나는 HTTP attempt 하나와 동일하다.

## Component Contracts

### LC-U2-01 Ticket Write Tool Adapter

- `TicketWriteToolInputV1`의 `prepare`, `confirm`, `revise`, `cancel`만 받고 unknown field를 거부한다.
- `confirm`/`cancel`의 권한은 argument가 아니라 U1 runtime이 제공한 `CurrentTurnEvidenceV1`에서만 온다.
- Output은 `TicketMutationToolResultV1`으로 제한하고 server-only field를 schema에 두지 않는다.

### LC-U2-02 Create Operation Policy

- 하나의 create operation에 대한 global `attempt_count`, refresh budget 1, key/bytes identity를 소유한다.
- Network 전 durable prerequisite의 순서는 ledger insert → pending publish → consume evidence bind → send claim이다.
- Transport result와 reconciliation result는 각각 expected state와 동일한 기존 send `claim_id`로 기록한다.
- `attempt_count == 2`이면 어떤 state에서도 추가 POST를 시작하지 않는다.

### LC-U2-03 Catalog Resolver and Canonical Serializer

- ID 또는 normalized name이 active match 하나를 가리킬 때만 service/component/model을 해석한다.
- Explicit `now`는 prepare/revise에서 injected UTC clock을 한 번만 capture한다.
- Fixed field order, compact UTF-8 JSON, omitted absent optional, version 1을 사용하고 exact bytes hash를 함께 반환한다.

### LC-U2-04 Create Attempt Repository

- U2-owned namespace만 migration하고 U1 `ticket_tools_state_v1`/`ticket_tools_history_v1`을 수정하지 않는다.
- Required C-04 field와 existing optional `last_outcome`, `refresh_reservation_id`, `refresh_used_at`, `refresh_state`, credential-generation evidence를 보존한다. `claim_kind`, `claim_started_at`, recovery ID, refresh deadline field는 추가하지 않는다.
- 모든 state mutation은 expected status, expected claim/reservation identity, affected-row count를 가진 explicit CAS method다.
- 현재 V1의 `begin_stale_claim_reconciliation`은 expected state·기존 send `claim_id`·필요 시 만료된 deadline을 비교하고 `lookup_unavailable_finalized`와 retryable/terminal state를 한 no-I/O CAS로 기록한다. 새 recovery identity나 중간 `started` phase를 쓰지 않는다.
- Confirmed row의 retention은 `max(existing, confirmed_at + 24h)`, unconfirmed row는 `created_at + 24h` 이상을 유지한다.

### LC-U2-05 Confirmation Bridge

- U1 public `put`, `get`, `confirm`, `consume_once`, `invalidate`만 사용한다.
- Review replace는 old evidence-free ledger terminalize → old pending invalidate → new ledger insert → new pending publish 순서다.
- Consumed evidence를 재구성하지 않고 crash-before-bind에서는 새 confirmation을 요구한다.

### LC-U2-06 Send Claim Executor

- Entry에서 repository의 exact send claim, stored bytes hash/version, key binding, remaining deadline을 재검증한다.
- U1 gateway에 delegated capability, exact stored bytes, original key, bounded timeout을 전달해 한 번만 호출한다.
- Gateway return 후 LC-U2-04의 send-claim-fenced outcome method만 호출한다.

### LC-U2-07 Reconciliation Coordinator

- `ambiguous` 또는 deadline이 지난 `in_flight`에서 expected state와 기존 send `claim_id`를 비교하는 CAS 하나만 실행한다. `in_flight`에서는 deadline 만료도 필수 전제다.
- 현재 계약에는 authoritative result lookup이 없으므로 CAS는 외부 I/O 전에 같은 transaction에서 `lookup_unavailable_finalized`와 `retryable_after_reconcile`(attempt count < 2) 또는 terminal `ambiguous`를 기록한다. Durable `started` 상태, 새 claim field, recovery ID, recovery deadline은 없다.
- CAS 전 crash는 원래 state를 남겨 다른 caller가 안전하게 재시도하고, CAS 후 crash는 이미 final state를 남긴다. 따라서 crash-after-start barrier에서도 고착 또는 중복 lookup이 없다.
- 향후 result lookup은 C-01/C-04에 명시적 idempotent operation과 crash-safe owner schema가 승인되기 전에는 추가하지 않는다. Coordinator는 직접 POST하지 않는다.

### LC-U2-08 Refresh Reservation Coordinator

- Bound evidence가 있는 `prepared` 또는 `retryable_no_apply`, budget remaining, `refresh_state=unused`를 전제로 unique reservation ID, `refresh_used_at`, base credential generation, `reserved`를 호출 전 commit한다.
- Reservation ID는 `r1.<kid>.<canonical-payload>.<HMAC-SHA256>` opaque envelope다. Payload에는 attempt, domain-separated actor binding hashes, used-at, base generation, creator boot ID, signed operation deadline, nonce가 들어간다. U2 signer와 U1 verifier는 raw key를 노출하지 않는 existing server-secret primitive를 사용하며 previous verification key를 attempt retention 동안 유지한다.
- Winner만 C-01의 정확한 `CredentialRefreshPortV1.refresh_delegated_capability_once(TicketRequestCapability, CredentialRefreshReservationV1, remaining_deadline)`를 호출한다. U1은 outer fields, capability actor/generation, signed deadline과 MAC을 직접 검증하고 U2 repository를 역호출하지 않는다. 이 port는 U1 read용 `ReadCredentialRefreshPortV1.refresh_once`와 별개다.
- Process startup마다 CSPRNG `boot_id`와 빈 active-reservation registry를 만든다. CAS commit winner는 port 호출 전에 registry에 등록한다. 같은 boot의 `reserved` observer는 registry membership과 무관하게 write·recovery·refresh 0회다. 다른 boot이고 registry에도 없을 때만 repository actor/envelope binding을 재검증하고 same-actor session generation으로 `committed` 또는 `failed`를 exact-reservation CAS한다.
- Reservation은 reset되지 않으며 refresh 실패·crash·restart도 두 번째 호출을 허용하지 않는다. 이미 refresh를 사용한 뒤 다시 authoritative no-apply 401이면 기존 send-claim-fenced `record_definitive_outcome`으로 terminal authentication failure를 기록하고 추가 claim·POST를 금지한다.
- U1 provider test와 U2 consumer test는 동일한 C-01 fixture와 exact operation signature를 사용한다. Actor/attempt/used-at/generation/deadline/MAC mismatch, commit-before-registry race, same-boot registry miss, different-boot recovery를 함께 검증한다.

### LC-U2-09 Create Result and Presentation Mapper

- Created 또는 idempotent-replayed ticket ID evidence만 success로 mapping한다.
- Review, input correction, auth, rate limit, ambiguity, unavailable state에 항상 plain-text equivalent와 다음 행동을 제공한다.
- External text는 text node와 동등하게 취급하고 kind/action/label은 server allowlist만 선택한다.

## Runtime Sequences

### Prepare or Revise

1. LC-U2-01이 draft/action을 검증한다.
2. LC-U2-03이 catalog, time, defaults, exact bytes/hashes를 확정한다.
3. Revise면 LC-U2-02가 LC-U2-04에서 old evidence-free row를 terminalize하고 LC-U2-05로 pending을 invalidate한다.
4. LC-U2-04가 new `prepared` attempt/key/bytes를 commit한다.
5. LC-U2-05가 matching U1 pending review를 publish한다.
6. LC-U2-09가 complete text-first review를 만든다. POST는 0회다.

### Confirm and Send

1. LC-U2-05가 exact current-turn decision과 actor/payload binding으로 U1 evidence를 consume한다.
2. LC-U2-04가 evidence를 bind하고 retention을 연장한다.
3. LC-U2-02가 send claim을 CAS하고 count를 증가시킨다.
4. LC-U2-06의 CAS winner만 gateway를 한 번 호출한다.
5. Outcome은 exact send claim으로만 기록되고 LC-U2-09가 safe result를 mapping한다.

### Reconcile, Refresh, and Retry

1. LC-U2-07이 ambiguous 또는 stale send state에서 기존 send `claim_id`를 보존한 no-I/O reconciliation finalization CAS를 수행한다.
2. 현재 lookup-unavailable 계약에서는 budget이 남으면 `retryable_after_reconcile`, 소진되면 terminal `ambiguous`가 같은 CAS로 확정된다.
3. 첫 POST 전 만료·만료 임박 또는 no-apply 401은 LC-U2-08이 refresh reservation을 먼저 소비한 뒤 U1에 refresh를 한 번 요청한다. Live loser는 관찰만 하고 restart recovery만 generation을 비교한다.
4. 두 retryable state의 다음 POST는 LC-U2-02의 새 send claim을 다시 이겨야 한다.
5. Count 2 또는 second ambiguous result은 terminal이며 third POST는 없다.

## Shared Resources and Isolation

| Resource | Owner/consumer | Isolation | Capacity stance |
|---|---|---|---|
| Server Session SQLite | existing owner; LC-U2-04 consumer | U2-only namespace, short transactions, expected-state CAS | existing single-process deployment |
| U1 pending repository | U1 owner; LC-U2-05 public-port consumer | actor/payload binding and one-time evidence | no direct table access |
| Application-lifetime AsyncClient | U1 gateway owner; LC-U2-06 caller | one gateway call = one attempt, bounded timeout | existing pool unchanged |
| Delegated credential store | U1 identity owner; LC-U2-08 caller | opaque refresh port and durable reservation | raw value never crosses port |
| Conversation lock | U1 lifecycle owner | serializes one-process Runner path | SQLite CAS remains restart authority |
| Registry/presentation envelope | U1 owner; U2 plugin/mapper contributor | immutable V1 registration and allowlists | no new endpoint/UI runtime |

SQLite transaction은 ledger/pending 상태 변경만 포함하고 ITSM/OpenAI network wait를 포함하지 않는다.

## Failure Domains and Blast Radius

| Domain | Example | Blast radius | Containment |
|---|---|---|---|
| Validation/catalog | invalid selector or malicious label | one draft | zero publication/POST, safe correction |
| Ledger/pending split | crash between commits | one attempt/review | orphan has no authority; idempotent cleanup |
| Confirmation/revise race | stale review confirmation | one actor-scoped create | conflicting CAS; one winner |
| Send claim | crash/late response | one create attempt | deadline and exact send-claim fence |
| Reconciliation | competing restart callers or crash at finalization | one ambiguous attempt | same-claim no-I/O finalization CAS; no intermediate owner, recovery identity or direct POST |
| Credential refresh | live competition, commit/registry race, or process crash after reservation | one create attempt | authenticated boot-bound envelope, same-boot observer no-op, different-boot generation recovery, refresh at most once |
| ITSM transport | timeout/malformed/5xx | one create attempt | durable ambiguity, total POST ≤2 |
| Presentation | mapper/history metadata failure | one assistant message | existing text fallback |
| Test harness | real network or canary leak | current test run | immediate sanitized failure |

## Infrastructure Handoff

U2는 새 deployable component를 요구하지 않는다. Infrastructure Design은 다음만 보존한다.

- Existing FastAPI process, application-lifetime httpx client, Server Session SQLite.
- U2-owned `ticket_tools_create_v1` additive migration과 기존 file permission/backup behavior; 새 recovery identity·refresh deadline field는 없음.
- Existing server-secret signer/verifier adapter와 key ring을 재사용한다. `kid` verification key는 create-attempt retention 이상 유지하고 application boot마다 ephemeral CSPRNG boot ID를 생성한다. 새 external secret store나 service는 없다.
- ITSM HTTPS certificate validation과 `ITSM_TIMEOUT_SECONDS`.
- Single-process per-conversation lock assumption; cross-restart authority는 SQLite CAS.
- FakeModel, MockTransport, fake clock/randomness, concurrent barrier, network-deny test seams.
- 새 service, queue, cache, distributed lock, dynamic registry가 없음.

## NFR Coverage Summary

| NFR | Logical allocation |
|---|---|
| NFR1.1–NFR1.3 | LC-U2-01, LC-U2-03, LC-U2-06, LC-U2-09, LC-U2-10 |
| NFR2.1–NFR2.3 | LC-U2-01, LC-U2-05, LC-U2-06 |
| NFR3.1–NFR3.3 | LC-U2-02, LC-U2-04, LC-U2-05 |
| NFR3.4–NFR3.8 | LC-U2-02, LC-U2-04, LC-U2-06, LC-U2-07 |
| NFR3.9 | LC-U2-08 and LC-U2-04 |
| NFR3.10 | LC-U2-02, LC-U2-04, LC-U2-08 |
| NFR5.1 | all components remain embedded and contract-compatible |
| NFR6.1–NFR6.2 | LC-U2-10 |
| NFR7.1–NFR7.2 | LC-U2-02, LC-U2-06, LC-U2-07, LC-U2-08 |
| NFR8.1 | LC-U2-10 measurement evidence consumed by U4 |
| NFR9.1 | LC-U2-09 |

## Outcome

Authority is narrow and acyclic: U1 owns identity, confirmation ports, gateway and registry; U2 owns create policy and ledger; ITSM owns authorization and visibility. Reconciliation은 send claim identity를 보존하고 refresh recovery는 실제 restart의 generation evidence에만 의존한다. 각 failure는 하나의 draft, attempt, message 또는 test run으로 격리되며 권한 확대, 성공 추측, 예산 초과로 전파되지 않는다.
