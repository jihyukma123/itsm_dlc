# ITSM 티켓 도구 제약 등록부

## 상태 정의

- **확정**: 사용자 요청, 승인된 의도 또는 ITSM 계약으로 고정된 제약
- **추천 가정**: 사용자가 추천안 선택을 위임하여 현재 계획에 채택한 제약
- **검증 필요**: 설계·구현·테스트에서 증거를 남겨야 하는 제약

## 제약 목록

| ID | 분류 | 제약 | 출처 | 영향 및 대응 | 상태 |
|---|---|---|---|---|---|
| CON-01 | 범위 | 기존 Agent와 Runner를 확장하고 새 에이전트나 별도 서비스를 만들지 않는다. | 사용자 요청, `intent-statement.md` | 앱 내부 도구·HTTP 클라이언트 확장으로 제한 | 확정 |
| CON-02 | 도구 계약 | Agent에 노출되는 티켓 도구는 `ticket_read`, `ticket_write`, `ticket_update` 정확히 세 개다. | 사용자 요청 | 카탈로그 조회나 토큰 도구를 별도 function tool로 노출하지 않음 | 확정 |
| CON-03 | 연동 | ITSM 연동 기준은 `docs/itsm/integration-guide.md`와 `docs/itsm/openapi.json`이다. | 사용자 요청 | 내부 저장소 코드 재사용 없이 HTTP 구현과 계약 테스트 작성 | 확정 |
| CON-04 | API 버전 | 모든 티켓 업무 호출은 `/api/v2/*`를 사용한다. | 사용자 요청, integration guide §1·§3 | v1 경로와 형식은 구현하지 않음 | 확정 |
| CON-05 | 인증 | 현재 로그인 사용자의 서버 측 세션과 사용자 위임 토큰을 사용한다. | 사용자 요청, integration guide §1.2 | 모델 인자가 아닌 서버 context에서 토큰 제공; 만료 전 갱신 | 확정 |
| CON-06 | 인가·가시성 | 권한과 티켓 가시성의 최종 판단은 ITSM API에 맡긴다. | 사용자 요청, integration guide §2·§2.1 | 로컬 역할로 결과를 확대하거나 404를 추론하지 않음 | 확정 |
| CON-07 | 비밀 보호 | 액세스 토큰, 클라이언트 secret, OpenAI API key를 모델 입력, 도구 결과, 로그, 오류 응답에 노출하지 않는다. | 사용자 요청, `intent-statement.md` | context 분리, 안전한 오류 매핑, 비밀값 부재 테스트 | 확정 |
| CON-08 | 조회 | ID가 있으면 상세, 없으면 검색·목록을 수행하며 커서 페이지네이션과 계약 필터를 따른다. | 사용자 요청, integration guide §3.1·§3.4, OpenAPI | 하나의 `ticket_read`가 두 모드를 명확히 구분 | 확정 |
| CON-09 | 등록 | 필수 등록 필드 7개와 허용된 선택 필드만 전송하고 서버 관리 필드는 보내지 않는다. | integration guide §3.4, `TicketCreateIn` | enum·길이·시간대 검증; 추가 필드 금지 | 확정 |
| CON-10 | 등록 멱등성 | 티켓 등록 재시도는 중복 생성을 막아야 한다. | integration guide §3.4 | 비밀정보 없는 요청 단위 `Idempotency-Key` 사용 | 검증 필요 |
| CON-11 | 수정 | `TicketPatchIn`의 허용 필드만 처리하고 빈 수정은 거부한다. | 사용자 요청, OpenAPI `TicketPatchIn` | 선택적 PATCH; 영향 범위는 `impact_note`로 매핑 | 확정 |
| CON-12 | 동시성 | 수정은 현재 버전의 `If-Match`를 반드시 전송하고 충돌 시 덮어쓰지 않는다. | integration guide §3.4 | 선행 상세 조회 또는 동등한 버전 확보; 412 안전 처리 | 확정 |
| CON-13 | 시간 | `occurred_at`과 시간 필터는 시간대를 포함한 ISO 8601이어야 한다. | integration guide §3.1, OpenAPI | tool 스키마와 테스트에서 시간대 필수 검증 | 확정 |
| CON-14 | 오류 | problem+json의 안정적 code를 기준으로 안전하게 매핑하고 헤더·원본 예외는 노출하지 않는다. | integration guide §3.2 | 대표 오류 계약 및 비밀값 부재 테스트 | 검증 필요 |
| CON-15 | 호출 제한 | 커서 조건 불일치와 분당 300회 제한 및 `Retry-After`를 존중한다. | integration guide §3.1 | 도구 설명·클라이언트·테스트에 반영 | 확정 |
| CON-16 | 기존 동작 | 사용자 전환, 세션, 대화 이력, 고정 모델·reasoning 설정, 화면과 기존 API를 유지한다. | 사용자 요청, `intent-statement.md` | 관련 파일 변경 최소화 및 회귀 테스트 유지 | 확정 |
| CON-17 | 테스트 | 실제 OpenAI API 없이 신규 자동화 테스트를 추가하고 기존 테스트도 통과시킨다. | 사용자 요청 | FakeModel과 MockTransport 사용; 기준선 37개 통과 | 확정 |
| CON-18 | 데이터 | 샘플 티켓이나 특정 티켓 ID를 지침 또는 도구 코드에 하드코딩하지 않는다. | 사용자 요청 | 테스트 fixture에만 합성 데이터 사용 | 확정 |
| CON-19 | 문서화 | 구현 내용, 설정, 실행과 테스트 방법을 README에 반영한다. | 사용자 요청 | 완료 기준에 README 검증 포함 | 확정 |
| CON-20 | 환경 | 기존 애플리케이션 설정과 배포 구조 안에서만 변경하고 새 인프라를 만들지 않는다. | feasibility Q1·Q4·Q5 | 기존 `Settings`, 앱 state, 클라이언트 수명주기 재사용 | 추천 가정 |
| CON-21 | 일정 | 고정 납기보다 품질 기준 충족을 우선한다. | feasibility Q3 | 계약·보안·회귀 검증을 생략하지 않음 | 추천 가정 |
| CON-22 | 규제 | 별도 규제는 식별되지 않았고 기존 사내 보안 정책을 적용한다. | feasibility Q2 | 최소권한·비밀 보호 유지 | 추천 가정 |
| CON-23 | 신뢰성 | 별도 처리량·가용성 목표 없이 기존 Assistant 운영 기준을 유지한다. | feasibility Q6 | 새 SLA를 만들지 않고 API 제한·시간 제한 준수 | 추천 가정 |
| CON-24 | 조직 | 식별된 추가 예산·조직 제약은 없다. | feasibility Q7 | 별도 승인·조달을 계획하지 않음 | 추천 가정 |
| CON-25 | 사용자 성과 | 대표 조회·등록·수정 시나리오 모두 외부 ITSM 화면 전환 0회로 완료한다. | `intent-statement.md`, review R-01 | 자동화된 인수 시나리오로 검증 | 확정 |
| CON-26 | 시간 성과 | 각 대표 시나리오를 동일 조건에서 양 방식으로 3회 수행했을 때 Assistant의 시나리오별 중앙 완료 시간이 기존 방식보다 짧아야 한다. | `intent-statement.md`, feasibility Q8, review R-04 | 동일 입력·시작/종료 조건을 사용해 결과 기록 | 확정 |

## 상충 및 모호성 검토

- 사용자 요청과 추천 가정 사이의 직접적인 상충은 없다.
- “영향 범위”는 등록·수정 모두 OpenAPI의 `impact_note`로 해석한다.
- `ticket_update`에서 서비스 변경은 요청되지 않았고 `TicketPatchIn`에도 없으므로 지원하지 않는다.
- 상태 전이, 담당자 배정, 댓글, 첨부, 삭제는 첫 버전 범위에 포함하지 않는다.
- 사람 팀의 숙련도 정보는 제공되지 않았다. 다만 저장소가 이미 Python/FastAPI, Agents SDK, `httpx`, pytest 패턴을 갖춰 구현 불확실성은 낮다.
- 검토 R-02의 근거 없는 “1단계 감소”와 R-03의 근거 없는 정량 목표 유보는 제약으로 채택하지 않는다.
