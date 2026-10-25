## Review

**Reviewer:** aidlc-architecture-reviewer-agent
**Iteration:** 2
**Date:** 2026-10-25T16:43:44Z
**Verdict:** READY
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/infrastructure-design/cicd-pipeline.md > Promotion Preconditions `PIPE-U3-02` and Ordered Verification Pipeline stage 2; aidlc/spaces/default/intents/261024-itsm-ticket-tools/inception/contract-design/contract-summary.md > C-02 `PendingMutationRepositoryV1.replace_update_pending` | Pipeline은 C-02의 required type과 exact-old replacement evidence를 fingerprint하고 provider/consumer fixture로 검증한 뒤에만 진행한다고 주장한다. 그러나 현재 C-02는 operation 결과를 `UpdatePendingReplacementV1`로 선언하면서 그 type을 어디에도 정의하지 않는다. U3 activation은 이 “replacement evidence”로 exact old execution을 retire하도록 설계되어 있어, 현재 baseline에서는 checker가 실패하거나 구현자가 result shape를 임의로 만들어야 한다. | C-02에 `UpdatePendingReplacementV1`의 old/new mutation ID, actor binding, committed/affected-row 의미와 closed-field 정책을 정의하고 contract fixture/fingerprint 대상에 포함한다. 정의가 들어오기 전에는 `PIPE-U3-02`의 현재 baseline을 통과 상태로 취급하지 않는다고 명시한다. | Resolved (reviewer) |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/infrastructure-design/cicd-pipeline.md > Promotion Preconditions, Commands and Evidence Contract, and Rollback and Recovery; aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/nfr-design/security-design.md > Migration, Storage, and Data-at-Rest Design | Upstream은 release evidence에 DB path, owner identity, permission/ACL class, disk protection, cleanup window, backup 포함 여부·암호화·접근 주체·retention을 기록하고, 누락·과도한 ACL·평문 무기한 backup·기존보다 긴 retention이면 release를 실패시키도록 요구한다. Pipeline은 rollback 단계에서 backup 정책을 서술할 뿐 이를 promotion blocking condition이나 evidence schema에 넣지 않으며, POSIX `0600`/parent `0700` 또는 동등 ACL과 retention 비교를 검사하는 stage가 없다. 따라서 `PIPE-U3-11`을 통과해도 승인된 data-at-rest gate를 실행하지 않을 수 있다. | 별도 promotion gate와 ordered stage를 추가해 runtime DB/parent path의 owner·ACL·disk protection, session cleanup window, backup encryption/access/retention을 수집·판정한다. 누락과 정책 위반을 production release failure로 만들고, 플랫폼별 equivalent-ACL 판정 및 redacted evidence fields를 Commands and Evidence Contract에 명시한다. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/infrastructure-design/cicd-pipeline.md > Commands and Evidence Contract lines 80-94 | 문서는 첫 명령을 “승인된 최종 Construction Verification Command”라고 부르지만 이 명령은 전체 source coverage 80%만 검사하고 NFR6.1의 changed-line gate를 실행하지 않는다. 이어지는 changed-line chain은 “같은 test run”을 사용한다고 하면서 `coverage erase` 후 pytest를 다시 실행하고, pinned `.venv/bin/python` 대신 PATH의 `coverage`와 `python`을 사용한다. 두 체인은 서로 다른 interpreter/dependency/coverage data를 사용할 수 있어 한 commit에 대한 재현 가능한 단일 승격 증거가 아니다. | pinned `.venv/bin/python -m coverage`로 test run과 JSON 생성을 한 번 수행하고 같은 JSON을 `.venv/bin/python scripts/changed_line_coverage.py`에 전달하는 하나의 fail-fast command chain을 정의한다. 전체 coverage를 별도 gate로 유지하려면 upstream보다 강한 추가 gate임을 명시하고, baseline/HEAD와 모든 exit code가 같은 evidence record에 묶이도록 한다. | Resolved (reviewer) |
| R-04 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/infrastructure-design/traceability.json > NFR3.4 and NFR3.7 coverage targets; cicd-pipeline.md > Promotion Preconditions | NFR3.4는 `PIPE-U3-07`을 PATCH counter gate라고 참조하지만 실제 `PIPE-U3-07`은 unexpected-network gate다. NFR3.7은 `PIPE-U3-04`를 exact-old publication gate라고 참조하지만 실제 `PIPE-U3-04`는 namespace ownership/schema isolation gate다. Target 문장의 나머지 설명은 올바른 검증을 가리키지만 stable gate ID가 틀려 evidence 자동 집계와 사람의 추적이 다른 gate로 연결된다. | NFR3.4와 NFR3.7 target을 실제 authority/attempt gate인 `PIPE-U3-09` 및 ordered stages 4/7에 연결하거나, promotion precondition IDs를 세분화해 publication과 PATCH gate에 고유 ID를 부여한 뒤 traceability를 맞춘다. | Resolved (reviewer) |
| R-05 | Minor | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u3-ticket-update/infrastructure-design/cicd-pipeline.md > Required Test Matrix > Security and presentation; traceability.json > NFR9.1 | NFR9.1은 review, confirmation, cancel, success, auth error, conflict, rate limit, ambiguous, invalidated, unavailable 각각의 plain-text 상태와 다음 행동을 요구한다. Pipeline matrix는 generic “text fallback과 safe next action”만 요구하고 trace target도 review/confirm/cancel/success/error/conflict/ambiguous만 열거해 rate-limited, invalidated, unavailable의 독립 snapshot assertion이 없다. | Required Test Matrix와 NFR9.1 target에 모든 요구 상태를 명시하고 각 상태의 plain-text label, next action, keyboard/screen-reader snapshot을 blocking assertion으로 만든다. | Resolved (reviewer) |

> R-01 Reviewer note: C-02 now defines `UpdatePendingReplacementV1` exactly once under `types` with `additional_properties: false`, required old/new mutation and actor/new-binding fields, committed and affected-row invariants, post-commit-only evidence semantics, and forbidden sensitive fields. `PIPE-U3-02` fingerprints that definition and fails Code Generation, merge and promotion when it is absent or reference-only.

> R-02 Reviewer note: `PIPE-U3-12` and ordered stage 11 now block production on DB/parent owner ACL, disk protection, session cleanup window, and backup inclusion, encryption, access principals and retention. The evidence contract records redacted platform-normalized fields and production promotion explicitly requires the storage-control evidence.

> R-03 Reviewer note: Promotion evidence now uses one fail-fast chain, one `.venv/bin/python`, one pinned test run, one `coverage.json`, one baseline/HEAD record, changed-line enforcement and the separately identified stronger whole-source threshold. The chain parses successfully and no PATH-selected Python or coverage executable remains in it.

> R-04 Reviewer note: NFR3.4 and NFR3.7 now target `PIPE-U3-09` and explicitly name ordered stages 7 and 4 respectively, matching the authority/attempt and publication checks in the pipeline.

> R-05 Reviewer note: The security/presentation matrix and NFR9.1 target now enumerate review, confirmation, cancel, success, auth error, conflict, rate limit, ambiguous, invalidated and unavailable, requiring a plain-text label, safe next action and keyboard/screen-reader snapshot for each.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON parse and shape check (`jq`) | PASS: stage/unit, 23 upstream IDs, 23 coverage rows, allowed `OK`/`Deferred` statuses | Infrastructure traceability is structurally valid. |
| Upstream ID set comparison (`jq`) | PASS: infrastructure IDs exactly equal current NFR Design IDs | No NFR ID is missing or orphaned. |
| Promotion command syntax (`zsh -n`) | PASS | The unified pinned-interpreter coverage command is syntactically executable. |
| Contract symbol cross-check (`rg`) | PASS: exactly one `UpdatePendingReplacementV1` definition and one operation reference | The replacement evidence type now resolves and has closed fields and invariants. |
| Markdown structure review | PASS | Applicability, preconditions, ordered pipeline, matrix, commands/evidence, secrets, promotion, rollback and U4 handoff are present and coherent for a library Unit. |
| `git diff --check` | PASS | No whitespace errors were found in the reviewed infrastructure artifacts or amended contract. |

### Summary

모든 이전 finding이 해결됐다. U3는 새 infrastructure를 추가하지 않으면서 migration, publication, confirmation, attempt/refresh, crash/response-loss, data-at-rest, coverage, rollback과 U4 release evidence를 실행 가능한 fail-closed 승격 계약으로 정의하며 current C-02/C-05와 정렬된다.
