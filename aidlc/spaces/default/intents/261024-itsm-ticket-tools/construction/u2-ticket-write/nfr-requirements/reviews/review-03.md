## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T10:55:42Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md > Contract-Compatible Persistence Decision | 이 산출물은 하나의 `ticket_create_attempts` row를 confirmation 전에 만드는 ledger-first 흐름을 채택하지만, 필수 upstream인 `functional-spec.md`와 `rules.md`는 여전히 별도 `PreparedCreatePayloadV1` table과 `CreateConfirmationHandoffV1` cross-namespace transaction을 authoritative workflow로 규정한다. NFR 문서가 이를 “refinement”라고 부르는 것만으로 기능 설계의 source-of-truth가 바뀌지 않아 후속 설계와 구현이 서로 배타적인 두 흐름 중 하나를 추측해야 한다. | ledger-first/public-port-only 흐름을 채택하려면 Functional Design을 다시 열어 entity, BR3.1~BR3.6, workflow/state model과 storage boundary를 같은 흐름으로 정렬하고 재검토하라. 그렇지 않으면 NFR 요구사항을 현재 authoritative functional flow와 일치시켜라. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.2 and NFR3.6 | ledger row의 `created_at`과 `retained_until`을 prepare 시점에 채우도록 바꾸면서도 최소 보존 측정은 `retained_until >= created_at + 24h`만 요구한다. 기존 계약의 ledger는 confirmation 직후 생성되는 전제였으므로 새 흐름에서 review가 최대 15분 대기한 뒤 확인되면 confirmation 이후 보존 시간이 그만큼 짧아질 수 있으며, 문서의 “confirmation 후 최소 24시간” 주장과 측정식이 일치하지 않는다. | 확인 성공 시점을 별도 `confirmed_at`으로 보존하고 `retained_until >= confirmed_at + 24h`를 보장하거나, consume 성공 때 retention boundary를 같은 의미로 연장하는 명시적·idempotent transition과 fake-clock 검증식을 정의하라. 미확인 orphan의 cleanup 기준은 별도로 명시하라. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md > Verification Tooling Decisions | NFR6.1은 changed application code line coverage 80%를 completion blocker로 두지만 현재 저장소에는 coverage 구성이 없고, 이 결정문도 사용할 도구, 버전, changed-file 산정 방식 또는 재현 가능한 명령을 선택하지 않았다. “coverage measurement를 추가한다”만으로는 개발자와 검토자가 같은 수치를 재현할 수 없다. | Python 3.13과 pytest 9.1.1에 맞는 coverage 도구와 고정 버전을 선택하고, application-code include/omit 범위, changed-code 산정 규칙, 실행 명령과 80% 판정 방식을 기술 스택 결정에 고정하라. | Resolved (reviewer) |
| R-04 | Critical | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.6 | NFR3.6은 모든 reconciliation outcome write가 `expected in_flight`를 비교해야 한다고 요구하지만, 상위 Functional Design은 transport 불명확 결과를 먼저 `ambiguous`로 기록한 뒤 `record_reconciliation`이 `expected_ambiguous_or_stale_claim`에서 실행되도록 정의한다. 정상 ambiguous reconciliation은 더 이상 `in_flight`가 아니므로 요구사항을 그대로 구현하면 CAS가 항상 실패하고, 이를 완화하면 어느 상태를 fence해야 하는지 구현자가 추측해야 한다. | Transport outcome write는 expected `in_flight`와 claim ID를 비교하고, reconciliation outcome write는 단일 recovery owner가 획득한 명시적 ambiguous/stale-reconciliation 상태와 claim ID를 비교하도록 요구사항·측정 기준·테스트 matrix를 분리해 Functional Design 상태 전이와 일치시켜라. | New |
| R-05 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/security-requirements.md > NFR3.6 and NFR7.1; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u2-ticket-write/nfr-requirements/tech-stack-decisions.md > Reliability and Concurrency Decisions | 문서는 no-apply 401 뒤 credential refresh를 한 번만 허용하지만 durable refresh ownership이나 refresh-used evidence를 요구하지 않고 검증 기준도 POST count만 센다. Refresh 후 새 CAS claim을 얻는 순서에서는 경쟁 caller가 각각 refresh할 수 있고, refresh 성공 후 claim 전 crash에서는 재시작 caller가 이미 사용된 refresh를 구별하지 못해 allowed-once 계약을 검증하거나 보장할 수 없다. | Refresh 권한을 단일 CAS owner에게 부여하고 사용 여부를 crash-safe하게 기록하는 요구사항을 추가하거나, refresh와 다음 send claim을 원자적으로 소유하는 동등한 계약을 정의하라. Concurrent callers와 refresh-success-before-claim crash에서 refresh invocation이 정확히 한 번임을 세는 결정적 테스트를 측정 기준에 포함하라. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| required-sections | PASS: security-requirements 7개, tech-stack-decisions 8개 H2 확인 | 두 Markdown 산출물이 문서형식 검사를 통과했다. |
| upstream-coverage | PASS: functional-spec, rules, requirements, contract-summary, technology-stack 모두 참조됨 | 선언된 상위 설계·요구·기술 근거가 산출물에 연결됐다. |
| linter | N/A | 검토 산출물은 Markdown/JSON이며 TS/JS match 대상이 없다. |
| type-check | N/A | 검토 산출물은 Markdown/JSON이며 TS/TSX match 대상이 없다. |
| traceability | PASS: gap, orphan, missing row, invalid target 모두 0건 | NFR1~NFR9 coverage와 derived NFR target이 구조적으로 유효하다. |

### Summary

대부분의 보안·보존·재시도·coverage 목표는 측정 가능하지만, reconciliation의 CAS expected state가 상위 상태 모델과 충돌해 정상 복구 경로를 구현할 수 없다. 또한 refresh-once는 crash·경쟁 상황에서 durable하게 증명되지 않아 두 계약을 수정한 뒤 재검토해야 한다.
