# ITSM 티켓 도구 페르소나

## Sources

- `inception/requirements-analysis/requirements.md`
- `aidlc/spaces/default/codekb/itsm_dlc/business-overview.md`
- `aidlc/spaces/default/codekb/itsm_dlc/component-inventory.md`
- `inception/practices-discovery/team-practices.md`
- `inception/user-stories/user-stories-questions.md`

## Primary Personas

### P1 — 민지, 일반 사내 사용자

- **Role:** 자신의 업무 중 발생한 IT 서비스 문제를 신고하고 진행 중인 티켓을 확인하는 직원
- **Goals:** 현재 화면을 벗어나지 않고 티켓을 찾고, 필요한 정보를 빠짐없이 등록하며, 자신이 볼 수 있는 티켓만 안전하게 다룬다.
- **Pain points:** ITSM 화면 전환과 반복 입력, 서비스·컴포넌트 이름의 불확실성, 오류가 발생했을 때 작업이 실행됐는지 알기 어려움
- **Tech comfort:** 중간
- **Frequency:** 필요 시 비정기적 사용
- **Success signal:** 자연어 요청과 짧은 확인 대화만으로 조회·등록을 완료하고, 실패 시 다음 행동을 이해한다.

### P2 — 현우, 서비스 데스크·운영 담당자

- **Role:** 권한 범위 안에서 여러 티켓을 검색하고 세부 정보를 확인하며 수정하는 운영 사용자
- **Goals:** 다양한 필터로 티켓을 좁히고, 최신 값을 확인한 뒤 필요한 필드만 안전하게 수정하며, 동시 변경을 덮어쓰지 않는다.
- **Pain points:** 반복적인 검색 조건 입력, 여러 티켓의 빠른 확인, 수정 충돌과 호출 제한, 권한별로 다른 가시성
- **Tech comfort:** 높음
- **Frequency:** 업무일마다 반복 사용
- **Success signal:** 전체 필터·페이지네이션과 ID 상세 조회를 사용하고, `If-Match` 충돌 시 최신 상태를 다시 확인해 의도한 변경만 적용한다.

### P3 — 서연, 개발·운영 유지보수 담당자

- **Role:** ITSM Assistant를 설정·검증·배포하고 보안·회귀 품질을 유지하는 담당자
- **Goals:** 실제 OpenAI·ITSM 호출 없이 기능을 재현 가능하게 검증하고, 기존 세션·대화·모델·화면 계약을 보존하며, 안전한 실행 방법을 문서로 제공한다.
- **Pain points:** 외부 API 의존 테스트의 불안정성, 비밀정보가 오류나 로그로 새는 위험, 신규 기능이 기존 사용자 흐름을 깨뜨릴 가능성
- **Tech comfort:** 높음
- **Frequency:** 개발·배포·장애 분석 시 사용
- **Success signal:** 기존 및 신규 자동화 테스트가 모두 통과하고 변경 코드 coverage가 기준을 충족하며 README만으로 실행·검증 경계를 이해한다.

## Persona Relationships and Priority

| Priority | Persona | Relationship to the feature |
|---|---|---|
| 1 | P1 일반 사내 사용자 | 등록과 자신의 티켓 조회라는 핵심 사용자 가치를 대표한다. |
| 1 | P2 서비스 데스크·운영 담당자 | 고급 검색과 안전한 수정을 대표하며 P1과 같은 화면을 사용하되 ITSM 권한이 다르다. |
| 2 | P3 개발·운영 유지보수 담당자 | 두 사용자 흐름을 안전하게 출시하고 운영하는 품질 책임을 대표한다. |

P1과 P2는 별도 로컬 권한 모델을 만들지 않는다. 동일한 Assistant를 사용하고, 실제 역할·객체 권한·가시성 차이는 현재 사용자 위임 토큰을 받은 ITSM API 응답으로만 나타난다. P3는 업무 티켓 권한을 우회하는 관리자가 아니라 애플리케이션 품질과 운영 경계를 책임지는 페르소나다.

## Excluded Personas

- 외부 고객·파트너 사용자
- 티켓 삭제·상태 전이·담당자 배정을 수행하는 별도 관리자
- 새로운 전용 화면이나 별도 Agent를 사용하는 사용자
