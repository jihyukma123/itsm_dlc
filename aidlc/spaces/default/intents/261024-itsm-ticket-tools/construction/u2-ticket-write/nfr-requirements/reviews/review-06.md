## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T14:26:56Z
**Iteration:** 2
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md > Contract-Compatible Persistence Decision | 이 산출물은 하나의 `ticket_create_attempts` row를 confirmation 전에 만드는 ledger-first 흐름을 채택하지만, 필수 upstream인 `functional-spec.md`와 `rules.md`는 여전히 별도 `PreparedCreatePayloadV1` table과 `CreateConfirmationHandoffV1` cross-namespace transaction을 authoritative workflow로 규정한다. NFR 문서가 이를 “refinement”라고 부르는 것만으로 기능 설계의 source-of-truth가 바뀌지 않아 후속 설계와 구현이 서로 배타적인 두 흐름 중 하나를 추측해야 한다. | ledger-first/public-port-only 흐름을 채택하려면 Functional Design을 다시 열어 entity, BR3.1~BR3.6, workflow/state model과 storage boundary를 같은 흐름으로 정렬하고 재검토하라. 그렇지 않으면 NFR 요구사항을 현재 authoritative functional flow와 일치시켜라. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.2 and NFR3.6 | ledger row의 `created_at`과 `retained_until`을 prepare 시점에 채우도록 바꾸면서도 최소 보존 측정은 `retained_until >= created_at + 24h`만 요구한다. 기존 계약의 ledger는 confirmation 직후 생성되는 전제였으므로 새 흐름에서 review가 최대 15분 대기한 뒤 확인되면 confirmation 이후 보존 시간이 그만큼 짧아질 수 있으며, 문서의 “confirmation 후 최소 24시간” 주장과 측정식이 일치하지 않는다. | 확인 성공 시점을 별도 `confirmed_at`으로 보존하고 `retained_until >= confirmed_at + 24h`를 보장하거나, consume 성공 때 retention boundary를 같은 의미로 연장하는 명시적·idempotent transition과 fake-clock 검증식을 정의하라. 미확인 orphan의 cleanup 기준은 별도로 명시하라. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md > Verification Tooling Decisions | NFR6.1은 changed application code line coverage 80%를 completion blocker로 두지만 현재 저장소에는 coverage 구성이 없고, 이 결정문도 사용할 도구, 버전, changed-file 산정 방식 또는 재현 가능한 명령을 선택하지 않았다. “coverage measurement를 추가한다”만으로는 개발자와 검토자가 같은 수치를 재현할 수 없다. | Python 3.13과 pytest 9.1.1에 맞는 coverage 도구와 고정 버전을 선택하고, application-code include/omit 범위, changed-code 산정 규칙, 실행 명령과 80% 판정 방식을 기술 스택 결정에 고정하라. | Resolved (reviewer) |
| R-04 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.6 | NFR3.6은 모든 reconciliation outcome write가 `expected in_flight`를 비교해야 한다고 요구하지만, 상위 Functional Design은 transport 불명확 결과를 먼저 `ambiguous`로 기록한 뒤 `record_reconciliation`이 `expected_ambiguous_or_stale_claim`에서 실행되도록 정의한다. 정상 ambiguous reconciliation은 더 이상 `in_flight`가 아니므로 요구사항을 그대로 구현하면 CAS가 항상 실패하고, 이를 완화하면 어느 상태를 fence해야 하는지 구현자가 추측해야 한다. | Transport outcome write는 expected `in_flight`와 claim ID를 비교하고, reconciliation outcome write는 단일 recovery owner가 획득한 명시적 ambiguous/stale-reconciliation 상태와 claim ID를 비교하도록 요구사항·측정 기준·테스트 matrix를 분리해 Functional Design 상태 전이와 일치시켜라. | Resolved (reviewer) |
| R-05 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.6 and NFR7.1; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md > Reliability and Concurrency Decisions | 문서는 no-apply 401 뒤 credential refresh를 한 번만 허용하지만 durable refresh ownership이나 refresh-used evidence를 요구하지 않고 검증 기준도 POST count만 센다. Refresh 후 새 CAS claim을 얻는 순서에서는 경쟁 caller가 각각 refresh할 수 있고, refresh 성공 후 claim 전 crash에서는 재시작 caller가 이미 사용된 refresh를 구별하지 못해 allowed-once 계약을 검증하거나 보장할 수 없다. | Refresh 권한을 단일 CAS owner에게 부여하고 사용 여부를 crash-safe하게 기록하는 요구사항을 추가하거나, refresh와 다음 send claim을 원자적으로 소유하는 동등한 계약을 정의하라. Concurrent callers와 refresh-success-before-claim crash에서 refresh invocation이 정확히 한 번임을 세는 결정적 테스트를 측정 기준에 포함하라. | Resolved (reviewer) |
| R-06 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.6; tech-stack-decisions.md > Contract-Aligned Ledger and Claim Decision | NFR3.6은 reconciliation owner가 새 recovery `claim_id`를 CAS로 획득하고 outcome write가 그 ID를 비교한다고 요구하지만, upstream `TicketCreateAttemptV1`에는 send용 `claim_id` 하나만 있고 `begin_stale_claim_reconciliation`에는 새 recovery ID 입력이나 그 ID를 저장하는 atomic effect가 없다. `functional-spec.md`도 recovery owner 획득만 말할 뿐 identity의 생성·저장·crash takeover를 정의하지 않아 어떤 durable value를 outcome fence로 비교할지 구현할 수 없다. | Recovery claim을 send claim과 구분할지 동일 필드를 상태 전이와 함께 교체할지 결정하고, field, 생성 규칙, CAS atomic effect, owner crash/deadline, outcome predicate를 Functional Design entity·workflow/state model과 NFR 요구사항에 동일하게 정의하라. | Resolved (reviewer) |
| R-07 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.9; tech-stack-decisions.md > Reliability and Concurrency Decisions | NFR3.9는 durable `refresh_deadline_at`과 deadline 전 recovery 금지를 요구하지만 upstream authoritative entity에는 그 field가 없고 `recover_refresh_after_restart`는 deadline 입력·predicate 없이 reserved row의 generation을 즉시 비교한다. `functional-spec.md` FD-U2-03 step 4도 restart에서 즉시 committed 또는 failed로 조정하므로 NFR을 구현하면 Functional Design을 위반하고 Functional Design을 따르면 live refresh owner를 조기 실패 처리할 수 있다. | `refresh_deadline_at`을 authoritative entity와 repository 계약에 추가하고 산정·clock source·CAS predicate를 정의한 뒤 FD-U2-03, crash/concurrency table, state model, C-04 optional fields와 NFR3.9를 같은 before/at/after-deadline 동작으로 정렬하라. | Resolved (reviewer) |
| R-08 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.10; tech-stack-decisions.md > Contract-Aligned Ledger and Claim Decision | NFR3.10은 refresh가 이미 사용된 뒤의 no-apply 401을 `record_definitive_outcome` 한 번으로 직접 `terminal_failure`에 기록하라고 요구하지만 upstream FD-U2-03 step 9와 durable state model은 먼저 `retryable_no_apply`로 전이한 뒤 terminalize하도록 기술한다. Repository source에는 그 후속 terminal transition도 없어서 downstream NFR이 upstream workflow를 대체하는 서로 배타적인 계약이 됐다. | Direct terminal transition을 authoritative 정책으로 채택한다면 Functional Design의 repository invariant/output, FD-U2-03, gateway decision table, state model과 verification scenario를 함께 수정하고 NFR3.10은 그 정렬된 계약을 참조하게 하라. | Unresolved |

> R-06 Reviewer note: NFR3.6과 기술 결정이 별도 recovery identity를 제거하고 기존 stored send `claim_id`를 reconciliation owner CAS와 outcome fence에 재사용한다고 명시했다. 이는 upstream `begin_stale_claim_reconciliation`과 `record_reconciliation`의 existing-claim-ID 입력에 맞으며, 상세 atomic state effect는 NFR Design의 명시적 precondition으로 남겼다.

> R-07 Reviewer note: 배포 범위를 기존 single-process로 고정하고 같은 process의 `reserved` observer는 no-op으로, generation 비교는 실제 process restart에서만 수행하도록 요구사항·기술 결정·검증 시나리오가 정렬됐다. 이 범위에서는 원 refresh caller가 살아 있는 동안 조기 failure write가 발생하지 않는다.

> R-08 Reviewer note: NFR3.10은 이미 사용된 refresh 뒤 401이 terminal authentication failure로 끝나야 한다고 하지만, `retryable_no_apply` 중간 상태를 허용하면서도 그 상태를 `terminal_failure`로 닫는 기존 repository operation은 여전히 없다. Upstream FD-U2-03 step 9는 먼저 `retryable_no_apply`를 기록하라고 하고 gateway table은 직접 `terminal_failure`를 요구하므로, 기존 `record_definitive_outcome`이 어느 상태를 atomic하게 기록해야 하는지가 아직 하나로 정해지지 않았다.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| required-sections | PASS for `security-requirements.md` and `tech-stack-decisions.md` | 이 library Unit에 적용되는 두 Markdown 산출물의 필수 구조가 존재한다. |
| upstream-coverage | PASS for `security-requirements.md` | 선언된 upstream coverage가 기계 검증을 통과했다. |
| traceability | PASS for `traceability.json` | 모든 inception NFR row가 유효한 상세 target 또는 명시적 N/A에 연결된다. |
| JSON parse | PASS | `traceability.json`이 유효한 JSON이다. |
| NFR ID audit | PASS | 상세 ID 23개가 중복 없이 존재하고 NFR1~NFR9가 모두 coverage에 포함된다. |
| Markdown table and escaping audit | PASS | 두 Markdown 산출물의 table column 수와 unescaped separator를 확인했다. |
| linter and type-check | N/A | 산출물에 matching TS/JS output이 없다. |

### Summary

Recovery ownership과 single-process refresh recovery는 upstream 계약에 맞게 정리됐다. 이미 사용된 refresh 뒤의 401 durable transition은 여전히 하나의 명확한 atomic 경로로 고정해야 하지만, 열린 finding이 Major 1건이므로 verdict는 READY다.
