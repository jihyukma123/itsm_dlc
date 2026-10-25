# U4 Release Assurance — Infrastructure Design Questions

## Context

U4는 기존 애플리케이션과 저장소 밖 승격 경로를 유지하면서 U1~U4의 계약·회귀·coverage·문서 증거를 하나의 재현 가능한 출시 판정으로 묶는 Unit이다. 승인된 상위 설계에 따라 새 runtime service, cloud resource, CI provider 또는 배포 topology를 추가하지 않는다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- 기존 단일-process Python 3.13 FastAPI 배포, app-scoped HTTP client, Server Session SQLite와 Agents SDK history SQLite를 그대로 사용하고 새 service, worker, queue, cache, database, load balancer 또는 IaC stack을 추가하지 않는다.
- 기본 자동화는 FakeModel, `httpx.MockTransport`, pytest process의 DNS/TCP default-deny와 deliberate bypass probe를 사용하며 실제 OpenAI·ITSM network 호출은 0건이어야 한다.
- U4는 C03 15개, C04 25개, C05 27개와 REL.01~REL.06으로 구성된 73개 자동화 검사, 별도의 REL.07 문서 검사, 전체 회귀와 비밀 canary·network fence를 모두 blocking evidence로 집계한다.
- 변경 line coverage는 U1~U4 `source-manifest.json`, 승인된 plan과 attempt baseline을 coverage 실행 전에 원자적으로 고정하고, 그 합집합의 executable application line을 `coverage==7.17.0` JSON으로 80% 이상 검증한다. 누락 source, 승인 밖 변경, 입력 drift 또는 denominator 축소는 fail closed한다.
- 검증 증거는 `.release-assurance/`의 source-revision-bound pending bundle에 allowlist record로 원자 기록한 뒤, 모든 predicate가 통과할 때만 immutable finalized bundle로 전환한다. 승격과 rollback은 bundle locator와 digest로 정확한 revision을 확인한다.
- baseline과 final 회귀는 동일한 normalized command와 environment fingerprint를 사용하고 exit 0, failed 0, skipped 0을 요구한다. 실패는 owning Unit과 C-01~C-07 계약으로 route하며 수선 뒤에는 predecessor를 가리키는 새 run에서 전체 증거를 다시 생성한다.
- 실제 smoke와 NFR8 성과 측정은 기본 자동화와 분리한다. 사람이 credential, 대상 환경, 일회용 test data와 정리 절차를 명시한 경우에만 실행하며, 방식·시나리오별 사전 지정 trial 3회의 중앙값과 Assistant 외부 화면 전환 0회로 결과를 판정한다.
- 기존 저장소 밖 승격·production 승인·rollback 절차는 유지한다. U4는 blue-green, canary, rolling 같은 새 배포 방식을 선택하거나 production 승인을 자동화하지 않는다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
