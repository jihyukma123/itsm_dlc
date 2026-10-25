## Review

**Verdict:** READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T10:09:10Z
**Iteration:** 2
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/infrastructure-design/cicd-pipeline.md > PIPE-U1-12 and Test Automation Integration / Read policy | The pipeline makes pre-call refresh for an expired or imminent credential a blocking gate, but the consumed logical design defines refresh only after the first gateway attempt returns an expired-credential outcome. Neither artifact defines the deterministic “imminent” predicate or threshold, so Code Generation cannot implement one behavior that satisfies both the runtime sequence and the proposed test. The NFR7.4 trace row nevertheless marks this path OK. | Establish one canonical pre-call usability predicate, including the clock source and imminent-expiry threshold, align the runtime sequence with it, and spell out fixtures for pre-call success, pre-call failure, and a later 401 sharing the same one-shot budget. Until that contract is resolved, mark the affected trace as a gap rather than OK. | Unresolved |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/infrastructure-design/cicd-pipeline.md > Verification Commands and PIPE-U1-05 | The recorded integrated command applies `--fail-under=80` to all measured `app` code, while PIPE-U1-05, Stage 7, the approved summary, and NFR6.1 apply the 80% floor only to changed application paths from the source manifest. Running both gates can block release on unrelated legacy coverage, while choosing only one leaves the documented verification sequence ambiguous. | Define a single authoritative U1 coverage gate. If whole-application 80% is an existing independent project gate, label it separately and state its ownership; otherwise remove its blocking threshold and make the source-manifest JSON command the sole U1 80% decision. | Resolved (reviewer) |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/infrastructure-design/cicd-pipeline.md > Deployment and Promotion Strategy / Database change and Rollback Design step 3 | The rollback claim says the prior application version can ignore the additive `session_expires_at` column, but no nullable/default migration shape or old-version write rehearsal is specified. The functional contract treats this field as required; an old binary whose INSERT omits a newly required column can fail after rollback even though reads ignore the column. | Specify a backward-write-compatible migration shape and add a rollback rehearsal that runs the prior session create, restore, login, and logout paths against the migrated database. If that compatibility cannot be proven, replace the rollback claim with a forward-fix or database-restore requirement. | Resolved (reviewer) |
| R-04 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u1-ticket-read-skeleton/infrastructure-design/cicd-pipeline.md > PIPE-U1-02 and Network Isolation | `httpx.MockTransport` protects only clients that use the injected boundary. The document names an “unexpected-network blocker” but never defines or tests a process-level deny mechanism, so an accidental new `AsyncClient`, SDK provider call, or other socket path can bypass MockTransport and invalidate the promised real-network count of zero. | Define the concrete default-deny network seam for the test process and add a deliberate bypass probe that proves an unregistered OpenAI or ITSM connection fails before DNS or socket I/O. Record that blocker result in release evidence. | Resolved (reviewer) |

> R-01 Reviewer note: The 60-second predicate and boundary fixtures remove the timing ambiguity, but the ownership conflict remains. PIPE-U1-12 places preflight evaluation inside the first public gateway call and then requires `TicketOperations` to invoke `CredentialRefreshPortV1`; the consumed LC-U1-03 sequence permits refresh only after a gateway expired-credential outcome, while LC-U1-04 forbids gateway refresh decisions and exposes one-attempt transport outcomes. No preflight result or callback contract connects those owners. Move the predicate to TicketOperations before invoking the gateway, or add and align an explicit preflight port before Code Generation.

> R-02 Reviewer note: The document now separates full-suite regression from the sole U1 80% decision and applies that decision only to source-manifest paths.

> R-03 Reviewer note: The additive column now has a backward-write-compatible epoch default, and the pipeline requires prior-release write rehearsal plus forward-redeploy fail-closed verification before claiming rollback readiness.

> R-04 Reviewer note: The process-level DNS/TCP deny fixture, deliberate AsyncClient/raw-socket bypass probes, blocking criteria, and release evidence now make the zero-real-network claim machine-checkable for the declared Python test process.

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| JSON and trace coverage consistency check | PASS: valid JSON, 23 upstream IDs, 23 coverage rows, no duplicates, missing rows, or orphan rows | Trace structure is complete; the NFR7.4 implementation target still depends on resolving R-01's owner/port mismatch. |
| Markdown table column check | PASS: no column-count mismatches | The revised delivery artifact's tables are structurally well formed. |

### Summary

The coverage, rollback, and network-isolation repairs are concrete and testable. One Major concern remains around where credential preflight belongs and how its result reaches the policy owner; resolve that port ownership before implementation to avoid reworking the gateway boundary.
