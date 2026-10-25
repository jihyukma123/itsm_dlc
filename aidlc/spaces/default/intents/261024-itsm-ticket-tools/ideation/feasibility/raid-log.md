# ITSM 티켓 도구 RAID 로그

## Risks

| ID | 위험 | 가능성 | 영향 | 완화·대응 | 검증/트리거 | 상태 |
|---|---|---:|---:|---|---|---|
| R-01 | 위임 토큰이나 다른 비밀값이 Agent 모델 입력·도구 결과·로그에 섞일 수 있음 | 중 | 매우 높음 | 서버 전용 context/capability, 비밀 필드 `repr=False`, 헤더·원본 예외 비직렬화, redaction 보강 | FakeModel 입력·도구 출력·로그·HTTP 응답의 canary 검사 | Open |
| R-02 | 토큰이 Agent 실행 또는 다단계 도구 호출 중 만료될 수 있음 | 중 | 높음 | 기존 `itsm_token_for()` 갱신 경로 재사용과 401 처리 | 만료 임박 토큰 fixture | Open |
| R-03 | 상세 조회 후 PATCH 전에 다른 변경이 발생해 갱신을 덮어쓸 수 있음 | 중 | 높음 | `If-Match` 사용, 412에서 자동 덮어쓰기·무조건 재시도 금지 | version conflict 계약 테스트 | Open |
| R-04 | Agent 또는 네트워크 재시도로 동일 티켓이 중복 등록될 수 있음 | 중 | 높음 | 요청 단위 멱등키를 생성하고 동일 요청 재시도에서 유지 | 동일 키·동일/상이 본문 테스트 | Open |
| R-05 | 권한 없는 티켓의 존재 여부가 오류 설명으로 노출될 수 있음 | 낮음 | 높음 | API의 404 의미 유지, 권한 추측 금지 | requester 가시성 테스트 | Open |
| R-06 | ITSM 오류의 `detail` 또는 예외 문자열이 내부정보를 모델·사용자에게 전달할 수 있음 | 중 | 높음 | 허용 목록 기반 오류 DTO, code/status/request_id 중심 응답 | 악의적 오류 본문과 비밀 canary 테스트 | Open |
| R-07 | 넓은 검색 결과가 모델 context를 과도하게 차지할 수 있음 | 중 | 중 | 기본 limit 유지, 최대 100 강제, 페이지 명시, 필요한 필드 중심 반환 | 최대 limit·cursor 테스트 | Open |
| R-08 | ITSM 장애·시간 초과·429가 대화 실패로 이어질 수 있음 | 중 | 중 | 기존 timeout, 안전한 재시도 정책, `Retry-After` 안내 | MockTransport 장애·429 테스트 | Open |
| R-09 | 도구 추가가 기존 대화 이력·사용자 전환·고정 모델 동작을 깨뜨릴 수 있음 | 낮음 | 높음 | 변경 범위 최소화, 기존 37개 테스트와 Agent 구성 회귀 테스트 | 전체 테스트 스위트 | Open |
| R-10 | 완료 시간 비교가 입력·시작·종료 조건 차이로 왜곡될 수 있음 | 중 | 중 | 동일 시나리오·입력·측정 경계, 각 방식 3회, 시나리오별 중앙값 사용 | 인수 측정 기록 검토 | Open |

## Assumptions

| ID | 가정 | 근거 | 틀릴 경우 영향 | 확인 시점 | 상태 |
|---|---|---|---|---|---|
| A-01 | 현재 Assistant와 ITSM API v2 사이에 필수 게이트웨이·별도 인증 시스템이 없다. | feasibility Q1 | 네트워크·인증 설계 재검토 | 설계 시작 전 환경 확인 | Accepted |
| A-02 | 기존 사내 보안 정책 외 별도 규제·레지던시 요구가 없다. | feasibility Q2 | 데이터 처리·감사 요구 추가 | 배포 전 보안 확인 | Accepted |
| A-03 | 고정 납기가 없으며 계약·보안·회귀 품질을 우선할 수 있다. | feasibility Q3 | 범위 또는 테스트 깊이 재협상 | 전달 계획 수립 | Accepted |
| A-04 | 기존 설정과 배포 구조만으로 기능을 제공할 수 있다. | feasibility Q4, 현재 앱 구조 | 환경 변수·네트워크 변경 승인 필요 | 구현 설계 | Accepted |
| A-05 | 별도의 AWS 계정·리전 결정이 필요 없다. | feasibility Q5 | 인프라 설계 단계 재개 | 배포 계획 | Accepted |
| A-06 | 처리량·가용성은 현재 Assistant 기준을 유지한다. | feasibility Q6 | NFR와 성능 시험 범위 확대 | NFR 단계 | Accepted |
| A-07 | 추가 예산·조직 승인·변경 동결이 없다. | feasibility Q7 | 일정과 승인 경로 변경 | 전달 계획 | Accepted |
| A-08 | 저장소의 Python/FastAPI/Agents SDK/httpx/pytest 패턴을 구현팀이 유지할 수 있다. | 현재 코드 구조 | 교육·검토 비용 증가 | 팀 구성 단계 | Open |

## Issues

| ID | 현재 이슈 | 영향 | 조치 | 상태 |
|---|---|---|---|---|
| I-01 | `AgentUserContext`에는 ITSM 호출 capability나 갱신 가능한 위임 토큰 접근 경로가 없다. | 도구가 현재 사용자를 대신해 업무 API를 호출할 수 없음 | 비밀값을 모델과 분리한 서버 측 실행 context 설계 | Open |
| I-02 | `ItsmAuthClient`는 인증·디렉터리만 지원하고 티켓 API 메서드가 없다. | 세 도구 미구현 | 동일 클라이언트에 v2 티켓 호출과 안전한 오류 매핑 추가 | Open |
| I-03 | Agent의 `TOOLS`가 비어 있고 현재 테스트는 “도구 없음”을 기대한다. | 신규 기능과 테스트 기준 불일치 | 정확히 세 도구 등록 후 기존 기대를 새 계약으로 갱신 | Open |
| I-04 | shell 전역 PATH에는 pytest가 없고 프로젝트 가상환경에만 있다. | 잘못된 실행 명령은 실패 | README에 가상환경 활성화 또는 `.venv/bin/pytest` 명시 | Open |

## Dependencies

| ID | 의존성 | 필요 조건 | 소유 경계 | 실패 시 대응 | 상태 |
|---|---|---|---|---|---|
| D-01 | ITSM API v2 | 문서화된 티켓·인증 엔드포인트와 스키마 유지 | 외부 ITSM 시스템 | problem code에 따른 안전한 실패, 계약 테스트 갱신 | Active |
| D-02 | 서버 측 사용자 세션 | 사용자·conversation·위임 토큰이 세션에서 복원됨 | 현재 앱 | 기존 session 회귀 테스트 유지 | Active |
| D-03 | 위임 토큰 교환·갱신 | `token_exchange` 허용, 만료 전 재발급 가능 | 현재 앱 + ITSM | 401/invalid grant 안전 처리 | Active |
| D-04 | OpenAI Agents SDK | `function_tool`, typed run context, Runner 세션 동작 | Python 의존성 | 고정 설치 버전에서 구성·스키마 테스트 | Active |
| D-05 | `httpx` | 비동기 HTTP, timeout, MockTransport | Python 의존성 | 공통 클라이언트와 테스트 transport 재사용 | Active |
| D-06 | FakeModel·Fake ITSM 테스트 기반 | 실제 OpenAI 없이 tool call과 HTTP 계약 재현 | 테스트 코드 | fixture를 티켓 엔드포인트까지 확장 | Active |

## 즉시 차단 항목

현재 No-Go 차단 항목은 없다. I-01부터 I-03은 설계·구현 범위에서 해소 가능한 선행 작업이며 R-01·R-03·R-04에 대한 테스트가 통과하기 전에는 완료로 판정하지 않는다.
