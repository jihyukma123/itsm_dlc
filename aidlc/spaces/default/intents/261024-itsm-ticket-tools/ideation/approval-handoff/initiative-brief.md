# ITSM 티켓 도구 이니셔티브 브리프

## Go/No-Go 권고

**Go — 조건부 진행.** 현재 No-Go 차단 항목은 없다. `ticket_read`, `ticket_write`, `ticket_update`를 기존 ITSM Assistant에 추가하는 작업은 현재 코드와 ITSM API v2 계약으로 실현 가능하다. 다만 열린 RAID 위험 R-01~R-10은 Inception의 요구사항·설계·테스트 수용 근거로 이관하며, 비밀정보 비노출·권한 가시성·등록 멱등성·수정 충돌 보호 등 필수 근거를 확보하지 못하면 후속 진행을 중단한다.

## 의도와 사용자 문제

기존 ITSM Assistant 사용자는 티켓 조회·등록·수정을 위해 대화 흐름을 벗어나 별도 ITSM 화면으로 이동하거나 정보를 반복 입력해야 한다. 일반 사내 사용자와 서비스 데스크 담당자가 현재 Assistant 안에서 세 업무를 완료하고, 기존 ITSM 권한 범위 안에서 반복 업무 시간을 줄이는 것이 목표다.

성공은 다음 결과로 판단한다.

- 대표 조회·등록·수정 시나리오를 외부 ITSM 화면 전환 0회로 완료한다.
- 동일 조건에서 기존 화면과 Assistant 방식을 각 3회 수행했을 때 Assistant의 시나리오별 중앙 완료 시간이 더 짧다.
- 계약 정확성, 기존 기능 무회귀, 비밀정보 노출 0건, 실제 OpenAI 호출 없는 전체 자동화 테스트 통과를 증명한다.

근거: `ideation/intent-capture/intent-statement.md`, `ideation/intent-capture/stakeholder-map.md`.

## 시장·투자 판단

Market Research는 의도적으로 생략했다. 이번 작업은 외부 시장 진입이나 신규 제품 투자가 아니라 기존 내부 brownfield 제품의 명시된 기능 공백을 해소하는 확장이다. 투자 판단은 승인된 사용자 문제, ITSM 계약, 현재 코드·테스트 기반, 타당성 평가를 근거로 한다. 따라서 외부 시장 주장이나 경쟁사 가정은 이 브리프의 근거로 사용하지 않는다.

## 승인 범위

### 포함

| 백로그 | 능력 | 핵심 수용 경계 |
|---|---|---|
| IB-01 | 공통 안전 실행 경계 | 서버 세션과 사용자 위임 토큰, ITSM 권한·가시성 유지, 비밀정보 비노출, 기존 동작 무회귀 |
| IB-02 | `ticket_read` | ID 상세 또는 계약상 필터·정렬·커서 기반 검색·목록, 보이지 않는 티켓 비노출 |
| IB-03 | `ticket_write` | 계약상 등록 정보, 실행 전 명시적 확인, 동일 요청 중복 방지 |
| IB-04 | `ticket_update` | 허용 필드만 변경, 실행 전 명시적 확인, `If-Match` 기반 충돌 보호 |
| IB-05 | 검증과 안내 | 실제 OpenAI 없는 테스트, 기존 테스트 포함 전체 통과, 성과 측정, README 갱신 |

Agent에 노출되는 티켓 도구는 위 세 개가 전부다. ITSM 연동 계약의 기준은 `docs/itsm/integration-guide.md`와 `docs/itsm/openapi.json`이며 모든 업무 호출은 API v2 HTTP로 수행한다.

### 제외

- 티켓 삭제, 상태 전이, 담당자·담당 그룹 배정
- 첨부파일, 댓글, 작업 기록, 통계, 대량 내보내기
- 새 Agent, 별도 서비스, 새 화면 또는 기존 화면 재설계
- 다른 저장소의 ITSM 내부 코드 import 또는 복사
- 특정 티켓 ID나 샘플 티켓의 제품 코드·지침 하드코딩
- 기존 모델·reasoning 설정, 사용자 전환, 세션, 대화 이력 동작 변경
- 신규 인프라, 새 SLA, 별도 규제 체계

근거: `ideation/scope-definition/scope-document.md`, `ideation/scope-definition/intent-backlog.md`.

## 타당성과 핵심 제약

기존 Python/FastAPI 앱은 Agents SDK의 Agent·Runner·세션, 서버 사용자 세션, 위임 토큰 갱신, `httpx`, FakeModel과 MockTransport 테스트 기반을 보유한다. 새 서비스 없이 기존 Agent context와 ITSM 클라이언트를 확장할 수 있다.

반드시 지킬 실행 경계는 다음과 같다.

- 토큰과 secret은 서버 전용 context에만 존재하고 모델 입력, function tool 스키마·결과, 로그, 오류 응답에 포함하지 않는다.
- 권한과 티켓 가시성은 ITSM API의 판단을 그대로 사용하며 404 의미로 존재 여부를 추론하지 않는다.
- 등록은 요청 단위 멱등 상태를 유지하고, 결과가 불명확한 동일 요청에는 새 키를 만들지 않는다.
- 수정은 현재 `version`을 읽어 `If-Match`를 보내며 412에서 자동 덮어쓰기나 무조건 재시도를 하지 않는다.
- 오류는 허용된 code, HTTP 상태, 안전한 설명, request ID만 전달하고 원문 예외·헤더를 노출하지 않는다.
- 기존 37개 테스트를 기준선으로 유지하고 신규 테스트에서도 실제 OpenAI API를 호출하지 않는다.

근거: `ideation/feasibility/feasibility-assessment.md`, `ideation/feasibility/constraint-register.md`.

## 위험과 인계 조건

| 위험 묶음 | RAID 항목 | Inception에서 요구할 근거 |
|---|---|---|
| 비밀·인증 | R-01, R-02, R-06 | 서버 전용 capability 설계, 갱신/401 흐름, canary 기반 비노출 테스트 |
| 데이터 무결성 | R-03, R-04 | `If-Match` 충돌 계약, 동일 요청 멱등 상태 수명주기와 재시도 테스트 |
| 권한·응답 범위 | R-05, R-07 | 404 비추론, 페이지 한도와 커서 조건 검증 |
| 장애·회귀 | R-08, R-09 | timeout·429·안전한 재시도 정책, 기존 기능 및 정확히 세 도구 회귀 테스트 |
| 사용자 성과 | R-10 | 동일 입력·측정 경계·각 3회·시나리오별 중앙값의 측정 기록 |

모든 위험은 완화책과 검증 트리거를 갖고 있으나 아직 Open 상태다. 설계 또는 테스트 근거가 필수 조건을 충족하지 못하면 해당 후속 단계를 중단하고 제품 책임자에게 선택지를 제시한다.

## 대화 경험 개념

새 화면은 만들지 않는다. 기존 대화 화면에서 다음 상태만 명확히 표현한다.

`사용자 요청 → 처리 중 → 조회 결과/상세 또는 등록·수정 최종 요약 → 명시적 확인 → 안전한 결과`

인증 만료, 수정 충돌, 등록 결과 불명확 상태는 데이터 변경 여부와 다음 행동을 명확히 알린다. 상태 메시지는 기존 heading·landmark·키보드 초점을 유지하고, 일반 상태는 polite live region, 즉시 행동이 필요한 오류는 alert로 한 번만 알린다.

근거: `ideation/rough-mockups/wireframes.md`, `ideation/rough-mockups/user-flow.md`.

## 팀과 전달 계획

하나의 스트림 정렬형 교차기능 역할 팀이 전체 기능을 소유한다. 요청자/제품 책임자가 범위·우선순위와 단계 승인을 맡고, 전달·아키텍처·개발·보안·품질 역할이 공통 안전 경계부터 함께 작업한다. ITSM 운영 책임자는 계약 또는 운영 의미가 막힐 때 자문한다.

전달 순서는 `IB-01 공통 안전 경계 → IB-02 조회 → IB-03 등록 → IB-04 수정 → IB-05 통합 검증·README`다. 고정 납기나 추가 예산·조직 제약은 없으며 계약·보안·회귀 품질을 우선한다.

근거: `ideation/team-formation/team-assessment.md`, `ideation/team-formation/mob-composition.md`.

## Inception 진입 기준

- 승인된 의도, 범위와 IB-01~IB-05 사이의 추적성이 유지된다.
- API 계약, 현재 코드 구조와 테스트 관행을 Reverse Engineering에서 증거로 확정한다.
- 열린 위험 R-01~R-10을 요구사항·설계·테스트 수용 기준에 배치한다.
- 새로운 범위·서비스·인프라가 필요해지면 암묵적으로 추가하지 않고 제품 책임자의 결정을 받는다.
- 이 브리프와 `decision-log.md`가 제품 책임자의 Approval & Handoff 승인을 받는다.

## 승인

- [ ] 제품 책임자 Approval & Handoff 승인
- 승인 후 다음 단계: Reverse Engineering
