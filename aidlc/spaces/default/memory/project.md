# Project-Level Rules

> Project-specific specialisation and corrections. Loaded after `org.md` and
> `team.md` as strict-additive guidance; contradictions with broader policy
> are rejected. Populated by practices-discovery and the self-learning loop.
>
> Use sparingly: most teams don't need a project layer. Reach for it
> only when this specific project needs stable, durable guidance beyond the
> team practice (for example, package-specific release checks or an additional
> regression suite for a legacy component).

## Way of Working

<!-- Project-specific specialisation. Example: -->
<!-- This monorepo requires package-scoped branch names and a package owner -->
<!-- review in addition to the team's normal merge policy. -->

## Walking Skeleton

<!-- Project-specific specialisation. Example: -->
<!-- The walking skeleton must exercise the legacy service adapter as well -->
<!-- as the new service boundary. -->

## Testing Posture

<!-- Project-specific specialisation. -->

- R-17은 runtime infrastructure 추가가 아니라 기존 promotion gate에 deterministic concurrency evidence를 추가하는 변경으로 해석했다. barrier event, direct row count, response/publication counter가 blocking evidence다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:infrastructure-design:519441d2a8500fc1f94b0e26019c65d6832162554b15c3cfa755613cdece0295 -->

- 테스트는 시간 기반 flaky race 대신 controllable Runner history-write barrier와 fake clock을 사용한다. 실제 경쟁 순서를 결정적으로 고정하면서 production lock 경계를 그대로 통과시킨다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:code-generation:7fe7fbdba193e9304d4e660af7f84853b875c7342c9b899effc74e72141c7c72 -->

- NFR3.2와 credential refresh 보강은 새 runtime resource가 아니라 기존 승격 경로의 blocking test contract로 반영했다. confirmation CAS, U2 ledger isolation, crash-before-bind, pre-call/401 shared refresh budget을 각각 관찰 가능한 counter와 snapshot으로 검증한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:infrastructure-design:59fce7d2ef78cc1fb8d39ca73c51ab6b33f3356bdcfa08d95276ae77b3842da3 -->

- brownfield의 기존 60초 token refresh margin과 server UTC clock을 pre-call usability predicate로 명시하고, gateway-only accessor의 preflight를 첫 public gateway call 내부이지만 첫 socket I/O 이전의 단계로 고정했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:infrastructure-design:d5cb2245513ec65289e5dead9563b7b2d7db4c1d7fe7e921504c70e234856693 -->

- whole-application 80% threshold를 새로 만들지 않고 changed-source JSON을 U1의 유일한 coverage 판정으로 삼았다. network 차단은 특정 CI provider 방화벽 대신 pytest process의 DNS/TCP default-deny fixture와 deliberate bypass probe로 증명한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:infrastructure-design:99553957a3f089746f967d2abd26a015cb6488fa92345545d2e6534b6c345d58 -->

- 실제 환경에서만 검증할 수 있는 NFR 성능 측정은 Build and Test의 자동화 timing으로 대체하지 않고 Performance Validation이 소유하며, 측정 전까지 Unverified로 유지한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:build-and-test:b2405aecb6af5a83f5760049533e506965acbab800da110e6bc48ae66a26b7c3 -->

- 고정된 manifest-union coverage 증거와 현재 workspace 전체 application coverage 결과는 출처와 범위가 다르므로 각각 보존하고 구분해 보고한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:build-and-test:2318e0968b35f30f7bc9e8617a3fa87cfdf5e7b59bb8d30c190288114dd7fc6c -->

## Guard Policy

<!-- Project-specific. Mode: strict, relaxed, or off. Strict here holds for every intent, whatever one person asks in chat; relaxed or off here applies to every intent whose policy came from its scope, unless the person sets another; changing this line changes it. A section under the retired Change Control heading, written by an earlier release, is still read. -->

## Deployment

<!-- Project-specific specialisation. -->

- 새 CI workflow나 provider를 만들지 않고 저장소 밖 기존 승격 경로가 실행할 test contract만 강화했다. 공급자 자동화는 U1 범위 밖으로 유지한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:infrastructure-design:e69524eebe763d05215b826e320a757b41a738ae71aa65396b13d21cb3c86bdb -->

## Code Style

<!-- Project-specific specialisation. -->

## Tech Stack

<!-- Technology choices locked for this project. -->

## Decided

<!-- Decisions made in earlier stages that should not be re-asked. -->
<!-- Format: DECIDED: [decision] (Stage [slug], [date]) -->

## Scope Overrides

<!-- Custom scope rules for this project. -->

## Forbidden

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: NEVER [behavior] (affirmed [date]) -->
<!-- Example: NEVER throw exceptions across service layer boundaries (affirmed 2026-05-17) -->

- NEVER 새 Agent나 별도 서비스를 만들거나 다른 저장소의 ITSM 내부 코드를 import·복사한다. (affirmed 2026-10-25)

- NEVER 액세스 토큰, client secret 또는 OpenAI API key를 모델 입력, function tool 결과, 로그 또는 오류 응답에 노출한다. (affirmed 2026-10-25)

- NEVER 제품 지침이나 도구 코드에 샘플 티켓 또는 특정 티켓 ID를 하드코딩한다. (affirmed 2026-10-25)

- NEVER 보이지 않는 티켓의 존재를 추론하거나 ITSM API가 부여하지 않은 권한을 로컬에서 확대한다. (affirmed 2026-10-25)

- NEVER 등록 결과가 불명확할 때 새 멱등 상태로 중복 생성을 시도하거나, 수정 충돌에서 최신 변경을 자동 덮어쓴다. (affirmed 2026-10-25)

## Mandated

<!-- Populated by practices-discovery affirmation gate. -->
<!-- Format: ALWAYS [behavior] (affirmed [date]) -->
<!-- Example: ALWAYS use Result<T,E> for fallible operations in service layer (affirmed 2026-05-17) -->

- ALWAYS 기존 OpenAI Agents SDK `Agent`와 `Runner`, 서버 측 사용자 세션, 사용자 위임 토큰 경계를 확장한다. (affirmed 2026-10-25)

- ALWAYS Agent에는 `ticket_read`, `ticket_write`, `ticket_update` 세 function tool만 노출한다. (affirmed 2026-10-25)

- ALWAYS `docs/itsm/integration-guide.md`와 `docs/itsm/openapi.json`을 계약 기준으로 삼아 ITSM API v2를 HTTP로 호출한다. (affirmed 2026-10-25)

- ALWAYS 권한과 티켓 가시성은 ITSM API에 맡기고, 등록·수정은 명시적 사용자 확인과 계약상 정합성 보호 뒤 실행한다. (affirmed 2026-10-25)

- ALWAYS 실제 OpenAI API를 호출하지 않는 자동화 테스트와 기존 전체 테스트를 통과시키고 README에 기능·실행·테스트 방법을 반영한다. (affirmed 2026-10-25)

- ALWAYS 기존 사용자 전환, 세션, 대화 이력, 고정 모델·reasoning 설정, 화면과 기존 API 동작을 보존한다. (affirmed 2026-10-25)

- ALWAYS 이번 기능은 `main` 기준의 짧은 기능 브랜치에서 작업하고 검증 후 squash merge한다. (affirmed 2026-10-25)

- ALWAYS `ticket_read` 최소 end-to-end 경로를 walking skeleton으로 먼저 연결하고 등록·수정 구현 전에 별도 확인한다. (affirmed 2026-10-25)

- ALWAYS 각 테스트 가능한 계층 구현 직후 해당 pytest 테스트를 작성·실행하고 마지막에 전체 회귀 테스트를 실행하는 `test-after` 순서를 따른다. (affirmed 2026-10-25)

- ALWAYS feature 범위에서 조직 기준인 80% line coverage floor를 충족한다. (affirmed 2026-10-25)

- ALWAYS 새 배포 인프라를 만들지 않고 기존 배포 경로를 유지하며 전체 자동화 테스트 통과를 승격 전 조건으로 둔다. (affirmed 2026-10-25)

- ALWAYS 현행 Python 3.13 관용구와 기존 모듈 경계를 유지한다. (affirmed 2026-10-25)

## Corrections

<!-- Project-specific corrections from human feedback. -->
<!-- Format: NEVER/ALWAYS [behavior] (learned [date]) -->
- 기존 Assistant, ITSM API v2, 사용자 위임 토큰, 비밀정보 비노출, 기존 동작 유지 조건은 이미 확인된 제약으로 취급했다. 질문은 추가 연동 계층, 규제, 일정, 환경 변경 허용 범위, 클라우드, 운영 규모, 조직적 장애물처럼 아직 확인되지 않은 타당성 요인에 집중했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:feasibility:c335093c5d27ca0a4e688dd286ecc9aa57b5611d7fc3c20552f2ff08e9211872 -->
- 승인된 상위 산출물이 최소 범위, Must Have, 제외 범위와 일정 제약을 이미 확정했으므로 재질문하지 않았다. 조회 범위의 깊이, 변경 전 사용자 확인, 전달 순서처럼 아직 결정되지 않은 범위 선택에만 질문을 집중했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:scope-definition:6b5bf3fbd820ec44560953d7a327034b61d3a64f825536c7109da49c38b0d38f -->
- 승인된 상위 산출물이 이미 의사결정자, 일정, 예산·조직 제약, 기술·보안 역량을 확정했으므로 이를 다시 묻지 않고 실행 팀 형태, 핵심 역할 구성, 협업 방식과 실제 역량 공백만 질문했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:team-formation:22080725840480e5ee9adadfaab210c6071e83cdeaceca723666fa922709c052 -->
- 새 화면과 화면 재설계는 범위 밖이지만 기존 대화 화면에 나타나는 조회 결과, 변경 확인, 오류 복구는 사용자 경험에 해당하므로 Rough Mockups를 생략하지 않았다. 산출물은 새 UI 레이아웃이 아니라 기존 채팅 안의 대화 상태와 시스템 상호작용 스케치로 제한한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:rough-mockups:3daef20f38b66462ba6fb5e0855a17de6654d639e4a249c65b2b90ad3d16db25 -->
- 승인된 이전 산출물에서 이해관계자 합의, 자원·일정 제약, Rough Mockups 승인, Market Research 생략 근거가 이미 확정됐다. 따라서 이 단계에서는 이를 다시 묻지 않고, 열린 RAID 위험을 Inception에 어떻게 인계할지만 확인한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:approval-handoff:21e56829cbe884346caeb7845ef80958944f1e58ec8aac56f6cb0d2ad1e97806 -->
- 모든 열린 위험을 Ideation 안에서 선해결하면 계약·코드 근거가 필요한 항목까지 추측으로 닫게 된다. 사용자가 선택한 대로 R-01~R-10을 Inception 요구사항·설계·테스트의 검증 의무로 이관하고, 필수 근거를 확보할 수 없을 때만 후속 진행을 중단한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:approval-handoff:46dfe2880c6f7c45e3240c135e3b0d7e038dd0c5697a4f71e6be217eaadf6d6f -->
- 전체 저장소 스캔 결과 기존 FastAPI·Agents SDK·서버 세션·위임 토큰·httpx 테스트 기반을 확장하는 경로가 확인됐다. 애플리케이션 코드는 변경하지 않았고, 구현의 핵심 경계는 서버 전용 ITSM capability, 안전한 오류 매핑, 등록 멱등성, 수정 `If-Match`다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:reverse-engineering:451b93c111fa3ca2ae2c1404f719f852922a35dbc88cc0d0c0ace7fa2faec890 -->
- 저장소는 현재 기술 패턴과 품질 도구 부재를 보여주지만 브랜치·통합 조각·테스트 작성 순서·실제 배포·새 품질 도구 도입에 관한 팀 의도는 증명하지 못한다. 따라서 다섯 관행 영역 모두 근거 기반 추천안을 제시하되 사람의 선택으로 확정한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:practices-discovery:0de4b6f8638e8ea7cc8be013e93782c9cb593795c117dea7d7a7850876b20e4b -->
- 이번 feature에 Ruff·Black·mypy를 새 의무로 추가하지 않고 현행 Python 관용구를 유지한다. 다만 도구 설정 부재가 품질 기준 면제를 뜻하지 않으므로, feature 범위의 80% line coverage floor와 전체 회귀 테스트는 후속 테스트 설계에서 측정·검증한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:practices-discovery:62dfcc2701dd03d66ad0ce7dcf5a7ff4cba327a5aec15690a40fb576914e7352 -->
- 승인된 상위 산출물과 ITSM API 계약이 조회 범위, 변경 전 확인, 권한·가시성, 멱등성, 충돌, 비밀정보 비노출과 회귀 기준을 이미 확정했다. 따라서 Requirements Analysis 질문은 이전 결정을 반복하지 않고 확인 결합 범위, 카탈로그 식별, 발생 시각, 토큰 만료, 재시도처럼 테스트 결과를 바꾸는 남은 경계에만 집중한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:requirements-analysis:4204ed392bab80c0b97b2ed542e57a01f12caa2c6025871e7d4a678038c02264 -->
- 위임 토큰 만료를 곧바로 재로그인으로 처리하는 이전 UX 표현 대신, 사용자가 선택한 대로 유효한 서버 세션에서는 기존 갱신 경로를 한 번 사용하고 갱신할 수 없을 때만 변경 미실행과 재로그인을 요구한다. 이는 기존 세션 동작을 보존하면서 서비스 토큰 대체와 만료 토큰 사용을 금지한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:requirements-analysis:853cb6471d8830cfed7c44f329af2289f2c815c50d2068e2646815659e7ebeff -->
- 기존 대화 화면의 조회·등록·수정처럼 사용자-facing 기능이 권한·확인·멱등성·충돌·오류 복구를 포함하면 User Stories를 실행하고 Given/When/Then으로 독립 검증한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:user-stories:fb8e3db6b8ab9cc12162eee741a2a3525fad06245e9ca7145d0f0a141d247697 -->
- 세 도구만으로 크게 묶거나 필드별로 지나치게 쪼개지 않고, 검색·목록과 ID 상세를 나누며 공통 복구·출시 준비를 독립 수직 스토리로 두어 사용자 가치와 walking skeleton을 함께 유지한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:user-stories:7ca630ca584cbba54d8d8f8806c50d23b7c4d38bdd4e30f617e3f3da96392ddc -->
- 새 화면·버튼·재설계가 범위 밖이면 Refined Mockups는 기존 대화 영역의 메시지 구조, 상태 전환, 오류 복구, 반응형·접근성 동작을 개발 가능한 수준으로 정교화한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:refined-mockups:98287b6616cb8cb635459911726bf58dd680422ea7f60bd7f0356f83a2de6e0a -->
- 기존 화면을 보존할 때는 새 버튼·breakpoint·픽셀 규칙 대신 확인 문구, 상태 전환, 긴 콘텐츠, live 알림을 구현과 테스트가 판정 가능한 텍스트 계약으로 상세화한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:refined-mockups:47c0da9a1db2b9fea8b5ac1a13c428d08ee48ddd62a37427a4770c8305a612eb -->
- [unit u1-ticket-read-skeleton] 일반 상세 조회와 수정 전 조회를 별도 typed port로 분리했다 (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:functional-design:afc78a0e87d59c5a9e1137909694b531877bd1c07892adaee16253f5d1ad85f1 -->
- R-17은 단순한 SQLite retry 문제가 아니라 같은 conversation의 Runner/history/presentation과 session-expiry cleanup이 공유해야 하는 단일 동시성 경계 문제로 해석했다. pre/post-Runner persisted-expiry 검사를 publication fence로 설계했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-design:118f7f622c453e93a3b6005ba5eacceac1eba8202e9d321befbf1887aca7ef0d -->
- 현재 단일-process 배포에서는 application per-conversation lock으로 직렬화한다. 다중 process 확장은 이번 Unit 범위에 넣지 않고 shared lock 또는 transaction 설계가 필요한 잔여 위험으로 유지한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-design:cc2aaced44083318b5f887a7c42a3aa6103a4c36960e1e9744517520a85113a7 -->
- 사용자의 Request Changes를 U1 기존 기능 전체 재구현이 아니라 R-17의 동일-lock lifecycle 보완과 교차 실행 회귀 추가로 제한했다. 이전 U1 완료 항목은 유지하고 계획 Step 17~18만 미완료 상태로 추가했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:code-generation:2b4f9918206ab9199c2f4d21335bacfc4c7a3a2a758a4fe4d2f0d608aaca88b7 -->
- 등록 결과 조정 조회가 실패하거나 존재 여부를 확정하지 못해도 전역 attempt count가 2 미만이면 같은 key·bytes로 마지막 CAS claim·POST를 허용하고, 두 번째 불명확 결과는 terminal ambiguous로 종료한다. 이는 AC2.1.5와 24시간 멱등 계약을 계약 경계에서 확정한 선택이다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:contract-design:65a8e016e06c829a58526be470bd943947aede95196a51db341cc07f24733c59 -->
- Contract Design에서 승인된 R-12~R-15는 traceability GAP가 아니라 B2의 delivery risk와 완료 증거로 수용했다. 결과 조회 operation은 권위 문서에서 확인될 때만 사용하고, 없으면 same-key/same-bytes replay와 terminal ambiguous 경로를 계획한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:delivery-planning:477cd9485dfd49f10bf4012fac59db4f13277f2451ddb061f16c2f01959c747e -->
- NFR3.2의 confirmation은 승인과 실행 권한 부여를 같은 연산으로 보지 않는다. U1은 분리된 confirm/consume_once CAS와 최소 일회성 evidence까지만 소유하고, 실제 mutation 권한은 U2·U3가 자체 state와 precondition에 결합한 뒤에만 성립한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-design:89c24d3b7a3a9c39ef3d6aca3930af9d5d252e95a783891dc5a3dff2100da695 -->
- consume 후 downstream bind 전 crash에서는 evidence 재발급보다 재검토·재확인을 택한다. 사용자 단계가 하나 늘지만 U2의 동일 attempt/idempotency key/request bytes를 보존하고 unbound POST를 막아 중복 생성 위험을 줄인다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-design:ad7023a30ed71664275f866e43dc750eb20e8f3b891f10b04e85a269ac7b5344 -->
- credential refresh는 identity boundary가 실행하되 정책 소유권은 TicketOperations에 남겼다. one-shot budget token과 remaining deadline을 narrow port로 전달해 dependency inversion을 추가하는 대신 gateway나 identity component의 독립 retry를 금지한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-design:5210b30c5b8609d568c909b954e00e88035061be9c1195e16225105aab691786 -->
- 이번 stage의 external surface는 새 티켓 API가 아니라 기존 chat API의 하위 호환 응답 계약이며, ITSM API v2는 Assistant가 소비하는 outbound provider 계약으로 다룬다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:contract-design:8622c1b9463115df604ebd97a9f6efd831e27ccccfbd4500509615a1762af68b -->
- U2와 U3의 병렬성을 유지하려면 공통 schema의 필드뿐 아니라 extension 등록 방식, 오류 taxonomy와 호환 규칙까지 U1 계약으로 고정해야 한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:contract-design:dd909352a0f075adc8c4d29fc52f7380e5e68d7c7f41ef7e0b9067b39fbdc69c -->
- 같은 프로세스 안의 Unit 경계에는 내부 HTTP나 event bus보다 typed Python port와 shared schema가 단순하고 테스트 가능하며, 새 서비스 금지와 기존 배포 유지 조건에도 맞는다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:contract-design:03ebb38432c3986f11cded6e54fb39958f481f5255ac6c504ab0880f4bf542e2 -->
- Contract Design 승인 시 수용된 R-16~R-18을 단순 면제가 아니라 B1~B3의 구현 전 교차 Unit 선행조건과 U4 통합 검증 의무로 해석했다. 저장소 소유권, lifecycle ordering, contract version/cutover 결정을 각 Bolt 완료 증거에 넣어 후속 구현이 모순을 조용히 선택하지 못하게 한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:delivery-planning:8d55ae903cf844b129f81899aa44ec9e9b1ec0cabec474eef74dafea8e5c8186 -->
- 승인된 관행과 Unit DAG가 `U1 → U2 → U3 → U4`의 직렬 능력 흐름, U1 walking skeleton, 단일 교차기능 팀을 이미 확정했으므로 이를 재질문하지 않고 경제적 휴리스틱·Bolt 크기·체크포인트·Bolt별 증거·조건부 외부 의존성만 열린 판단으로 분리했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:delivery-planning:485d31acfccd9e0f4e741335134ef22a8803e66073538763d49679dd5d3b9e74 -->
- U2와 U3는 DAG상 병렬 가능하지만, 사용자가 Unit당 한 Bolt·모든 Bolt 체크포인트를 선택했고 팀 관행이 등록 후 수정의 단일 흐름을 확정했으므로 `unit-major`·`serial`을 유지한다. 각 기능 Bolt는 관련 subset을 실행하고 전체 suite·80% coverage 판정은 U4에 둔다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:delivery-planning:555dfdf52ce8f8b41c8291d82a1bdff04ee676edcece93f09b7939305c8be233 -->
- [unit u1-ticket-read-skeleton] 수명주기 정리가 대화 이력을 건드리는 모든 경우에 Runner와 같은 conversation lock을 적용하고, lock 획득 뒤 사용자·세션·대화 binding을 재검증하도록 보강했다. Confirm과 consume 사이 crash로 남은 confirmed update는 정확한 소비·만료·수명주기 무효화 전까지 새 update 공개를 차단한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:functional-design:c6f58e24168f0bcaa778cb01d2d4e480c851b22326ec49ce919dd212c5eca4bc -->
- [unit u1-ticket-read-skeleton] refresh와 update publication 모두 cross-owner transaction으로 확장하지 않았다. Crash 뒤 두 번째 token exchange를 금지해 가용성보다 일회성 안전성을 우선하고, update는 U3 staged/active 수명주기와 U1 exact-old replacement를 분리해 각 namespace의 단일 소유권을 유지한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:functional-design:10c597b967173101d2bd5d8d9fc53ede75cdd630d31d54e6b6935a86696d6fcb -->
- [unit u1-ticket-read-skeleton] refresh reservation의 actor binding은 V1 필드를 늘리지 않고 서버 인증 opaque envelope로 검증하며, restart replay 차단은 U2 durable one-invocation claim이 담당하도록 했다. U1은 U2 저장소를 읽지 않고 envelope 검증과 단일 exchange·session commit만 담당한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:functional-design:de45b89560ad82aaeb129357a25ae67238f67e2fd718402ff60f6bb31cd5d53e -->
- lifecycle cleanup은 U1 revocable state만 제거하고 U2 durable ledger를 보존한다. consume 뒤 binding 전 crash에서는 자동 실행 대신 같은 attempt의 새 확인을 요구해 편의보다 중복 mutation 방지를 우선했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-requirements:6359707c1a66ca78beb157049278ccbf7de6f54c836c3791c0bf9ae35aa30cd3 -->
- [unit u1-ticket-read-skeleton] 사용자가 기존 산출물 유지를 선택했지만 현재 기능 계약과 충돌하는 항목은 검토 수선 범위에서만 보완했다. 기존 ServerSession credential field는 유일한 허용 persistence 경계로 유지하고, U1이 U2 storage를 읽는 대신 인증된 opaque reservation과 U2 durable replay gate를 사용한다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-requirements:e4d8f83204e1b9d41a2678bda55810eb77e83b6fb3fe4dcca6393ecad0cc3f80 -->
- architecture review에서 lifecycle coordinator와 identity/Runner component 사이의 역참조가 one-way dependency 주장과 충돌함을 확인했다. 별도 conversation-serialization port와 opaque lock-held context로 acquisition ownership과 consumer proof를 분리했다. (learned 2026-10-25) <!-- cid:261024-itsm-ticket-tools:nfr-design:479a90da5b2189d6311e1e7482f0a621b8998cfae8eaf681598b8e5fc79c32ba -->
