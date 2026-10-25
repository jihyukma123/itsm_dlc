# ITSM 티켓 도구 외부 의존성 지도

## Sources

- `docs/itsm/integration-guide.md`
- `docs/itsm/openapi.json`
- `inception/requirements-analysis/requirements.md`
- `inception/user-stories/stories.md`
- `inception/refined-mockups/mockups.md`
- `inception/domain-design/components.md`
- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-dependency.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/contract-design/contract-summary.md`
- `inception/practices-discovery/team-practices.md`
- `ideation/team-formation/team-assessment.md`
- `inception/delivery-planning/delivery-planning-questions.md`

## Dependency Policy

현재 구현 착수를 막는 외부 handoff나 선행 승인은 없다. 외부 의존성은 기존 계약·환경 경계를 소비하거나, 명확한 예외가 발생할 때만 활성화되는 조건부 gate로 관리한다. 새 서비스, 데이터 복제, CI/CD 또는 배포 인프라는 만들지 않는다.

## Dependency Map

| ID | 의존성 | 소유자 | 소비 Bolt | 현재 상태 | 예상 대기 | 활성화 조건 | 지연 시 대응 |
|---|---|---|---|---|---|---|---|
| ED-01 | ITSM API v2 계약 문서 | ITSM API 소유 팀 | B1~B3 | 사용 가능; idempotency-key 결과 조회 operation은 현재 문서에서 확인되지 않음 | 0 | 문서에 없는 결과 조회를 요구하거나 두 문서의 의미 충돌·operation 의미 불명확이 발생 | B2는 조회 불가 전제 same-key/same-bytes replay 계약을 사용하고, 새 조회가 필요하면 해당 Bolt를 정지해 typed 계약을 먼저 확보 |
| ED-02 | 기존 인증·위임 token 교환 환경 설정 | 기존 Assistant/ITSM 운영 | B1~B4 | 기존 경로 사용 | 0 | 개발·테스트 환경에서 기존 server-side 설정 누락 | 비밀을 출력하지 않고 설정 존재 여부만 진단, 기존 운영 경로 소유자에게 요청 |
| ED-03 | 내부 보안 정책 해석 | 내부 보안 책임자 | 발생 Bolt | 조건부 | 미확정 | delegated credential, 오류·로그 또는 retention 규칙이 문서만으로 판정 불가 | 해당 안전 결정만 보류하고 범위·영향·선택지로 자문 |
| ED-04 | 기존 배포 경로 | 저장소 밖 기존 배포 책임자 | B4 이후 | 변경 없음 | 미확정 | 실제 환경 승격을 요청할 때 | 새 pipeline을 만들지 않고 전체 자동화 증거와 README를 기존 절차에 인계 |
| ED-05 | NFR8 운영 측정 환경·대표 테스트 데이터 | 제품·운영 책임자 | B4 | 조건부; 자동화 절차와 기록 형식은 로컬에서 정의 가능 | 미확정 | 실제 환경 성능·운영 기준값을 판정할 때 | B4에서 재현 가능한 측정 절차·입력·결과 schema를 인계하고, 실제 운영 수치는 승인된 환경에서 별도 기록 |

## Non-Blocking Local Test Substitutes

- ITSM API v2: `httpx.MockTransport`로 request/response, retry, ETag, idempotency, safe-error 계약을 검증한다.
- OpenAI Agents SDK: FakeModel로 function tool schema와 tool-call loop를 검증한다.
- 실제 credential: 생성형 canary와 fake capability를 사용하며 실제 token을 fixture·로그에 기록하지 않는다.
- 운영 티켓 데이터: 생성형 fixture만 사용하고 특정 티켓 ID를 하드코딩하지 않는다.

이 대체 수단은 실제 API smoke를 자동화 suite에 포함한다는 뜻이 아니다. 실제 smoke는 명시적 credential과 운영 승인 아래 README에서 분리하며 기본 Construction verification command에는 포함하지 않는다.

## Escalation Contract

- 계약 충돌은 `integration-guide.md`와 `openapi.json`의 operation·schema·상태 코드를 함께 제시한다.
- 보안 자문은 비밀 원문 없이 data classification, retention, 노출 지점과 제안 완화를 전달한다.
- 외부 답변이 기존 scope나 contract를 바꾸면 암묵적으로 구현하지 않고 해당 상위 산출물과 Delivery Plan을 수정한다.
- R-16~R-18의 소유권·lifecycle·version 결정은 우선 내부 아키텍처 책임이다. ITSM 문서 의미나 운영 책임이 실제로 불명확할 때만 ED-01/ED-03 자문을 활성화한다.
- 응답 지연 중에는 차단되지 않은 다른 Bolt로 우회하지 않는다. 기록된 직렬 순서와 Unit ownership을 유지한다.

## Assumptions & Open Questions

- 현재 권위 문서에 idempotency-key 기반 생성 결과 조회 operation이 없다는 전제로 계획한다. 외부 소유 팀이 그런 operation을 제공한다고 확인하면 B2 구현 전에 Contract Design의 typed port와 outbound profile을 갱신한다.
- NFR8 실제 운영 수치는 현재 확정하지 않는다. B4 완료 범위는 측정 절차와 기록 형식의 재현성까지이며, 운영 환경 수치 채움은 ED-05가 활성화된 뒤 수행한다.
