# U2 Ticket Write — NFR Requirements Questions

## Context

U2는 기존 애플리케이션 안에 포함되는 `library` Unit이다. 상위 요구사항은 비밀·권한·무결성·복구·회귀·테스트·접근성 목표를 이미 측정 가능하게 확정했고, 프로젝트 제약은 새 처리량·가용성 목표나 새 인프라를 만들지 않도록 정했다. 기능 설계 검토에서 남은 두 계약 경계 우려는 새 인프라가 아니라 구현 전 계약 정합성 요구사항으로 다룬다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- 비밀·신뢰 경계는 모든 모델 입력, tool schema·결과, 로그, 테스트 실패 출력, HTTP 오류에서 credential canary 노출 0건을 요구한다. ITSM 텍스트가 신원·권한·확인·도구 정책을 바꾸는 사례도 0건이어야 한다.
- 모든 티켓 POST의 100%는 현재 서버 세션의 사용자 위임 토큰을 사용하며 서비스 토큰 사용은 0건이다. 정확한 현재 사용자 turn과 15분 이내의 사용자·세션·대화·operation·payload binding이 일치하지 않으면 POST는 0회다.
- 같은 확인 의도는 승인된 `ticket_create_attempts` ledger의 하나의 예측 불가능한 key와 byte-identical body만 사용하고, 최초 포함 총 POST는 최대 2회다. 429 자동 대기·재시도는 0회이며, authoritative created/replayed ticket ID가 없으면 성공 표시도 0건이다.
- 기능 설계에서 남은 계약 우려는 구현 전에 fail-closed하게 해결한다. 새 `prepared_create_payloads` table이나 계약에 없는 U1 transaction-participant API를 전제로 구현하지 않는다. 후속 NFR Design은 승인된 `ticket_create_attempts` table을 확인 전 canonical-byte 보존에도 사용하고, U1 공개 confirmation port가 성공하기 전 POST를 금지하며, 단일 compare-and-set 실행 claim으로 동시 확인·crash에서 중복 POST를 막는 계약 호환 경로를 상세화해야 한다.
- confirmation 전 ledger row가 고아로 남아도 실행 권한은 없으며, U1 pending binding과 consume 성공 없이는 전송할 수 없다. confirmation 이후 ledger는 logout·사용자 전환·대화 초기화·session expiry·process restart를 넘어 최소 24시간 유지되고, unresolved outcome을 안전하게 조정한다.
- 기존 37개 테스트와 신규 테스트의 통과율 100%, 변경 애플리케이션 코드 line coverage 80% 이상, 실제 OpenAI·ITSM 네트워크 호출 0건을 유지한다. clock, randomness, concurrency barrier, restart, lifecycle, malicious external text를 결정적으로 주입한다.
- 새 처리량·가용성·배포 인프라 목표는 추가하지 않고 기존 Assistant 운영 기준을 유지한다. U2가 `library`이므로 이 단계 산출물은 적용 가능한 `security-requirements.md`, `tech-stack-decisions.md`, `traceability.json`으로 제한한다.
- 기술 선택은 기존 Python 3.13, FastAPI, Pydantic, OpenAI Agents SDK, httpx, SQLite, pytest/FakeModel/MockTransport를 확장하며 새 Agent·서비스·UI·formatter·linter·type checker를 도입하지 않는다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
