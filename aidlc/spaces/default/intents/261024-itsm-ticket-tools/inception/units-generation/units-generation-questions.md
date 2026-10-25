# Units Generation 질문

## Sources

- `inception/domain-design/components.md`
- `inception/domain-design/decisions.md`
- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `aidlc/spaces/default/memory/team.md`
- `aidlc/spaces/default/memory/project.md`

## Q1. Unit 경계 전략

기존 단일 FastAPI 배포 안에서 구현 단위를 어떤 기준으로 나눌까요?

- A. **수직 기능 단위 (Recommended)** — 공통 안전 경계를 포함한 조회 walking skeleton, 등록, 수정, 출시 검증으로 나누어 각 단위가 사용자 가치를 독립 검증하게 한다.
- B. 컴포넌트 단위 — Gateway, Session, TicketOperations, Agent, Presentation을 각각 별도 Unit으로 나눈다.
- C. 계층 단위 — transport, domain, application, presentation 순으로 나눈다.
- D. 단일 Unit — 모든 기능을 하나의 큰 Unit으로 묶는다.
- E. 배포 대상 단위 — 현재 단일 배포이므로 하나의 runtime Unit과 문서 Unit으로만 나눈다.
- X. Other (please specify)

[Answer]: A. **수직 기능 단위 (Recommended)** — 공통 안전 경계를 포함한 조회 walking skeleton, 등록, 수정, 출시 검증으로 나누어 각 단위가 사용자 가치를 독립 검증하게 한다.

## Q2. Unit 세분성

수직 기능 단위를 어느 정도 크기로 구성할까요?

- A. **중간 크기 4개 (Recommended)** — `ticket_read` 통합 조각, `ticket_write`, `ticket_update`, 전체 출시 검증·문서화로 나눈다.
- B. 굵은 3개 — 조회, 등록·수정, 출시 검증으로 나눈다.
- C. 세밀한 6개 이상 — 공통 기반, 목록, 상세, 등록, 수정, 검증을 각각 나눈다.
- D. 최소 2개 — 모든 런타임 변경과 출시 검증으로 나눈다.
- E. 스토리별 6개 — US1.1부터 US5.1까지 정확히 한 Unit씩 둔다.
- X. Other (please specify)

[Answer]: A. **중간 크기 4개 (Recommended)** — `ticket_read` 통합 조각, `ticket_write`, `ticket_update`, 전체 출시 검증·문서화로 나눈다.

## Q3. 의존성과 병렬성

Unit 간 topology는 어떻게 둘까요?

- A. **조회 skeleton 뒤 등록·수정 병렬 가능 (Recommended)** — 등록과 수정은 공통 조회·세션·도구 경계에만 의존하고 서로 직접 의존하지 않으며, 출시 검증이 둘을 모두 의존한다.
- B. 완전 직렬 — 조회 → 등록 → 수정 → 출시 검증으로 연결한다.
- C. 최대 병렬 — 조회·등록·수정을 모두 독립 Unit으로 두고 마지막에 통합한다.
- D. 등록 우선 — 공통 기반 뒤 등록 → 수정, 조회를 별도 병렬로 둔다.
- E. 수정 우선 — 공통 기반 뒤 수정 → 등록, 조회를 별도 병렬로 둔다.
- X. Other (please specify)

[Answer]: A. **조회 skeleton 뒤 등록·수정 병렬 가능 (Recommended)** — 등록과 수정은 공통 조회·세션·도구 경계에만 의존하고 서로 직접 의존하지 않으며, 출시 검증이 둘을 모두 의존한다.

## Q4. Unit 사이 연동 계약

같은 프로세스 안의 Unit들은 어떤 계약으로 연결할까요?

- A. **명시적 내부 Python 인터페이스와 owner-scoped SQLite schema (Recommended)** — typed 요청·결과, 요청 범위 capability, Unit별 versioned durable state를 사용하고 새 외부 API나 이벤트 버스를 만들지 않는다.
- B. 기존 클래스에 직접 메서드를 추가하고 별도 내부 계약을 두지 않는다.
- C. 내부 HTTP API를 새로 만들어 Unit 사이를 연결한다.
- D. 비동기 이벤트와 queue를 추가한다.
- E. 공유 전역 상태와 dictionary로 연결한다.
- X. Other (please specify)

[Answer]: A. **명시적 내부 Python 인터페이스와 owner-scoped SQLite schema (Recommended)** — typed 요청·결과, 요청 범위 capability, Unit별 versioned durable state를 사용하고 새 외부 API나 이벤트 버스를 만들지 않는다.

## Q5. 배포 모델

각 Unit의 결과를 어떻게 배포 가능한 형태로 취급할까요?

- A. **기존 단일 FastAPI 배포에 embedded (Recommended)** — 런타임 Unit은 `library`, 최종 검증·문서 Unit은 `packaging`으로 표시하되 모두 한 애플리케이션으로 배포한다.
- B. 각 Unit을 독립 서비스로 배포한다.
- C. 조회만 독립 서비스, 나머지는 기존 앱에 둔다.
- D. 하이브리드 worker를 추가해 변경 작업을 분리한다.
- E. 배포 모델을 후속 단계까지 미정으로 둔다.
- X. Other (please specify)

[Answer]: X. 기존 단일 FastAPI 배포에 모두 embedded한다. U1~U3는 `library`로 분류하고, U4는 통합·회귀·문서 acceptance 책임이 `packaging` 정의와 맞지 않으므로 kind를 생략해 전체 설계 산출물 matrix를 적용한다.

## Q6. Ledger-first 등록 상태의 Unit 소유권

Domain Design에서 확정한 ledger-first 등록 원장과 U1 확인 계약을 Unit 사이에 어떻게 배치할까요?

- A. U1은 기존 공개 pending-review·`consume_once` 계약만 소유하고, U2가 `ticket_create_attempts`와 confirmation evidence 결합, 전역 attempt budget, CAS claim·복구를 소유한다. U1 schema 변경이나 cross-owner transaction은 추가하지 않는다. (Recommended)
- B. U1이 `ticket_create_attempts`까지 소유하고 U2는 U1 transaction port로만 등록한다.
- C. U1·U2가 create ledger schema를 공동 소유한다.
- X. Other (please specify)

[Answer]: A. U1은 기존 공개 pending-review·`consume_once` 계약만 소유하고, U2가 `ticket_create_attempts`와 confirmation evidence 결합, 전역 attempt budget, CAS claim·복구를 소유한다. U1 schema 변경이나 cross-owner transaction은 추가하지 않는다. (Recommended)

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- 기존 단일 FastAPI 배포 안에서 공통 안전 경계를 포함한 수직 기능 단위로 나눈다.
- Unit은 `ticket_read` walking skeleton, `ticket_write`, `ticket_update`, 전체 출시 검증·문서화의 4개로 구성한다.
- 첫 Unit은 서버 세션부터 Agent function tool, 사용자 위임 ITSM HTTP, 정제된 결과와 FakeModel/MockTransport 검증까지 실행 가능한 통합 조각이다.
- 등록과 수정 Unit은 조회 skeleton의 공통 경계에 의존하지만 서로 직접 의존하지 않아 병렬 개발할 수 있고, 출시 검증 Unit은 앞선 세 Unit을 모두 의존한다.
- Unit 사이에는 typed 내부 Python 인터페이스, 요청 범위 capability와 owner-scoped versioned SQLite 상태 계약을 사용하며 새 외부 API나 이벤트 버스를 만들지 않는다.
- U1은 공개 pending-review·`consume_once` 계약과 공통 cursor/presentation 기반만 소유한다. U2는 별도 `ticket_tools_create_v1.ticket_create_attempts`에서 ledger-first 준비, confirmation evidence 결합, 전역 최대 2회 POST 예산, CAS claim·복구를 소유한다. U1 schema 변경이나 cross-owner transaction port는 추가하지 않는다.
- U1~U3는 `library`로 분류하고 U4는 kind를 생략해 전체 설계 산출물 matrix를 적용한다. 모든 결과는 기존 FastAPI 애플리케이션 하나로 배포한다.
- 각 기능 Unit은 자신의 계층별 테스트를 구현 직후 실행하고, 최종 Unit은 전체 회귀·80% coverage·README·성과 측정 절차를 통합 검증한다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
