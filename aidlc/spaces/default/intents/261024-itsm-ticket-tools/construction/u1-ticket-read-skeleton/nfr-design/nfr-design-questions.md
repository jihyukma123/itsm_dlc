# U1 Ticket Read Skeleton — NFR Design Questions

## Context

U1의 기능 설계, 보안·품질 요구사항, 기술 스택, inter-unit 계약이 신뢰 경계, 재시도·시간 예산, 저장소 수명주기, 표시 fallback과 기존 단일 애플리케이션 배포를 이미 확정했다. 이 단계에서 새로 결정해야 할 비기능 설계 선택은 없다.

## Questions

None.

## Assumptions & Open Questions

None.

## Consolidated Summary Confirmation

- U1은 기존 FastAPI 프로세스 안의 library로 유지하며 새 서비스, cache, queue, circuit breaker, rate limiter 또는 배포 인프라를 추가하지 않는다.
- `ApplicationLifecycle`이 chat·사용자 전환·로그아웃·대화 초기화 순서를 조정하고, `TicketOperations`만 전체 조회 deadline, 최대 두 번의 HTTP 시도, 한 번의 credential refresh와 허용된 250ms retry를 소유한다. `ItsmGateway` 호출 한 번은 HTTP 시도 정확히 한 번이다.
- 신원과 위임 credential은 서버 session에서 만든 직렬화 불가능 request capability에만 머물고, 외부 응답은 typed allowlist projection과 `SafeErrorV1`로 축소한다. 비밀과 원본 cursor·header·problem detail·exception은 model, API, persistence, log, test failure 출력으로 나가지 않는다.
- cursor, pending confirmation, presentation companion은 각각 사용자·세션·대화·정확한 query 또는 message correlation에 결합한다. 저장·소비·무효화는 기존 SQLite namespace에서 원자적으로 처리하고 lifecycle cleanup은 idempotent하게 수행한다.
- pending mutation의 `confirm`과 `consume_once`는 분리된 원자적 compare-and-set 전이다. `confirm`은 current-turn evidence와 exact binding을 확인해 `confirmed`로만 바꾸고, 이후 `consume_once`가 같은 binding을 다시 확인해 `consumed`로 바꾸면서 정확히 `{mutation_id, confirmed_at}`만 가진 일회성 `ConsumedMutationEvidenceV1`을 반환한다. 이 evidence 자체에는 HTTP 전송 권한이 없다.
- U1 lifecycle cleanup은 U1 소유 namespace만 정리한다. U2가 소유하는 durable `ticket_tools_create_v1` ledger의 key나 bytes를 삭제·수정하지 않으며, U1 consume 후 U2 bind 전 crash가 발생하면 U2는 같은 attempt·idempotency key·request bytes를 보존하고 새 pending review를 발행해 새로운 명시적 확인을 요구한다. bind되지 않은 evidence로 POST를 호출하지 않는다.
- 논리 `ServerSession` 만료 모델을 기존 물리 schema의 대체 정의로 사용하지 않는다. migration은 현재 저장소의 모든 인증·사용자·권한·위임 credential column과 의미를 introspection·회귀 fixture로 고정한 뒤 `session_expires_at`만 additive하게 추가하고, 복원 경로는 기존 field를 그대로 읽는다.
- 보호 chat은 하나의 per-conversation lock 아래 Runner 전과 Runner 직후 persisted session expiry를 재검사한다. 두 번째 검사는 presentation·text fallback·응답 결정에 선행하며, 그 사이 session이 만료되면 Runner 결과를 폐기하고 U1-owned state와 history를 terminal cleanup하되 U2 durable create ledger는 보존한다.
- 내부 `read_for_update`는 strong quoted-decimal ETag와 public version이 일치할 때만 typed evidence를 만들고, missing·weak·malformed·mismatched ETag는 `SafeErrorV1(upstream_unavailable)`로 종료해 review·PATCH 호출 수를 0으로 유지한다.
- optional presentation이 검증·저장·readback에 실패하면 기존 assistant text로 안전하게 fallback하며, ITSM 문자열은 끝까지 비신뢰 데이터로 유지해 브라우저에서 text node로 escape한다.
- 검증은 FakeModel, `httpx.MockTransport`, fake clock/sleeper와 secret canary를 사용한다. 실제 OpenAI·ITSM 호출은 0건이어야 하며, 기존 회귀와 U1 변경 application code line coverage 80% 이상을 유지한다.
- 이 library Unit의 NFR 설계 산출물은 적용 가능한 `security-design.md`, `logical-components.md`, `traceability.json`으로 제한한다.

**Does this all look correct before I generate the artifact?**

- Looks correct
- Request changes

[Answer]: Looks correct
