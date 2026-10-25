# U1 Ticket Read Skeleton — 기술 스택 결정

## Sources

- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md` — 현재 runtime·framework·database·test 도구
- `construction/u1-ticket-read-skeleton/functional-design/functional-spec.md` — U1 ports, workflow, state ownership
- `construction/u1-ticket-read-skeleton/functional-design/rules.md` — retry, identity, presentation, verification 규칙
- `inception/requirements-analysis/requirements.md` — NFR1–NFR9와 기술 제약
- `inception/contract-design/contract-summary.md` — shared V1, storage namespace, outbound profile
- `construction/u1-ticket-read-skeleton/nfr-requirements/security-requirements.md` — 측정 가능한 U1 안전 목표
- `https://pypi.org/project/coverage/7.17.0/` — coverage.py 7.17.0 배포 metadata와 Python 3.13 지원
- `https://coverage.readthedocs.io/en/7.17.0/` — pytest 실행과 report 형식에 대한 공식 문서

## 결정 원칙

U1은 독립 서비스가 아니라 기존 단일 애플리케이션에 embedded되는 `library`다. 따라서 기존 runtime과 framework를 교체하거나 병렬 stack을 만들지 않고, 외부 ITSM 경계를 port/adapter로 격리해 테스트 가능성을 확보한다. 기술 선택은 상위 계약을 구현하는 최소 변경으로 제한한다.

## Stack Decisions

| ID | 선택 | 용도 | 근거와 제약 | 대안 및 기각 이유 | 관련 요구사항 |
|---|---|---|---|---|---|
| TD-U1-01 | Python 3.13 | U1 domain, ports, adapters, repository, tool integration | 저장소 runtime과 팀 관행을 유지하고 새 실행 환경을 만들지 않는다. | 다른 언어·별도 process는 기존 배포와 session 경계를 분리하므로 기각한다. | NFR5.1 |
| TD-U1-02 | FastAPI 0.162.0 + Pydantic 2.14.1 | 기존 chat API 호환, strict V1 input/result 검증 | 기존 endpoint와 dependency injection을 확장하고 `additional_properties: false` 계약을 model validation으로 고정한다. | 새 endpoint framework나 새 service는 범위 밖이다. | NFR1.1, NFR5.1 |
| TD-U1-03 | openai-agents 0.24.0의 기존 `Agent`, `Runner`, `SQLiteSession`, `function_tool` | `ticket_read` tool과 기존 대화 이력 | 새 Agent나 자체 loop 없이 기존 model `gpt-6-luna`, reasoning `high`, tracing disabled 설정을 보존한다. | 별도 orchestration loop는 FR1.2와 회귀 요구에 어긋난다. | NFR5.1, NFR9.2 |
| TD-U1-04 | httpx 0.28.1의 application-lifetime `AsyncClient`와 typed adapter | ITSM API v2 outbound HTTP | connection reuse를 유지하되 public gateway operation은 호출당 정확히 한 HTTP attempt만 수행한다. | 새 HTTP client 또는 gateway 내부 retry는 timeout·attempt 계약을 이중화하므로 기각한다. | NFR2.1, NFR7.1, NFR7.2 |
| TD-U1-05 | 기존 Server Session SQLite의 additive `session_expires_at` migration과 `ticket_tools_state_v1` namespace | 서버 세션 절대 만료, pending mutation, cursor binding | 기존 ServerSession 인증·사용자·권한·위임 credential field를 그대로 둔 채 만료 column만 추가한다. pending repository는 transaction/CAS로 `confirm`과 `consume_once`를 분리하고 최소 증거를 한 번만 반환한다. Unexpired confirmed update는 exact consume·expiry·lifecycle invalidation 전 새 publication을 차단한다. U1 lifecycle cleanup은 자체 revocable namespace만 정리하고 U2의 `ticket_tools_create_v1` ledger를 삭제·재작성하지 않으며 U1만 migration을 소유한다. | session table 재작성·field rename, confirm과 consume을 한 연산으로 합치기, confirmed authority와 새 pending의 공존, U1의 U2 table 직접 mutation 또는 새 database·cache는 기존 복원·소유권 계약을 깨고 중복 mutation 위험과 운영 의존성을 추가하므로 기각한다. | NFR2.3, NFR2.5, NFR3.2, NFR4.2, NFR5.2, NFR7.3 |
| TD-U1-06 | 기존 Agents SDK history SQLite 안의 `ticket_tools_history_v1` namespace + 하나의 application conversation lock | Runner history 접근, presentation companion 저장·message correlation, 모든 history-mutating lifecycle cleanup 직렬화 | 같은 conversation의 Runner, user switch, logout, conversation clear, session expiry가 같은 lock을 사용한다. 각 event는 lock 뒤 actor scope를 재검증하고 presentation-before-history cleanup과 terminal commit까지 lock을 유지한다. Runner 직후 original actor scope와 persisted expiry를 response 결정 전에 재검증해 stale/expired 결과를 폐기한다. | event별 다른 lock이나 lock 밖 history 삭제는 cleanup 이후 old-scope row 재생성을 허용한다. in-memory-only metadata는 restart 복원을 잃고, 별도 store는 원자성 범위를 넓히므로 기각한다. | NFR2.6, NFR5.1, NFR9.2 |
| TD-U1-07 | server-owned request capability와 typed `SafeErrorV1`·projection V1 models | credential confinement과 trust boundary | token value를 model/schema/log에서 제거하고 외부 응답을 allowlist로 축소한다. | raw response pass-through나 dict 기반 비정형 경계는 비밀·schema drift를 검증하기 어려워 기각한다. | NFR1.1, NFR1.2, NFR1.3, NFR2.1 |
| TD-U1-08 | pytest 9.1.1 + 기존 FakeModel + `httpx.MockTransport` | unit, contract, walking-skeleton, regression test | 실제 OpenAI·ITSM 호출 없이 tool loop와 HTTP request를 결정적으로 검증한다. | 실제 API를 기본 자동화에 포함하면 비결정성·비용·운영 데이터 위험이 생기므로 기각한다. | NFR1.4, NFR2.2, NFR6.1 |
| TD-U1-09 | test-only `coverage==7.17.0`을 고정하고 pytest를 그 아래 실행 | 변경 application code line coverage 측정 | 공식 배포 metadata상 Python 3.11–3.16을 지원하므로 프로젝트의 Python 3.13과 호환된다. 현재 coverage 도구가 없으므로 재현 가능한 line data와 machine-readable JSON report가 필요하다. formatter·linter·type checker 추가 금지에는 해당하지 않는다. | 수동 추정은 80% 기준을 증명하지 못하고, pytest-cov는 이 용도에 불필요한 plugin dependency를 추가하므로 기각한다. | NFR6.1 |
| TD-U1-10 | 기존 browser JavaScript/HTML/CSS의 optional `TicketPresentationV1` 처리와 text fallback | 목록·상세·오류의 접근 가능한 표현 | build tool 없이 기존 reply와 live announcement를 유지하며 unknown metadata는 무시한다. | 새 UI framework·화면·button은 범위 밖이며 기존 경험 회귀 위험이 크다. | NFR5.1, NFR9.1, NFR9.2 |
| TD-U1-12 | 기존 server secret으로 검증하는 authenticated opaque refresh reservation + U2 durable one-invocation claim + U1 `CredentialRefreshPortV1` | create token-expired 복구의 actor binding, replay 차단, 단일 exchange와 atomic credential rotation | U2가 reservation claim과 restart replay 차단을 소유하고 opaque envelope에 create-attempt·actor binding을 인증한다. U1은 U2 table을 읽지 않고 envelope를 검증한 뒤 exchange 최대 1회와 기존 ServerSession credential atomic commit만 수행한다. | raw actor field를 신뢰하거나 U1이 U2 storage를 읽는 방식은 위조 또는 소유권 침범을 만들고, in-memory replay set은 restart 안전성이 없어 기각한다. | NFR1.1, NFR2.7, NFR7.3 |

## 상세 교차 품질 요구사항

| ID | 요구사항 | 합격 기준 | 구현·검증 결정 |
|---|---|---|---|
| NFR5.1 | 기존 37개 기준선과 신규 U1 테스트를 모두 통과하고 model·reasoning·tracing·user switch·session·history·UI/API의 승인되지 않은 변경을 만들지 않는다. | 기준선과 완료본 테스트 통과율 100%; 승인되지 않은 회귀 0건 | 코드 변경 전 기준선을 기록하고 U1 계층 테스트 후 전체 suite를 다시 실행한다. |
| TD-U1-11 | NFR5.2의 additive ServerSession migration 계약을 기존 physical schema에 적용한다. | authoritative 요구사항과 합격 기준은 `security-requirements.md`의 NFR5.2를 그대로 적용하며 이 문서는 별도 NFR을 정의하지 않는다. | 기존 migration helper로 `session_expires_at` column만 추가하고, NFR5.2가 열거한 기존 field의 PRAGMA schema와 byte 값 snapshot, session restore, refresh, user switch, parse 가능한 `created_at + 8시간` backfill, malformed row fail-closed expiry를 하나의 contract test에서 검증한다. |
| NFR6.1 | U1에서 새로 만들거나 변경한 application code의 line coverage를 측정한다. | 대상 code line coverage 80% 이상; 누락·측정 실패는 통과로 간주하지 않음 | `python -m coverage erase`, `python -m coverage run --source=app -m pytest`, `python -m coverage json --include='<Code Generation source manifest의 comma-separated app paths>' --fail-under=80 -o coverage.json` 순서로 실행한다. Code Generation이 확정한 changed application path만 report 대상에 넣고 최종 전체 판정은 U4가 수행한다. |

## Dependency and Version Policy

- 기존 직접 dependency 버전은 현재 pin을 유지한다. 계약 구현에 필요하지 않은 upgrade를 U1과 함께 수행하지 않는다.
- `coverage==7.17.0`을 test-only 직접 dependency로 `requirements.in`에 pin하고 Python 3.13용 `requirements.txt`를 기존 uv compile 절차로 갱신한다. 표준 실행과 JSON report 명령은 NFR6.1을 따른다.
- application code는 Python 관용구, type hints, dataclass/Pydantic boundary, explicit dependency injection, 작은 함수와 기존 module layout을 따른다.
- 새 formatter, linter, type checker, package build system, JavaScript bundler, container, cloud IaC는 추가하지 않는다.

## Logical Module Boundaries

| Module responsibility | 허용 dependency | 금지 dependency |
|---|---|---|
| IdentitySession capability | 기존 server session field·token refresh path, additive `session_expires_at`, authenticated reservation verifier | model/tool-supplied identity, serializable token value, U2 table 직접 접근, 기존 field 제거·rename·재해석 |
| TicketOperations policy | typed gateway port, cursor/pending repositories, clock/sleeper abstraction, 분리된 `confirm`/`consume_once`와 `ConsumedMutationEvidenceV1` | raw HTTP client, independent tool/mapper retry, 소비 증거만으로 mutation transport 실행 |
| ItsmGateway adapter | application AsyncClient, environment-derived timeout, outbound contract | repository, Agent, browser presentation |
| Tool plugin/registry | TicketOperations public boundary, Agents SDK function tool | credential, raw cursor, raw response/header |
| Presentation mapper/history | typed tool result, persisted assistant correlation, Runner와 expiry cleanup이 공유하는 conversation lock | raw tool trace, credential, HTML injection, post-Runner expiry 검사 전 metadata commit |
| Lifecycle integration | 같은 conversation lock 아래의 persisted-session 재검증, U1 repository invalidation ports와 existing session/history operations, U2 durable ledger preservation | lock 밖 SDK history 삭제, Runner와 cleanup의 독립 동시 실행, `ticket_tools_create_v1` 삭제·재작성 또는 다른 direct downstream Unit table mutation |

## 운영·확장 결정

- 새 throughput, availability, horizontal-scaling 또는 deployment target을 만들지 않고 기존 Assistant 운영 기준을 유지한다.
- U1은 current single-process application 경계에서 conversation lock을 사용한다. 다중 process 배포가 실제로 도입되면 같은 correlation/atomicity를 보장하는 shared lock 또는 transaction design을 별도 versioned 결정으로 검토한다.
- 자동화 테스트는 제어 가능한 Runner barrier를 주입해 history write가 진행 중일 때 user switch·logout·conversation clear·session expiry를 각각 시작한다. 각 event가 같은 lock에서 대기하고 actor scope를 재검증한 뒤 terminal commit까지 lock을 유지하며, cleanup 뒤 old-scope SDK message/session·presentation이 재생성되지 않음을 검증한다. Expiry에서는 revocable state·server session과 성공 publication도 0건이어야 한다.
- Refresh contract test는 U2 durable one-invocation claim과 opaque reservation verifier를 fake로 주입해 actor/create-attempt mismatch, tamper, restart replay, pre/post-commit crash에서 허용 밖 exchange와 second exchange가 0건이고 성공 전에 기존 session credential이 원자 교체됐음을 검증한다.
- cursor·pending·presentation state는 authoritative ITSM data의 cache가 아니다. loss 시 권한을 확대하거나 성공을 추측하지 않고 안전하게 search/review를 다시 시작하거나 text-only로 degrade한다.
- pending confirmation 소비 뒤 U2 evidence binding 전에 process가 중단되면 U1은 소비 증거를 재발급하지 않는다. U2의 기존 attempt/key/bytes는 보존하고 같은 attempt에 새 pending review를 발행해 명시적 재확인을 요구하며, 결합되지 않은 증거로 POST하지 않는다.
- ITSM API v2와 OpenAI 호출에 대한 실제 smoke는 기본 자동화에서 분리하며 명시적 credential과 운영 승인 없이는 실행하지 않는다.

## 결과

U1은 기존 배포와 사용자 흐름을 그대로 유지하면서 ports/adapters, exact V1 schemas, scoped SQLite namespaces, 분리된 confirmation consumption, deterministic test doubles만 추가한다. 이 결정은 U2·U3가 공통 경계를 재정의하지 않고 plugin과 mutation-specific 정책만 확장하게 하며, U1 cleanup이 U2의 durable create state를 손상하지 않도록 소유권을 고정한다.
