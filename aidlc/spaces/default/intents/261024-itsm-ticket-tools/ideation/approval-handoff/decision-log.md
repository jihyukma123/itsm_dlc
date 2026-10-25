# Ideation 결정 로그

## 목적

이 문서는 ITSM 티켓 도구 이니셔티브의 Ideation 단계에서 확정한 결정을 하나의 인계 기록으로 묶는다. 상세 근거는 각 Source 산출물에 있으며, 이후 단계는 이 결정을 임의로 확대하거나 축소하지 않는다.

## 결정 목록

| ID | 결정 | 상태 | 근거 / Source | 후속 영향 |
|---|---|---|---|---|
| DEC-01 | 대화 안에서 조회·등록·수정을 완료하고, 반복 시간을 줄이며, 기존 ITSM 권한 안에서 안전하게 실행하는 세 목표를 동등하게 추구한다. | Approved | `intent-capture/intent-statement.md` | 기능·보안·사용자 성과를 함께 완료 기준으로 사용 |
| DEC-02 | 대상 사용자는 일반 사내 사용자와 서비스 데스크 담당자이며, 제품 책임자가 최종 결정한다. | Approved | `intent-capture/stakeholder-map.md` | 권한 판단은 사용자 역할을 로컬에서 확대하지 않고 ITSM에 위임 |
| DEC-03 | Market Research를 생략하고 내부 사용자 문제, 계약, 코드·테스트 근거로 투자 판단한다. | Approved | workflow skip, `approval-handoff-questions.md` | 외부 시장·경쟁사 주장을 요구사항 근거로 사용하지 않음 |
| DEC-04 | 기존 Agent와 Runner, 서버 세션, 사용자 위임 토큰을 확장하며 새 Agent나 별도 서비스를 만들지 않는다. | Approved | `scope-definition/scope-document.md`, CON-01 | brownfield 구조 보존을 Reverse Engineering에서 확인 |
| DEC-05 | Agent에 노출하는 티켓 도구는 `ticket_read`, `ticket_write`, `ticket_update` 정확히 세 개다. | Approved | 사용자 요청, CON-02 | 토큰·카탈로그 등의 별도 function tool 추가 금지 |
| DEC-06 | ITSM 계약 기준은 두 문서이며 모든 티켓 업무는 API v2 HTTP로 호출한다. | Approved | CON-03, CON-04 | 다른 저장소 내부 코드 import·복사 금지, 계약 테스트 필요 |
| DEC-07 | `ticket_read`는 ID 상세 또는 계약상 전체 목록 필터·정렬·커서 검색을 제공한다. | Approved | IB-02, CON-08 | 404 비추론, limit·cursor 검증 필요 |
| DEC-08 | `ticket_write`는 계약상 필수·선택 필드만 사용하고 최종 요약과 명시적 확인 후 실행하며 중복을 방지한다. | Approved | IB-03, CON-09, CON-10 | 요청 단위 멱등 상태 설계와 불명확 결과 복구 필요 |
| DEC-09 | `ticket_update`는 허용 필드만 처리하고 최종 요약과 명시적 확인 후 `If-Match`로 실행한다. | Approved | IB-04, CON-11, CON-12 | 빈 수정 거부, 412 충돌 시 덮어쓰기·자동 재시도 금지 |
| DEC-10 | 사용자 위임 토큰과 모든 secret은 서버 전용 실행 context에 두며 모델·결과·로그·오류에 노출하지 않는다. | Approved | CON-05~CON-07, CON-14 | 안전한 오류 DTO와 canary 비노출 테스트 필요 |
| DEC-11 | 권한과 가시성의 최종 판단은 ITSM API에 맡긴다. | Approved | CON-06 | 로컬 권한 확대와 보이지 않는 티켓 존재 추론 금지 |
| DEC-12 | 사용자 전환, 세션, 대화 이력, 고정 모델·reasoning, 화면과 기존 API 동작을 유지한다. | Approved | CON-16 | 변경 범위 최소화와 회귀 테스트 필수 |
| DEC-13 | 테스트는 FakeModel과 MockTransport를 사용해 실제 OpenAI API 없이 수행하고 기존 37개 테스트도 함께 통과시킨다. | Approved | CON-17, feasibility baseline | 신규 계약·보안·도구 통합 테스트와 전체 회귀 실행 |
| DEC-14 | 특정 티켓 ID와 샘플 티켓은 제품 코드·지침에 하드코딩하지 않고 README에 기능·설정·실행·테스트 방법을 반영한다. | Approved | CON-18, CON-19 | 합성 데이터는 테스트 fixture에만 사용 |
| DEC-15 | 첫 릴리스는 IB-01~IB-05 전체를 Must로 두고 공통 안전 경계, 조회, 등록, 수정, 통합 검증 순으로 전달한다. | Approved | `scope-definition/intent-backlog.md` | 선행 안전 경계 없이 쓰기 능력을 독립 추진하지 않음 |
| DEC-16 | 새 화면을 만들지 않고 기존 대화에서 조회, 확인, 성공·오류·인증 만료·충돌·등록 결과 불명확 상태를 표현한다. | Approved | `rough-mockups/wireframes.md`, `rough-mockups/user-flow.md` | 접근성 semantics와 복구 흐름을 요구사항·테스트에 반영 |
| DEC-17 | 하나의 교차기능 역할 팀이 전체 기능을 소유하고 ITSM 운영·보안은 계약·정책 해석이 막힐 때 자문한다. | Approved | `team-formation/team-assessment.md` | 추가 상시 팀이나 외부 서비스 없음 |
| DEC-18 | 고정 납기, 추가 예산·조직 제약, 신규 인프라·SLA는 두지 않고 계약·보안·회귀 품질을 우선한다. | Approved | CON-20~CON-24 | 품질 근거를 일정 때문에 생략하지 않음 |
| DEC-19 | 열린 위험 R-01~R-10을 Inception의 요구사항·설계·테스트 검증 의무로 이관하고, 필수 근거를 확보할 수 없을 때만 중단한다. | Confirmed | `approval-handoff-questions.md` Q1 | 위험은 자동 종료하지 않으며 downstream 수용 근거로 추적 |
| DEC-20 | 현재 No-Go 차단 항목은 없으므로 조건부 Go를 권고한다. | Pending gate | `feasibility/feasibility-assessment.md`, `feasibility/raid-log.md`, `initiative-brief.md` | Approval & Handoff 승인 후 Reverse Engineering 진입 |

## 보류 또는 거절된 대안

- 모든 열린 위험을 Ideation에서 먼저 닫는 안은 계약·코드 근거 없이 위험을 형식적으로 종료할 우려가 있어 채택하지 않았다.
- 보안 위험만 먼저 닫는 안은 데이터 무결성·회귀·사용자 성과 위험을 추적에서 분리하므로 채택하지 않았다.
- 티켓 삭제, 상태 전이, 담당자 배정, 첨부·댓글·작업 기록, 통계·내보내기, 새 화면·서비스·인프라는 첫 릴리스 범위에서 제외했다.
- 근거가 없던 “조작 단계 1단계 감소”와 “정량 목표 유보”는 성공 기준으로 채택하지 않았다.

## 열린 검증 의무

결정 자체의 미해결 항목은 없다. 다음 증거는 Inception 이후 확보해야 하며, 실패 시 관련 결정의 구현 완료를 승인하지 않는다.

- ITSM 계약과 실제 코드 구조의 일치
- 서버 전용 위임 capability와 토큰 갱신·401 처리
- 허용 목록 오류 매핑과 비밀 canary 검사
- 등록 멱등성과 결과 불명확 복구
- 수정 버전·`If-Match`·412 충돌 처리
- 권한 없는 티켓 404 비추론과 페이지 경계
- 기존 사용자 전환·세션·대화 이력·고정 모델 무회귀
- 동일 조건 사용자 완료 시간 측정 기록

## 승인 기록

- 통합 요약 확인: Looks correct
- Approval & Handoff 게이트: Pending
