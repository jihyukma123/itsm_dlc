# U1 Ticket Read Skeleton — Logical Components

## Sources

- `construction/u1-ticket-read-skeleton/nfr-design/security-design.md`
- `construction/u1-ticket-read-skeleton/nfr-requirements/security-requirements.md`
- `construction/u1-ticket-read-skeleton/nfr-requirements/tech-stack-decisions.md`
- `construction/u1-ticket-read-skeleton/functional-design/functional-spec.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`

## Architectural Context

U1은 기존 단일 FastAPI 애플리케이션에 포함되는 library Unit이며 별도 runtime 또는 network service가 아니다. 논리 컴포넌트는 기존 `ApplicationLifecycle`, `IdentitySession`, `AgentConversation`, `TicketOperations`, `ItsmGateway`, `ConversationPresentation` 경계를 구체화한다. 이 목록은 구현 파일 구조가 아니라 책임, dependency direction, failure domain과 shared resource ownership을 정의한다.

## Logical Component Inventory

| ID | Logical component | Responsibility | Allowed dependencies | Forbidden dependencies | Failure behavior |
|---|---|---|---|---|---|
| LC-U1-01 | ApplicationLifecycle Coordinator | injected conversation-serialization port로 lock을 획득하고 chat, Runner/history/presentation, session-expiry cleanup, user switch, logout, conversation clear의 순서·commit 경계를 조정 | LC-U1-02, LC-U1-05, LC-U1-06, LC-U1-08, LC-U1-09, LC-U1-12 | model-derived identity, direct HTTP client, lock 밖 SDK history deletion, U2 `ticket_tools_create_v1` ledger mutation | cleanup 또는 capability 생성 실패 시 새 context를 활성화하지 않으며 stale/expired Runner 결과를 폐기함 |
| LC-U1-02 | Identity Capability Provider | 기존 server session schema 보존, additive absolute-expiry migration, lock-held context 아래 persisted-expiry 재검증, delegated credential capability, 내부 read refresh와 U2 `CredentialRefreshPortV1` 구현 | 기존 server session repository와 migration helper, existing token-exchange adapter, LC-U1-12 context contract, LC-U1-13 reservation verifier | LC-U1-01 coordinator 호출, retry/deadline 정책 결정, U2 table 접근, 기존 session field 제거·rename·재해석, Agent/tool schema·browser·serializer에 credential 제공, history 직접 삭제 | migration·expiry·reservation·refresh 실패 시 typed authentication failure; capability·Runner·ITSM을 fail closed |
| LC-U1-03 | Ticket Operations Policy | input canonicalization, read deadline·attempt·single-refresh budget, projection, safe error, state orchestration | LC-U1-02의 `CredentialRefreshPortV1`, LC-U1-04, LC-U1-05, LC-U1-06, clock/sleeper port | raw httpx, browser presentation, independent retry/refresh decision in callers or gateway | success evidence 없으면 failed; 추가 시도·refresh 금지 |
| LC-U1-04 | ITSM Gateway Adapter | application-lifetime AsyncClient로 한 번의 typed HTTP attempt를 수행하고 ordinary-detail과 read-for-update 목적 profile을 구분 | 기존 httpx AsyncClient, ITSM API v2 | repositories, Agent, mapper, retry/sleep/refresh decision | raw response를 경계 밖으로 내보내지 않고 typed failure; read-for-update invalid ETag는 safe failure |
| LC-U1-05 | Cursor Repository | CSPRNG continuation 발급, exact binding, once-only resolve와 lifecycle invalidation | 기존 Server Session SQLite의 `ticket_tools_state_v1` | model-visible upstream cursor, credential | mismatch·tamper·expiry에서 outbound 없이 invalid continuation |
| LC-U1-06 | Confirmation Repository | create/update pending variant, per-operation replacement, expiry, exact binding, 분리된 atomic `confirm`/`consume_once`, one-time minimal evidence | 기존 Server Session SQLite의 U1-owned `ticket_tools_state_v1` | POST/PATCH transport, credential, U2/U3 migration 또는 `ticket_tools_create_v1` row/key/bytes 수정 | 저장·binding·CAS 실패 또는 repeat consume 시 evidence와 mutation authority를 만들지 않음 |
| LC-U1-07 | Tool and Mapper Registry | `ticket_read` plugin 등록, downstream plugin composition, duplicate/version collision 차단 | LC-U1-03, typed tool and mapper contracts | credential, raw gateway result, dynamic external registry keys | duplicate/unknown contract를 composition time에 fail closed |
| LC-U1-08 | Agent Conversation and Presentation Committer | coordinator가 전달한 opaque lock-held context 아래 existing Runner 실행과 SDK history 접근, post-Runner expiry 검사 이후 persisted assistant correlation, mapper 호출, companion commit/readback | LC-U1-02, LC-U1-07, LC-U1-09, LC-U1-12의 context contract, existing SQLiteSession | LC-U1-01 coordinator 호출, lock 획득·해제, raw credential, uncorrelated sequence prediction, expiry 재검사 전 response/presentation 처리 | 유효 session의 presentation 실패는 existing assistant text로 degrade하고, post-Runner expiry는 전체 Runner 결과를 폐기함 |
| LC-U1-09 | Presentation History Repository | canonical `TicketPresentationV1` companion 저장·복원, history-load/startup orphan cleanup | existing Agents SDK history SQLite의 `ticket_tools_history_v1` | raw tool trace, upstream body, credential | invalid/missing/orphan metadata를 응답에서 제외하고 text fallback; cleanup 실패는 다음 실행에서 재시도 |
| LC-U1-10 | Browser Presentation Adapter | optional V1 metadata 검증과 accessible text-node rendering | existing chat response/history API | `innerHTML` trust, payload-defined DOM/ARIA semantics | unknown metadata를 무시하고 existing reply 렌더링 |
| LC-U1-11 | Deterministic Verification Harness | FakeModel, MockTransport, fake clock/sleeper, secret scan, coverage evidence | public ports와 test-only seams | real OpenAI/ITSM network | 예상 밖 network 또는 canary 발견 즉시 test failure |
| LC-U1-12 | Conversation Serialization Port | existing per-conversation lock provider를 감싸고 acquisition 결과를 opaque `LockHeldRequestContextV1`으로 표현 | existing application lock provider only | identity, Runner, history, HTTP, repository policy | acquisition 실패 시 context를 만들지 않고 호출자에게 typed lifecycle failure |
| LC-U1-13 | Refresh Reservation Verifier | server secret으로 U2의 opaque reservation envelope authenticity와 create-attempt·user·session·conversation binding을 검증 | existing server-secret verification primitive only | U2 `ticket_tools_create_v1` read/write, token exchange, retry policy, raw reservation payload 노출 | tamper·binding mismatch·malformed envelope를 exchange 전에 typed authentication failure로 거부 |

## Dependency Direction

```text
Browser Presentation Adapter
  -> ApplicationLifecycle Coordinator
      -> Conversation Serialization Port -> existing conversation lock provider
      -> Identity Capability Provider -> existing session repository/token exchange
          -> Refresh Reservation Verifier -> existing server-secret verification primitive
      -> Cursor Repository -> Server Session SQLite
      -> Confirmation Repository -> Server Session SQLite
      -> Agent Conversation and Presentation Committer
          -> Conversation Serialization Port contract
          -> Identity Capability Provider
          -> Tool and Mapper Registry
              -> Ticket Operations Policy
                  -> Identity Capability Provider.ReadCredentialRefreshPortV1
                  -> ITSM Gateway Adapter -> ITSM API v2
                  -> Cursor Repository -> Server Session SQLite
                  -> Confirmation Repository -> Server Session SQLite
          -> Presentation History Repository -> Agents SDK History SQLite
      -> Presentation History Repository
```

The direction is one-way. LC-U1-01 acquires LC-U1-12 once and passes `LockHeldRequestContextV1` downward; LC-U1-02와 LC-U1-08은 coordinator를 호출하거나 lock을 획득·해제하지 않는다. LC-U1-01은 LC-U1-05/06 invalidation ports를 직접 호출하지만 repositories는 coordinator·policy·transport를 역호출하지 않는다. LC-U1-03은 LC-U1-02의 internal read refresh port만 호출하고 LC-U1-02는 policy를 호출하지 않는다. U2는 durable claim 뒤 public create refresh port를 호출하며 LC-U1-02는 LC-U1-13을 통해 envelope만 검증하고 U2 storage에는 접근하지 않는다. `ItsmGateway`는 `TicketOperations`를 호출하거나 자체 retry할 수 없다.

## Component Contracts

### LC-U1-01 ApplicationLifecycle Coordinator

- **Input:** authenticated FastAPI request, lifecycle command, existing conversation identifier.
- **Output:** request capability and chat result, or an existing safe application error.
- **Atomicity boundary:** user switch/logout/clear/expiry 모두 같은 lock에서 expected actor scope 재검증 후 presentation-before-history cleanup, LC-U1-06/05 invalidation, terminal lifecycle commit을 수행한다. New identity commit or session deletion is last.
- **Concurrency boundary:** LC-U1-12에 opaque conversation scope를 전달해 lock을 얻고 `LockHeldRequestContextV1`을 LC-U1-02와 LC-U1-08에 명시적으로 전달한다. Runner 직전/직후 persisted expiry 검사, Runner/history 접근, presentation commit/readback, cleanup과 response 결정이 끝날 때까지 coordinator만 lock lifetime을 소유한다.
- **Dependency rule:** LC-U1-02·05·06·08·09의 narrow ports를 호출하지만 어느 component도 LC-U1-01을 호출하지 않는다. 하위 component는 전달받은 context와 selector만 검증·사용하고 acquisition/release나 lifecycle sequencing을 수행하지 않는다.
- **Expiry publication fence:** post-Runner 검사 전에는 correlation, mapping, text fallback 또는 response publication을 시작하지 않는다. missing/expired이면 결과를 폐기하고 LC-U1-09 → SDK history → LC-U1-06/05 → session 순서로 zero-row cleanup한다.
- **NFR allocation:** NFR2.3, NFR2.6, NFR5.1, NFR9.2.

### LC-U1-02 Identity Capability Provider

- **Input:** opaque server session ID, persisted existing session row and operation budget reference.
- **Output:** non-serializable capability bound to user/session/conversation.
- **Shared resource:** existing session SQLite and existing token exchange path.
- **Schema rule:** 물리 row의 기존 인증·사용자·권한·위임 credential column을 snapshot contract로 보존하고 `session_expires_at`만 additive하게 추가한다. 논리 만료 view는 기존 schema를 대체하지 않는다.
- **Expiry rule:** lock 획득 직후 Runner 전과 Runner 직후에 persisted row를 읽는다. `now >= session_expires_at`이거나 row가 없으면 capability/Runner를 막거나 in-flight 결과를 폐기하고, LC-U1-01이 같은 lock 아래 전체 lifecycle cleanup을 수행한다. restart·activity·token refresh는 deadline을 연장하지 않는다.
- **Isolation:** only the gateway-facing accessor can retrieve a credential for one outbound attempt.
- **Read refresh port:** internal `ReadCredentialRefreshPortV1.refresh_once(capability_ref, refresh_budget_token, remaining_deadline)`는 LC-U1-03의 one-shot budget만 받고 동일 actor-bound capability handle을 반환한다. pre-call unusable credential과 typed 401은 같은 budget을 공유한다.
- **Create refresh port:** public `CredentialRefreshPortV1.refresh_delegated_capability_once(capability_ref, CredentialRefreshReservationV1, remaining_deadline)`는 U2가 durable하게 소비한 reservation을 필수로 받는다. LC-U1-13이 authenticated envelope와 exact create-attempt/actor binding을 검증한 뒤에만 exchange 최대 1회와 기존 `ServerSession.itsm_token` atomic commit을 수행한다. U2 table은 읽거나 쓰지 않는다.
- **Crash and replay:** reservation mismatch·tamper·restart replay는 exchange 0건이다. pre-commit crash는 consumed reservation을 되살리지 않고, post-commit crash는 persisted session credential을 복원하며 second exchange를 허용하지 않는다.
- **Policy separation:** LC-U1-02는 refresh를 실행하지만 시작 여부·횟수·남은 attempt/deadline을 결정하지 않는다. LC-U1-03은 read budget을, U2는 create durable reservation을 소유한다.
- **NFR allocation:** NFR1.1, NFR1.4, NFR2.1–NFR2.3, NFR2.5, NFR2.7, NFR5.2, NFR7.4.

### LC-U1-03 Ticket Operations Policy

- **Input:** strict `TicketReadToolInputV1`, capability, clock and sleeper ports.
- **Output:** exact `TicketReadToolResultV1` or repository operation for shared U2/U3 state.
- **Policy ownership:** canonicalization, max two HTTP attempts, refresh budget one, retry delay 0.25 seconds, whole-operation monotonic deadline.
- **Refresh sequence:** 첫 ticket call 전에 capability의 server-only usability를 검사한다. expired/imminently-expiring이면 one-shot budget을 소비해 `ReadCredentialRefreshPortV1`을 호출하며 실패 시 ticket HTTP call 0건으로 닫는다. usable credential의 첫 gateway attempt가 typed expired-credential outcome을 반환한 경우에도 같은 budget이 남아 있을 때만 refresh한다. 성공 handle은 operation context를 대체하고 남은 attempt에 사용하며, 두 trigger를 합쳐 refresh는 최대 1회다.
- **Projection:** allowlisted summary/detail, safe page, server-only ETag evidence and SafeErrorV1.
- **NFR allocation:** NFR1.2–NFR1.4, NFR3.1, NFR4.1, NFR7.1–NFR7.4.

### LC-U1-04 ITSM Gateway Adapter

- **Input:** capability plus typed endpoint input and per-attempt timeout no greater than remaining operation deadline.
- **Output:** typed success or typed transport failure from exactly one HTTP attempt; internal update profile returns `ReadForUpdateResultV1 | SafeErrorV1` through LC-U1-03.
- **Ordinary detail profile:** a contract-valid visible public projection may succeed without usable ETag; invalid or absent ETag yields no server-only update evidence.
- **Read-for-update profile:** the C-01/C-02 port consumed by U3 requires a strong quoted-decimal ETag equal to the public version. Valid evidence produces `ReadForUpdateResultV1`; missing, weak, non-decimal or mismatched ETag returns exactly `SafeErrorV1(upstream_unavailable)` and keeps review/PATCH call counts at zero.
- **Contract seam:** both profiles share response/body validation, but LC-U1-03 selects the purpose before the call and tests the two success criteria independently.
- **Connection resource:** existing application-lifetime `httpx.AsyncClient`; no per-request client.
- **Trust-boundary rule:** raw body, response object, header collection and exception never cross the adapter.
- **NFR allocation:** NFR1.1–NFR1.3, NFR2.1–NFR2.4, NFR7.1–NFR7.3.

### LC-U1-05 Cursor Repository

- **Input:** capability, canonical query material/hash and upstream cursor.
- **Output:** CSPRNG `continuation_ref`, or exact canonical query and server-only cursor on successful once-only resolve.
- **Transaction boundary:** binding validation, hash recheck and consumption occur atomically.
- **Cleanup:** access-time and startup cleanup plus explicit lifecycle invalidation.
- **NFR allocation:** NFR4.2.

### LC-U1-06 Confirmation Repository

- **Input:** strict create/update variant, server-derived exact binding and, for confirmation only, `CurrentTurnEvidenceV1`.
- **Ports:** `confirm(binding, current_turn_evidence)` atomically performs only `pending → confirmed`; `consume_once(binding)` is a separate operation that rechecks the same binding and atomically performs only `confirmed → consumed`.
- **Output:** save returns an opaque pending ref; confirm returns state success without transport authority; successful consume returns exactly `ConsumedMutationEvidenceV1 { mutation_id, confirmed_at }` once. No output contains a credential, idempotency key, canonical request bytes, raw confirmation text, or a claim that HTTP executed.
- **Transaction boundary:** same-operation invalidation and new insert are one transaction; each confirm and consume transition is its own compare-and-set transaction. Concurrent or repeated consume has at most one winner.
- **Operation-specific publication:** create publication은 이전 pending/confirmed create를 원자 교체할 수 있다. update prepare/revise는 미만료 `confirmed` update가 있으면 새 row publication을 원자 거부하며, exact `consume_once` 재개·expiry·lifecycle invalidation 전에는 경쟁 pending을 만들 수 없다. update revise는 exact expected-old `pending`만 교체한다.
- **Downstream execution boundary:** U2 and U3 must bind the evidence to their own operation state and pass their own execution CAS/preconditions. Evidence alone can never call POST/PATCH.
- **Downstream ownership:** U2 owns the external durable `ticket_tools_create_v1` ledger. LC-U1-06 and every U1 lifecycle path are forbidden from deleting or rewriting its rows, keys, or canonical bytes.
- **Crash-before-bind recovery:** after U1 consume but before U2 evidence binding, keep the same U2 attempt, idempotency key and request bytes; publish a new pending review and require a new explicit confirmation. Never reconstruct evidence from the consumed U1 row or POST from unbound evidence.
- **NFR allocation:** NFR1.4, NFR2.3, NFR3.2, shared lifecycle safety.

### LC-U1-07 Tool and Mapper Registry

- **Input:** versioned plugin registrations from U1–U3.
- **Output:** immutable tool and mapper collections for Agent composition.
- **Checkpoint rule:** U1 checkpoint contains `ticket_read`; U4 requires the exact final set `ticket_read`, `ticket_write`, `ticket_update`.
- **Isolation:** tool name and mapper kind are code-owned allowlists; ITSM/model text cannot register or select components.
- **NFR allocation:** NFR1.4, NFR5.1.

### LC-U1-08 and LC-U1-09 Conversation Presentation Boundary

- **Input:** existing Runner result, persisted assistant item and typed tool result.
- **Output:** required assistant text plus optional validated V1 presentation.
- **Entry fence:** LC-U1-01이 전달한 valid `LockHeldRequestContextV1`과 유효한 pre-Runner persisted-expiry 검사 없이는 Runner 또는 SDK history에 접근하지 않는다. LC-U1-08은 LC-U1-01을 호출하거나 lock을 직접 획득하지 않는다.
- **Post-Runner fence:** persisted session을 다시 읽어 유효함을 확인한 뒤에만 assistant correlation, mapping, fallback 또는 publication을 수행한다. expired/missing이면 입력 Runner result를 폐기하고 typed `ExpiredAfterRunnerV1` outcome을 상위 호출자에게 반환한다. LC-U1-01이 그 outcome을 받아 cleanup을 조정하며 LC-U1-08은 coordinator를 호출하지 않는다.
- **Transaction boundary:** verify persisted message and insert/replace companion atomically under the conversation lock; expose metadata only after commit readback.
- **History-load operation:** left-join by conversation/sequence/text hash, omit every invalid or orphan companion from the response, then idempotently delete orphan rows in a bounded repository transaction.
- **Startup cleanup operation:** scan companion correlation keys against existing SDK assistant-item keys and idempotently delete rows with no matching message. It never synthesizes or repairs presentation data.
- **Cleanup failure:** preserve text-only history, roll back the failed cleanup transaction, record only a safe diagnostic, and retry on the next startup or history load. Orphan metadata is never returned while cleanup is pending.
- **NFR allocation:** NFR1.3, NFR9.1, NFR9.2.

### LC-U1-12 Conversation Serialization Port

- **Input:** opaque conversation scope derived before capability creation.
- **Output:** an opaque, non-serializable `LockHeldRequestContextV1` whose lifetime is bounded by an LC-U1-01-owned acquire/release scope.
- **Ownership:** the existing lock provider performs acquisition; LC-U1-01 owns orchestration and release. LC-U1-02/08 accept the context as proof of the held boundary but cannot acquire, release, retain, serialize, or call the coordinator through it.
- **Acyclic composition:** LC-U1-12 depends only on the existing lock provider. LC-U1-01, LC-U1-02 and LC-U1-08 depend on its contract; none is an implementation dependency of LC-U1-12.
- **NFR allocation:** NFR2.6, NFR9.2.

### LC-U1-13 Refresh Reservation Verifier

- **Input:** opaque `CredentialRefreshReservationV1`, current server-held capability binding and expected create attempt.
- **Output:** non-serializable verified reservation claim or typed authentication failure.
- **Verification:** existing server secret로 envelope authenticity와 create-attempt·user·session·conversation·used-at·nonce binding을 검증한다. U2 ledger의 durable one-invocation claim은 U2가 이 port 호출 전에 완료하며 U1은 그 table에 접근하지 않는다.
- **Isolation:** token exchange, session mutation, retry와 replay storage를 소유하지 않는다. 검증된 claim만 LC-U1-02에 전달한다.
- **NFR allocation:** NFR2.7.

## Runtime Sequences

### First-page list or detail

1. LC-U1-01이 opaque session ID에서 conversation scope만 얻고 LC-U1-12를 통해 shared per-conversation lock과 `LockHeldRequestContextV1`을 획득한다. context를 전달받은 LC-U1-02가 persisted session과 absolute expiry를 다시 읽는다. expired/missing row는 presentation·SDK history·pending·cursor·session cleanup을 수행하며 Runner·ITSM call counts는 0이다.
2. session이 유효할 때 LC-U1-01은 context를 LC-U1-08에 전달하고, LC-U1-08은 lock을 직접 관리하거나 coordinator를 역호출하지 않은 채 immutable registry의 existing Agent를 실행한다.
3. The `ticket_read` boundary validates one mode and calls LC-U1-03.
4. LC-U1-03 canonicalizes input and creates one operation budget. capability가 expired/imminently-expiring이면 LC-U1-02의 internal `ReadCredentialRefreshPortV1`을 먼저 호출한다. 실패 시 ticket HTTP call 0건으로 닫고 성공 handle만 다음 단계에 사용한다.
5. LC-U1-04 performs one HTTP attempt with the usable delegated credential and returns a typed outcome.
6. typed expired-credential outcome이면 같은 one-shot refresh budget이 아직 남았을 때만 `ReadCredentialRefreshPortV1`을 호출한다. 성공 handle은 남은 final attempt에만 사용한다. 그 외에는 allowlisted transient first failure만 250ms delay 뒤 final call을 허용한다. pre/post-call trigger를 합쳐 refresh는 1회, HTTP attempt는 2회 이하이다.
7. Runner 직후 LC-U1-02가 같은 context 아래 persisted session을 재검증한다. missing/expired이면 LC-U1-08이 결과를 폐기하고 typed expiry outcome을 반환하며, LC-U1-01은 response correlation·mapping·fallback·publication 전에 terminal cleanup을 수행한다.
8. post-Runner session이 유효할 때만 LC-U1-08이 optional metadata를 map하고 LC-U1-09가 persisted assistant item에 commit한다. LC-U1-01은 text 또는 validated presentation을 포함한 응답을 결정한 뒤 lock을 해제한다.

### Continuation

1. LC-U1-03 supplies capability and `continuation_ref` to LC-U1-05.
2. LC-U1-05 verifies actor, conversation, serialization version and canonical material/hash, then consumes the row atomically.
3. LC-U1-03 reuses the exact stored query and server-only upstream cursor; replacement filters are impossible.
4. A further page issues a new reference. Any mismatch ends before LC-U1-04 is called.

### U2 create credential refresh

1. U2가 자기 `ticket_tools_create_v1` attempt에서 reservation one-invocation claim을 durable하게 소비하고 authenticated opaque `CredentialRefreshReservationV1`을 만든다.
2. U2가 current capability, reservation과 positive remaining deadline으로 LC-U1-02의 `CredentialRefreshPortV1`을 정확히 한 번 호출한다.
3. LC-U1-02는 U2 table을 읽지 않고 LC-U1-13에 envelope authenticity와 exact create-attempt·user·session·conversation binding 검증을 요청한다. mismatch·tamper·replay는 exchange 0건으로 종료한다.
4. 검증 성공 시 LC-U1-02가 token exchange를 최대 한 번 실행하고 기존 `ServerSession.itsm_token`을 원자 교체한 뒤 같은 actor-bound capability만 반환한다.
5. commit 전 crash는 consumed reservation을 되살리지 않고, commit 후 return 전 crash는 이후 request가 persisted credential을 복원한다. 어떤 경로도 같은 create attempt의 second exchange를 허용하지 않는다.

### Lifecycle cleanup

| Event | Ordered logical components | Commit rule |
|---|---|---|
| User switch | prepare new identity → LC-U1-01 acquires old conversation lock → post-lock expected old user/session/conversation revalidation → LC-U1-09 presentation clear → existing history clear → LC-U1-06/05 invalidate → preserve U2 durable ledger → commit new identity → release lock | actor mismatch leaves the newly committed scope untouched and discards old-scope work; cleanup failure prevents new identity commit; commit 뒤 old-scope message/presentation 재생성 0건 |
| Logout | LC-U1-01 lock acquire → post-lock expected actor revalidation → LC-U1-09 clear → existing history clear → LC-U1-06/05 invalidate → preserve U2 durable ledger → session delete → release lock | actor mismatch touches no different scope; session delete is terminal and commit 뒤 old-scope message/presentation 재생성 0건 |
| Conversation clear | LC-U1-01 lock acquire → post-lock expected actor/conversation revalidation → LC-U1-09 clear → existing history clear → LC-U1-06/05 invalidate → terminal cleared-state commit → release lock | operations are idempotent, U2 durable ledger는 보존되며 commit 뒤 old-scope message/presentation 재생성 0건 |
| Session expiry before Runner | LC-U1-01 lock acquire → LC-U1-02 persisted expiry re-read → LC-U1-09 clear → existing SDK message/session clear → LC-U1-06/05 invalidate → preserve U2 durable ledger → session delete | terminal U1-owned zero-row cleanup precedes `authentication_required`; Runner and ITSM calls are 0; U2 ledger key/bytes remain unchanged |
| Session expiry during Runner | Runner completes under LC-U1-01 lock → LC-U1-02 persisted expiry re-read → discard LC-U1-08 result → LC-U1-09 clear → existing SDK message/session clear → LC-U1-06/05 invalidate → preserve U2 durable ledger → session delete | correlation, mapping, fallback, success response and presentation publication are 0; competing expiry request waits and then accepts empty U1-owned state idempotently |

### Presentation retention cleanup

1. On application startup, LC-U1-09 enumerates companion correlation keys and checks for the exact matching persisted SDK assistant item.
2. It deletes orphan rows idempotently in short transactions and leaves valid rows unchanged.
3. On every history load, the left join first determines the text response; unmatched, corrupt or unknown metadata is excluded from that response.
4. LC-U1-09 then attempts idempotent deletion of the orphan rows found by that load.
5. If either cleanup transaction fails, the existing text history still returns, no orphan metadata is exposed, and the next startup or history load retries cleanup.

## Shared Resources and Isolation

| Shared resource | Owner and consumers | Isolation mechanism | Capacity/scaling stance |
|---|---|---|---|
| Application-lifetime AsyncClient | LC-U1-04 | typed adapter and per-attempt timeout | reuse existing connection pool; no new pool or tuning target |
| Server Session SQLite | existing session owner, LC-U1-02, LC-U1-05, LC-U1-06 | existing session columns preserved, additive `session_expires_at`, U1-only `ticket_tools_state_v1`, short transactions, exact actor keys | current single-process deployment; no new database |
| U2 durable create ledger | U2 owner; U1 read/write consumers 없음 | separate `ticket_tools_create_v1` namespace, immutable attempt/key/canonical-bytes ownership across U1 lifecycle cleanup | downstream resource preserved unchanged; U2 completes claim/replay policy |
| Agents SDK History SQLite | existing conversation owner, LC-U1-09 | U1-only `ticket_tools_history_v1`, conversation/sequence uniqueness | follows existing history capacity and retention |
| Conversation lock | existing provider exposed by LC-U1-12; LC-U1-01 owns acquire/release scope; LC-U1-02/08/09 receive opaque held context | one shared lock per conversation from pre-Runner persisted-expiry re-read through Runner/history, post-Runner re-read, publication decision or terminal cleanup; consumers cannot call coordinator or release lock | single-process guarantee; multi-process requires later shared mechanism |
| Tool registry | LC-U1-07 | composition-time immutable map and duplicate rejection | exactly three final ticket plugins; no dynamic remote registry |
| Read budget | LC-U1-03 | operation-local attempts, internal read refresh and monotonic deadline | no global/shared breaker state |
| Create refresh reservation | U2 durable ledger owner; LC-U1-13 verifies; LC-U1-02 exchanges/commits | authenticated opaque envelope, durable one-invocation claim before U1, atomic `ServerSession.itsm_token` rotation | no U1 access to U2 storage; no second exchange after crash/replay |

SQLite transactions are kept to binding/correlation mutations and do not include outbound ITSM or OpenAI waits. This avoids holding the shared databases across network latency while preserving atomic compare-and-set semantics.

## Failure Domains and Blast Radius

| Failure domain | Example failure | Blast radius | Containment and recovery |
|---|---|---|---|
| Identity capability | expired session before Runner or credential refresh failure after a typed 401 | one user request | pre-Runner failure makes no Runner/ITSM call; refresh failure consumes the single refresh budget and permits no further HTTP attempt; re-login |
| Create refresh reservation | tamper, binding mismatch, replay, exchange/commit crash | one U2 create attempt | verifier rejects before exchange; accepted reservation exchanges at most once; persisted commit is restored without second exchange |
| Runner/expiry interleaving | session expires while Runner writes SDK history and another expiry request arrives | one conversation | shared lock serializes both requests; post-Runner result is discarded and terminal cleanup leaves no SDK/session/presentation/revocable rows or success publication |
| Session migration | existing column drift or unsafe legacy row | application startup or affected protected request | rollback/fail closed; never replace existing schema or grant fresh lifetime |
| ITSM transport | timeout, 503, malformed body | one ticket read operation | ≤2 attempts and shared deadline; safe error |
| Cursor state | row missing, tampered, expired | one continuation | invalidate and start a new search |
| Confirmation state | confirm/consume transaction, expiry, binding or repeat-consume failure | one operation's confirmation | no evidence or mutation authority; prepare or review again |
| Confirmed update publication | crash after confirm followed by prepare/revise | one update scope | exact consume may resume; otherwise expiry/lifecycle only, with competing pending and PATCH 0건 |
| U1 consume before U2 bind | process crash after one-time evidence issuance | one preserved U2 create attempt | keep attempt/key/bytes, issue a new pending review, require new confirmation, and make no POST from unbound evidence |
| Registry composition | duplicate name or incompatible V1 | application startup/composition | fail closed before serving altered tool set |
| Presentation persistence or retention cleanup | lock, correlation, commit, startup cleanup or history-load cleanup failure | one message's structured metadata or orphan rows in one history store | preserve text-only response/history, never expose orphan metadata, retry idempotent cleanup next startup/load |
| History cleanup | partial SQLite failure | one conversation lifecycle transition | idempotent retry; new context not committed |
| Browser metadata parser | unknown version/kind/block | one rendered message | ignore metadata and render existing text |
| Test harness | unexpected network or leaked canary | current test run | immediate failure with sanitized diagnostics |

No failure domain is allowed to turn unknown state into success, broaden authorization, or cause a third read attempt. Presentation is intentionally a lower-criticality domain: it may degrade independently without making the core text response unavailable.

## Performance and Reliability Allocation

- LC-U1-04 reuses the existing AsyncClient connection pool; U1 adds no cache because ITSM remains authoritative and query freshness is required.
- LC-U1-03 owns the entire read time budget. Each attempt receives the lesser of `ITSM_TIMEOUT_SECONDS` and remaining time.
- Only timeout, transport error, 500, 502, 503 and 504 from the first attempt may cause one 250ms delay and final attempt.
- 429 returns immediately without sleep or retry. A validated integer Retry-After may inform text only.
- Circuit breaker, queue, global rate limiter, background refresh and stale-ticket fallback are excluded because no new availability/throughput target was established and shared state could amplify cross-user impact.
- Repository loss does not grant authority: continuation and confirmation fail closed; presentation alone degrades to text.

## Security and Accessibility Allocation

| Concern | Primary component | Supporting component |
|---|---|---|
| Server-only identity | LC-U1-02 | LC-U1-01 |
| Delegated token use | LC-U1-04 | LC-U1-02 |
| Refresh policy and execution separation | LC-U1-03 | LC-U1-02 `CredentialRefreshPortV1` |
| Authenticated create refresh reservation | U2 durable claim + LC-U1-13 | LC-U1-02 `CredentialRefreshPortV1` |
| Safe input/output projection | LC-U1-03 | LC-U1-04 |
| Cursor binding | LC-U1-05 | LC-U1-03 |
| Confirmation binding | LC-U1-06 | LC-U1-01 |
| Prompt/markup isolation | LC-U1-03 | LC-U1-07, LC-U1-10 |
| Message correlation | LC-U1-08 | LC-U1-09 |
| Text-first accessible state | LC-U1-10 | LC-U1-08 |
| Secret regression testing | LC-U1-11 | every public boundary |

## Infrastructure Handoff

U1 requires no new deployable component. Infrastructure Design should preserve the existing FastAPI process, application-lifetime httpx client, Server Session SQLite, Agents SDK History SQLite and browser assets. It only needs to account for:

- two U1-owned migration namespaces in the existing databases;
- one additive `session_expires_at` column in the existing session table, with every existing session column and restore meaning preserved;
- transaction and file-permission behavior already used by those stores;
- existing TLS validation for ITSM HTTPS;
- current single-process conversation-lock assumption;
- deterministic Runner barrier/fake-clock seams for user switch, logout, conversation clear and session expiry; each asserts same-lock wait, post-lock actor revalidation, presentation-before-history cleanup, terminal commit and old-scope message/metadata regeneration 0건;
- concurrent confirmation-consumption, confirm-then-crash update prepare/revise, and crash-before-U2-bind seams that assert a single consume winner, confirmed-update publication/PATCH 0건, exact two-field evidence, unchanged U2 ledger attempt/key/bytes, new review/re-confirmation and zero POST from unbound evidence;
- U2 durable one-invocation reservation/verifier seam that covers actor/create-attempt mismatch, tamper, restart replay and pre/post-credential-commit crash with exchange≤1 and second exchange 0건;
- test-only `coverage==7.17.0`, with no runtime dependency impact.

## NFR Coverage Summary

| NFR | Logical allocation |
|---|---|
| NFR1.1–NFR1.4 | LC-U1-02, LC-U1-03, LC-U1-04, LC-U1-07, LC-U1-10, LC-U1-11 |
| NFR2.1–NFR2.5 | LC-U1-01, LC-U1-02, LC-U1-04 |
| NFR2.6 | LC-U1-12 acyclic lock contract, LC-U1-01 acquire/release ownership, 네 lifecycle event의 post-lock actor 재검증·presentation-before-history cleanup·terminal commit, LC-U1-02 pre/post-Runner expiry checks와 LC-U1-08 stale-result discard |
| NFR2.7 | U2 durable one-invocation claim, LC-U1-13 authenticated reservation verification, LC-U1-02 exact binding, single exchange and atomic ServerSession credential commit |
| NFR3.1 | LC-U1-03 and LC-U1-04 validated ETag evidence seam |
| NFR3.2 | LC-U1-06 separate confirm/consume_once CAS operations, exact two-field one-time evidence, downstream binding boundary, LC-U1-01 lifecycle exclusion of the U2 durable ledger |
| NFR4.1–NFR4.2 | LC-U1-03 and LC-U1-05 |
| NFR5.1–NFR5.2 | all components remain embedded; LC-U1-02 preserves the physical session schema and adds expiry only |
| NFR6.1 | LC-U1-11 |
| NFR7.1–NFR7.4 | LC-U1-03 and LC-U1-04 |
| NFR9.1–NFR9.2 | LC-U1-08, LC-U1-09, LC-U1-10 |

## Outcome

The logical design concentrates authority and recovery policy in narrow owners: lifecycle in LC-U1-01, credentials in LC-U1-02/04, attempts in LC-U1-03, revocable state in LC-U1-05/06, composition in LC-U1-07, and message correlation in LC-U1-08/09. Each component has a bounded failure domain and an explicit safe degradation path without introducing another service or operational dependency.
