## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T05:43:51Z
**Iteration:** 2
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/nfr-design/security-design.md > Authentication and Authorization Architecture > Authorization decisions | 이 설계는 strong quoted-decimal ETag가 없거나 public version과 불일치해도 visible detail read가 성공하고 update evidence만 버리도록 한다. 그러나 shared C-01의 `SafeTicketDetailV1.metadata_invariants`는 missing, weak, non-decimal 또는 mismatched ETag에서 safe `upstream_unavailable`을 반환하도록 고정한다. 같은 gateway 응답을 성공으로 투영할지 실패시킬지 계약별로 달라 구현과 contract test의 기대 결과가 결정되지 않는다. | C-01의 invariant와 현재 functional/NFR 요구사항 중 하나를 versioned 결정으로 정합화한 뒤, security design의 detail adapter 결과와 invalid ETag verification matrix를 그 단일 의미에 맞춘다. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/nfr-design/logical-components.md > LC-U1-09 Presentation History Repository and Lifecycle cleanup | shared C-03은 orphan presentation row를 history load와 startup cleanup에서 idempotent하게 삭제하도록 요구하지만, LC-U1-09는 invalid, missing, orphan metadata를 무시한다고만 하고 lifecycle 표에도 startup 또는 history-load deletion이 없다. `security-design.md`의 retention 표도 orphan cleanup이라는 결과만 적어 실행 시점과 소유 동작을 정하지 않아, SDK history가 사라진 뒤 companion metadata가 계약된 history lifetime보다 오래 남을 수 있다. | LC-U1-09의 operations와 runtime sequence에 history load 시 orphan 판정·idempotent 삭제, application startup cleanup, 실패 시 text fallback과 재시도 동작을 명시하고 retention verification에 orphan row 삭제 증거를 추가한다. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/nfr-design/security-design.md > Presentation and Browser Security | 이 절은 conversation lock을 `Runner 완료부터` presentation commit/readback까지 유지한다고 정하지만, shared C-03 lifecycle과 functional design은 lock을 Runner 실행 전에 획득해 Runner, persisted assistant correlation, commit/readback 전체에 유지하도록 요구한다. 같은 NFR 산출물의 `logical-components.md`도 before-Runner 획득을 전제로 한다. 보안 설계를 그대로 구현하면 동시 chat 두 개가 Runner와 SDK message persistence를 교차시킨 뒤 잘못된 assistant sequence 또는 text hash를 상관시킬 수 있다. | security design의 request flow와 presentation control에서 conversation lock을 Runner 호출 전에 획득하고 persisted message correlation, companion commit/readback, 최종 응답 결정 후 해제하도록 순서를 통일한다. concurrent Runner fixture가 이 획득 순서와 mismatched metadata 0건을 검증하도록 명시한다. | New |

> R-01 Reviewer note: ordinary detail과 U3용 read-for-update profile을 분리하고, 후자에서만 invalid ETag를 `upstream_unavailable`로 실패시키는 성공 조건과 독립 contract fixture를 명시해 C-01의 read-for-update invariant와 일반 조회 의미를 구분했다.

> R-02 Reviewer note: LC-U1-09에 history-load 및 startup orphan 삭제, bounded idempotent transaction, rollback, text fallback과 다음 실행 재시도 순서가 추가됐다.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON parse and upstream coverage check | PASS: 19개 upstream NFR 모두 unique `OK` row에 매핑되고 누락, 중복, extra ID 0건 | 선언된 추적성 구조와 범위는 완전하다. |
| Cross-reference check | PASS: SEC-U1-01–10과 LC-U1-01–11 참조 모두 해석됨 | 내부 보안 결정 및 논리 컴포넌트 ID에 broken reference가 없다. |
| Type-check and snippet linter | NOT APPLICABLE: TypeScript/JavaScript snippet 없음 | 해당 센서가 검사할 코드 조각이 없다. |

### Summary

이전 두 결함은 수정됐지만, security design의 lock 획득 시점이 shared lifecycle 및 같은 단계의 logical design과 충돌한다. 동시 대화에서 message correlation을 보장하려면 Runner 전부터 하나의 lock을 유지하도록 단일 순서를 확정해야 한다.
