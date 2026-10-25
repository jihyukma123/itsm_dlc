# U3 Ticket Update — NFR Requirements Questions

## Context

U3는 기존 애플리케이션 안에 포함되는 `library` Unit이다. 상위 요구사항은 비밀·권한·무결성·복구·회귀·테스트·접근성 목표를 이미 측정 가능하게 확정했고, 프로젝트 제약은 새 처리량·가용성 목표나 새 인프라를 만들지 않도록 정했다. 최신 C-02/C-05 계약은 U1의 exact-old 원자적 update-pending 교체와 U3 durable execution 저장소의 소유권·migration·정리·검증 책임을 확정했으며, 갱신된 기능 설계가 이를 구현 가능한 흐름으로 반영했다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- 비밀·신뢰 경계는 모델 입력, tool schema·결과, 로그, 테스트 실패 출력과 HTTP 오류에서 credential canary 노출 0건을 요구한다. ITSM 텍스트가 현재 사용자·권한·확인 상태·도구 동작을 바꾸는 사례도 0건이어야 한다.
- 모든 티켓 상세 조회와 PATCH의 100%는 현재 서버 세션의 사용자 위임 capability를 사용하고 서비스 토큰 사용은 0건이다. 사용자·세션·대화·operation·ticket·patch hash·base version·현재 raw turn 중 하나라도 맞지 않으면 PATCH는 0회다.
- review는 public version과 정확히 일치하는 strong quoted-decimal ETag에서 U1이 만든 server-only `IfMatchVersion`에만 기반한다. 값이 없거나 weak·비정수·불일치이면 review와 PATCH를 만들지 않는다.
- 각 PATCH gateway 호출은 HTTP 시도 1회다. 사용자 operation은 최초 호출과 권위 있는 미적용 보장 401 뒤 추가 호출을 합쳐 최대 2회이며, 412·428·timeout·transport·그 밖의 불명확 결과에는 PATCH를 자동 재전송하지 않는다. 최신 상세에서 모든 기대 변경과 version 증가가 확인되지 않으면 성공으로 표시하지 않고 429 자동 대기·재시도도 0회다.
- U1 `replace_update_pending`은 `prepare`의 no-old 조건과 `revise`의 exact-old mutation·actor·operation·pending 조건을 검증하고, 이전 row 무효화와 새 row 삽입을 `ticket_tools_state_v1` 안에서 원자적으로 수행한다. 실패하면 이전 review를 유지하며 broad-selector invalidation은 금지한다.
- U3는 `ticket_tools_update_v1.pending_update_executions`를 소유하고 U1 migration 뒤/U3 plugin 활성화 전에 적용한다. canonical patch bytes/hash와 검증된 `IfMatchVersion`을 staged로 저장하고 U1 replacement 뒤 exact-binding CAS로 active 승격하며, 접근·startup·lifecycle 경계에서 orphan·만료·terminal row를 멱등 정리한다.
- PATCH 권한은 exact matching active U3 execution, exact matching U1 pending, 현재 raw turn의 명시적 확인과 원자적 confirm+consume evidence가 모두 있을 때만 성립한다. tool input ticket ID나 mutation·actor·patch hash·base version이 다르면 consume과 PATCH는 모두 0회다.
- active 승격 뒤 review 응답이 유실되면 exact actor/session/conversation/ticket locator와 U1 binding 재검증으로 같은 pending reference만 복구한다. 다른 actor·ticket 또는 staged·retired row는 반환하지 않으며 version drift에서는 PATCH 없이 revise/cancel로 수렴한다.
- 기존 37개 테스트와 신규 테스트의 통과율 100%, 변경 애플리케이션 코드 line coverage 80% 이상, 실제 OpenAI·ITSM 네트워크 호출 0건을 유지한다. restart, crash point, concurrent confirm, lifecycle invalidation, malicious external text를 결정적으로 주입한다.
- 새 처리량·가용성·배포 인프라 목표는 추가하지 않고 기존 Assistant 운영 기준을 유지한다. U3가 `library`이므로 이 단계 산출물은 적용 가능한 `security-requirements.md`, `tech-stack-decisions.md`, `traceability.json`으로 제한한다.
- 기술 선택은 기존 Python 3.13, FastAPI, Pydantic, OpenAI Agents SDK, httpx, SQLite, pytest/FakeModel/MockTransport를 확장하며 새 Agent·서비스·UI·formatter·linter·type checker를 도입하지 않는다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
