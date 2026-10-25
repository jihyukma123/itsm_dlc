# U4 Release Assurance Code Summary

## Outcome

Implemented the approved repository-local release-assurance boundary without changing the FastAPI startup graph, Agent/Runner semantics, the exact three-tool registry, external deployment infrastructure, or dependencies. The implementation provides a closed 74-case catalog (73 automated cases plus `REL.07`), content-addressed source snapshots, separate immutable baseline receipts, atomic evidence bundles, fail-closed evaluation, manifest-union coverage freezing, README verification, and an honest NFR8 measurement ledger.

## Changed Application Code

- `app/release_assurance/`: closed Pydantic/domain models, 73 unique selectors bound to real U1~U4 behavior, JUnit-derived selector evidence, locked atomic baseline/final repositories, closed evidence validation, derived terminal predicate/defect routing, README verifier, and fixed 18-trial NFR8 evaluator.
- `scripts/release_assurance.py`: provider-independent baseline/run/record/finalize/show/performance CLI. Callers cannot assert `release_ready`; finalization derives `release_ready` or `blocked` under the repository lock. It makes no OpenAI or ITSM call.
- `scripts/changed_line_coverage.py`: backward-compatible legacy mode plus explicit `--u4-union`, which requires exactly U1/U2/U3/U4 manifest/approved-plan/source-baseline bindings, freezes every binding, revalidates byte drift, and uses each Unit baseline in the union denominator.
- `README.md`, `.gitignore`: current three-tool behavior, security boundary, test/coverage commands, explicit separate live smoke/NFR8 procedure, and generated evidence exclusions.

## Verification Results

| Verification | Result |
|---|---|
| Review-repair baseline | `679 passed`; exit 0; skipped 0; locked pending→final receipt `baseline-2a49a87a940c`; baseline/final roots both `app`, `scripts` |
| Review-repair focused tests | forged/stale/partial/foreign-run/blocked/concurrent-writer/root-parity cases included in the green exact U4 run |
| Exact U4 unit command | `168 passed in 0.84s`; exit 0 |
| Catalog execution | 73 real, unique U1~U4 behavior selectors executed; `73 passed in 0.93s`; raw JUnit exact mapping validated; missing/duplicate/skipped/failed/mismatched evidence fails closed |
| Full-suite coverage collection | `679 passed in 8.71s`; real external network calls 0 |
| Explicit frozen U1~U4 union gate | `3838/4462 (86.02%)`; threshold 80%; exactly four Unit bindings; drift 0; missing sources 0 |
| Final full regression | `679 passed in 7.61s`; exit 0; failed 0; skipped 0 |
| Network boundary | unexpected attempts 0; deliberate raw-socket/fresh-client bypass blocked |
| Secret boundary | model/tool/result/log/error/assertion/traceback/stdout/stderr/runner-report canary exposure 0 |
| Documentation | seven required topics and explicit live-smoke separation passed |

The authoritative gate used explicit `--u4-union` mode and the full repository suite so every owning Unit's real selector behavior and source denominator were exercised. Legacy single-manifest behavior remains available only when explicit U4 union mode is absent.

## Evidence Bundle

- Baseline receipt: `.release-assurance/baselines/70b9a6eab63b25ba6501f906089346dc521ac500efa17c5e5051f8a09a23ae06/baseline-2a49a87a940c/`
- Frozen coverage inputs: `.release-assurance/coverage/u4/coverage-inputs-v3.json`
- Final immutable run: `.release-assurance/runs/dd84267bfed31433a0088853cee80a873f4d2aecf51ba6c71d861663d9f957a7/u4-review-repair-20261025-v3/`
- Final state: `release_ready`

## Live Validation and Remaining Limits

- No real OpenAI or ITSM smoke was run. The default automation remained FakeModel/MockTransport-only.
- NFR8 real-environment performance is `not_measured`, not passed. The 18-trial schema and evaluator are implemented; a person must explicitly supply target, test user, credential, generated data, cleanup, browser/device/network fingerprint, and execution intent.
- The baseline and final suite use the exact normalized command and dependency/runtime profile. The final source snapshot is independent from the baseline snapshot and references the baseline only by locator/digest.

## Assumptions & Open Questions

None.
