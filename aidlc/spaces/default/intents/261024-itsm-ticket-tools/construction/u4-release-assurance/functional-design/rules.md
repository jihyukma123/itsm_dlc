# U4 출시 보증 비즈니스 규칙

## Sources

- `inception/user-stories/stories.md`의 `US4.1`, `US5.1`
- `inception/requirements-analysis/requirements.md`의 `FR1`, `FR5`~`FR7`, `NFR1`~`NFR9`
- `inception/contract-design/contract-summary.md`의 C-01~C-07 및 Contract Verification Matrix

## Rules

```yaml
rules:
  - id: BR4.1
    statement: 최종 Agent는 기존 Agent와 Runner 안에서 정확히 세 티켓 도구만 제공한다.
    category: constraint
    applies_to: final_agent_assembly
    trigger: 최종 plugin registry를 조립하거나 시작할 때
    logic: "IF registry의 tool 이름 집합이 ticket_read, ticket_write, ticket_update와 정확히 같지 않거나 중복 이름이 있으면 THEN 조립을 실패 처리한다."
    violation_behaviour: 출시 보증을 차단하고 registry 소유 Unit으로 결함을 되돌린다.
    source: [FR1.1, FR1.2, FR7.3, NFR5]

  - id: BR4.2
    statement: 모든 티켓 호출은 서버 세션의 현재 사용자와 위임 credential에 고정되고 비밀 노출은 0건이어야 한다.
    category: authorization
    applies_to: ticket_request_capability_and_all_tool_boundaries
    trigger: 도구 schema, 모델 입력, gateway 요청, 결과, 로그 또는 오류를 검증할 때
    logic: "IF 사용자 신원이 서버 세션에서 복원되지 않았거나 티켓 호출이 서비스 credential을 쓰거나 비밀 canary가 한 경계라도 나타나면 THEN 검증은 실패한다."
    violation_behaviour: 모든 mutation을 금지하고 보안 차단 결함으로 기록한다.
    source: [FR1.3, FR1.4, FR5.1, FR5.2, NFR1, NFR2]

  - id: BR4.3
    statement: operation별 HTTP 시도와 credential refresh는 계약의 단일 예산을 넘지 않는다.
    category: policy
    applies_to: read_create_update_recovery
    trigger: timeout, transport 오류, 만료 임박 credential 또는 token_expired 401이 발생할 때
    logic: "IF read이면 전체 HTTP 시도는 2회 이하이고, create이면 같은 key·bytes의 POST가 전역 attempt count 2회 이하이며, update이면 권위 있는 미적용 401 복구를 제외한 PATCH 재전송은 0회이고, 각 실행의 refresh port 호출은 1회 이하여야 한다."
    violation_behaviour: 추가 호출을 금지하고 안전한 실패로 종료한다.
    source: [FR5.3, FR6.2, FR6.3, FR6.4, NFR7]

  - id: BR4.4
    statement: session 또는 credential 복구 실패는 어떤 등록·수정도 발생시키지 않아야 한다.
    category: constraint
    applies_to: authenticated_mutation_flow
    trigger: session 만료, 사용자 비활성, refresh 실패 또는 crash 복구가 발생할 때
    logic: "IF 현재 actor binding과 유효 capability를 확정할 수 없으면 THEN POST와 PATCH를 호출하지 않고 보류 확인을 재사용 불가 상태로 만든다."
    violation_behaviour: authentication_required 안전 오류와 재로그인 안내만 제공한다.
    source: [FR5.3, FR5.4, NFR2, NFR3]

  - id: BR4.5
    statement: 사용자 전환·로그아웃·대화 초기화·세션 만료는 revocable 상태를 격리해 정리하고 durable 중복 방지 상태는 보존한다.
    category: constraint
    applies_to: lifecycle_orchestration
    trigger: lifecycle 사건 또는 같은 conversation의 동시 실행이 발생할 때
    logic: "IF lifecycle 사건이 발생하면 THEN 같은 conversation 직렬화 경계에서 pending mutation, cursor, presentation history와 SDK history를 정해진 순서로 정리하고 create ledger는 최소 보존 기간 동안 유지하며 다른 사용자에게 상태를 넘기지 않는다."
    violation_behaviour: 새 session commit 또는 응답 공개를 차단하고 idempotent 정리를 다시 수행할 수 있게 한다.
    source: [FR5.4, FR7.3, NFR3, NFR5]

  - id: BR4.6
    statement: 오류와 외부 텍스트는 허용 목록 기반 안전 데이터로만 반환하며 숨은 mutation replay나 429 자동 대기를 하지 않는다.
    category: policy
    applies_to: safe_error_and_presentation_boundaries
    trigger: 외부 응답, 예외, conflict, rate limit 또는 ambiguous 결과를 처리할 때
    logic: "IF 외부 오류나 텍스트를 반환하면 THEN 안정 code와 안전 message만 제공하고 raw detail·header·exception을 제거하며, 429는 즉시 반환하고 불명확 PATCH는 자동 재전송하지 않는다."
    violation_behaviour: 안전한 일반 오류 또는 text fallback을 사용하고 출시는 차단한다.
    source: [FR1.5, FR6.1, FR6.4, NFR1, NFR7]

  - id: BR4.7
    statement: 기본 자동화 검증은 FakeModel과 격리 transport만 사용하고 예상하지 않은 실제 network를 기본 거부한다.
    category: policy
    applies_to: automated_test_execution
    trigger: U4 검증 suite를 시작할 때
    logic: "IF 테스트가 명시된 mock endpoint 밖 DNS, TCP, 실제 OpenAI 또는 실제 ITSM 접근을 시도하면 THEN 즉시 실패한다."
    violation_behaviour: 테스트 실행을 실패 처리하고 호출 대상 증거만 비밀 없이 기록한다.
    source: [FR7.4, NFR1, NFR5]

  - id: BR4.8
    statement: 모든 신규·기존 회귀 테스트는 통과하고 변경 애플리케이션 line coverage는 80% 이상이어야 한다.
    category: constraint
    applies_to: regression_and_coverage_assessment
    trigger: 출시 보증 판정을 계산할 때
    logic: "IF 전체 suite 통과율이 100%가 아니거나 source manifest 기준 line coverage가 80% 미만이면 THEN release_ready로 전이하지 않는다."
    violation_behaviour: 실패를 소유 Unit에 route하고 수선 후 전체 판정을 다시 실행한다.
    source: [FR7.4, NFR5, NFR6]

  - id: BR4.9
    statement: 기존 세션·사용자 전환·대화 이력·API·화면·접근성·고정 모델 설정의 승인되지 않은 변화는 0건이어야 한다.
    category: constraint
    applies_to: brownfield_regression_surface
    trigger: 최종 조립 및 전체 회귀를 검증할 때
    logic: "IF 기존 reply/context 계약, history fallback, keyboard·screen-reader 흐름, model 이름, reasoning effort 또는 tracing 설정이 바뀌면 THEN 회귀 실패다."
    violation_behaviour: 새 티켓 기능 성공 여부와 무관하게 출시를 차단한다.
    source: [FR7.1, FR7.2, FR7.3, NFR5, NFR9]

  - id: BR4.10
    statement: README는 기능·설정·실행·보안 경계·테스트·coverage와 smoke 분리를 모두 설명해야 한다.
    category: validation
    applies_to: release_documentation
    trigger: documentation assurance를 판정할 때
    logic: "IF 필수 주제 중 하나라도 없거나 문서 명령이 실제 검증 절차와 다르면 THEN 문서 검증은 실패한다."
    violation_behaviour: documentation_verified 전이를 차단한다.
    source: [FR7.5]

  - id: BR4.11
    statement: 실제 연동 smoke는 기본 자동화와 분리되고 명시적 credential과 대상 환경이 있을 때만 사람이 선택해 실행한다.
    category: authorization
    applies_to: live_smoke_procedure
    trigger: 실제 OpenAI 또는 ITSM smoke 실행을 요청할 때
    logic: "IF 명시적 credential, 대상 환경 또는 실행 의사가 없으면 THEN 실제 외부 호출을 시작하지 않는다."
    violation_behaviour: 절차를 미실행 상태로 유지하되 기본 자동화 결과를 실패로 바꾸지 않는다.
    source: [FR7.4, FR7.5, NFR1]

  - id: BR4.12
    statement: NFR8 성과 판정은 고정된 실제 환경 절차의 사전 지정된 3+3회 trial과 화면 전환 수로만 결정한다.
    category: calculation
    applies_to: performance_measurement
    trigger: read, create 또는 update 시나리오의 사용자 성과를 평가할 때
    logic: "IF 동일 조건에서 방식별 warm-up을 제외한 사전 지정 trial 1·2·3이 모두 성공하고 Assistant 세 duration의 중앙값이 기존 UI 세 duration의 중앙값보다 짧으며 Assistant 외부 화면 전환이 모두 0이면 THEN 해당 시나리오를 충족으로 판정한다; IF trial이 실패하면 추가 trial로 교체하지 않고 해당 시나리오를 미충족으로 판정한다."
    violation_behaviour: 환경 조건 위반은 session invalid, 정상 조건의 trial 실패·완료 사건 미도달은 성과 목표 미충족으로 구분하고 어느 경우에도 달성을 주장하지 않는다.
    source: [NFR8]

  - id: BR4.13
    statement: release_ready는 모든 자동화·coverage·문서 차단 조건이 동시에 충족될 때만 가능하다.
    category: constraint
    applies_to: release_assurance_state
    trigger: 최종 출시 판정을 요청할 때
    logic: "IF Required Verification Catalog의 release 필수 check_id마다 현재 run에 정확히 하나의 passed evidence가 있고 baseline·final regression evidence와 coverage가 passed이며 documentation이 passed이고 blocking defect가 없으면 THEN release_ready로 전이하고 ELSE blocked로 전이한다."
    violation_behaviour: 부분 성공을 전체 출시 성공으로 표시하지 않는다.
    source: [NFR1, NFR2, NFR3, NFR5, NFR6, NFR7, NFR9]

  - id: BR4.14
    statement: U4는 U1~U3의 결함을 숨기거나 우회하지 않고 계약 소유 Unit에 되돌려 새 증거로 재검증한다.
    category: policy
    applies_to: defect_routing
    trigger: contract, lifecycle, 보안, regression 또는 coverage 실패가 발견될 때
    logic: "IF 실패 원인이 U1, U2 또는 U3 소유 계약이나 구현이면 THEN 해당 Unit과 계약 reference를 지정하고 repair 뒤 원래 실패 검사를 포함한 전체 보증을 다시 실행한다."
    violation_behaviour: repaired만으로 defect를 닫지 않고 reverified까지 release를 차단한다.
    source: [FR7.4, NFR3, NFR5, NFR6]

  - id: BR4.15
    statement: 모든 보증 증거는 소스 revision과 실행 조건에 결합되어 재현 가능해야 한다.
    category: validation
    applies_to: assurance_evidence
    trigger: evidence를 기록하거나 재사용할 때
    logic: "IF evidence의 source revision, procedure, environment 또는 digest를 확인할 수 없으면 THEN 현재 출시 판정의 증거로 인정하지 않는다."
    violation_behaviour: 해당 검사를 not_run으로 취급하고 재실행한다.
    source: [FR7.4, FR7.5, NFR5, NFR6, NFR8]
```

## Rules Summary

| Rule | Summary |
|---|---|
| BR4.1 | 최종 tool 집합은 정확히 세 개이며 중복은 fail-closed다. |
| BR4.2 | 현재 서버 사용자·위임 credential만 사용하고 비밀 노출은 0건이다. |
| BR4.3 | read/create/update의 시도 및 refresh 상한을 하나의 정책 소유자가 지킨다. |
| BR4.4 | 인증·세션 복구 실패 시 mutation은 0건이다. |
| BR4.5 | lifecycle 상태는 교차 사용자 재사용 없이 원자적·멱등적으로 정리한다. |
| BR4.6 | 안전 오류만 반환하고 429 대기와 숨은 PATCH replay를 금지한다. |
| BR4.7 | 기본 자동화에서 실제 외부 network 호출은 0건이다. |
| BR4.8 | 전체 suite 100%와 변경 line coverage 80% 이상을 요구한다. |
| BR4.9 | 기존 제품·API·접근성·model 동작 회귀는 0건이다. |
| BR4.10 | README의 출시 필수 설명을 검증한다. |
| BR4.11 | 실제 smoke는 명시적 credential이 있는 별도 절차다. |
| BR4.12 | NFR8은 실제 환경의 방식별 3회 중앙값으로만 판정한다. |
| BR4.13 | 모든 차단 조건을 동시에 만족해야 release-ready다. |
| BR4.14 | 결함은 소유 Unit으로 route하고 재검증한다. |
| BR4.15 | evidence는 revision과 환경에 결합되어야 한다. |

