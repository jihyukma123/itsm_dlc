## Summary

- Builds: U1~U3의 세 도구를 검증하는 73개 release catalog, 분리된 baseline receipt와 final revision run, 원자적 evidence bundle, coverage·문서·성과 측정 gate를 구현한다.
- Touches: 새 `app/release_assurance/`, `scripts/release_assurance.py`, `scripts/changed_line_coverage.py`, U4 pytest, `README.md`, `.gitignore`를 변경한다.
- Tests: 구성요소별 5~8개 수준의 단위·통합·보안 테스트 약 45~65개와 73개 catalog-to-pytest selector 완전성 검사를 추가하고 manifest-union changed lines 80% 이상을 검증한다.

## Scope and Guardrails

- U4는 U1~U3의 계약을 재정의하거나 실패 expectation을 완화하지 않는다. 발견된 결함은 check ID, 소유 Unit, C-01~C-07 reference로 fail-closed route한다.
- 기존 FastAPI runtime, Agent/Runner/model/reasoning/tracing, 세 tool schema, SQLite migration namespace와 browser surface에는 새 기능을 넣지 않는다. 최종 조립은 public registry와 기존 API/UI 회귀를 통해 검증한다.
- 기본 자동화는 FakeModel, `httpx.MockTransport`, fake clock/barrier와 process-wide network deny만 사용한다. 실제 OpenAI/ITSM smoke는 명시적 credential·target·test user·사람의 실행 의사가 있을 때만 별도 명령으로 가능하다.
- release evidence에는 ticket payload, canonical mutation bytes, credential, Authorization, raw header/problem/exception 또는 raw test output을 저장하지 않는다.
- 변경 전 전체 suite는 final run의 evidence가 아니다. 별도 immutable `BaselineReceipt`가 baseline source snapshot·명령·환경·결과를 소유하고, 구현 완료 후 content-addressed final source snapshot으로 새 `ReleaseAssuranceRun`을 시작해 baseline receipt locator/digest만 비교 입력으로 참조한다.
- final source snapshot은 `HEAD`와 tracked/untracked application source의 정렬된 path/mode/content SHA-256으로 계산한 `workspace-source-v1:<sha256>`다. 한 run의 모든 evidence는 이 식별자와 일치해야 하며 predecessor 또는 baseline evidence를 current-run evidence로 복사하지 않는다.
- `blocked`와 `release_ready`는 finalized run의 terminal 상태다. final bundle의 `final.json` 이후 write를 거부하고, repair는 predecessor locator/digest를 가진 새 run과 새 evidence를 요구한다.
- feature scope의 Standard strategy와 80% line-coverage floor를 모두 적용한다. test-after 순서에 따라 각 testable layer 구현 직후 해당 테스트를 작성·실행한다.

## Brownfield Blast Radius

| Change surface | Direct consumers | Impact | Planned protection |
|---|---|---|---|
| `scripts/changed_line_coverage.py` | U1~U3 기존 coverage 명령, U4 union gate | High | 기존 flat CLI 의미를 그대로 유지하고 freeze/prior plan/prior baseline/frozen-input 옵션을 additive하게 추가한다. 기존 tests를 모두 재실행한다. |
| 새 `app/release_assurance/` | U4 CLI와 tests만 | Medium | FastAPI startup/import graph에서 분리하고 explicit dependency injection과 closed evidence schema를 사용한다. |
| `.release-assurance/` local artifact | 기존 승격 경로와 rollback consumer | Medium | VCS 제외, single-writer lock, temp+fsync+replace, final directory atomic rename, archive digest/locator 계약을 검증한다. |
| pytest/JUnit evidence | 전체 existing/new suite와 73 catalog mapping | High | exact normalized command/environment, exit/counts/output digest, unique stable selector와 missing/duplicate fail-closed 검사를 둔다. |
| `README.md` | 개발자와 운영자 | Low | 실제 명령을 documentation verifier로 파싱하고 기본 자동화/live smoke 분리를 테스트한다. |
| `.gitignore` | local developer workspace | Low | `.release-assurance/`, `.coverage`, `coverage.json`처럼 생성 evidence만 제외하고 application source/plan/manifest는 제외하지 않는다. |

## Planned Source Set

아래 목록이 U4가 만들거나 변경하도록 승인 요청하는 source/test/documentation 범위다. 다른 path가 필요하면 구현 전에 계획을 갱신하고 현재 Guard Policy 절차를 따른다.

| Path | Action | Responsibility |
|---|---|---|
| `app/release_assurance/__init__.py` | create | U4 public release-assurance API export |
| `app/release_assurance/models.py` | create | closed BaselineReceipt, SourceSnapshot, evidence, defect, coverage, documentation, performance와 run schema |
| `app/release_assurance/catalog.py` | create | C03.01~C03.15, C04.01~C04.25, C05.01~C05.27, REL.01~REL.07 exact catalog와 stable pytest selector binding |
| `app/release_assurance/evidence.py` | create | source snapshot, command/environment fingerprint, safe output digest, single-writer bundle, atomic write/finalize/retrieval |
| `app/release_assurance/evaluator.py` | create | catalog completeness, baseline/final comparison, documentation, defect와 terminal release predicate |
| `app/release_assurance/performance.py` | create | fixed-fingerprint NFR8 session/trial ledger와 `met/not_met/not_measured/invalid` 판정 |
| `app/release_assurance/documentation.py` | create | README 필수 topic·명령·기본 자동화/live-smoke 분리 검증 |
| `scripts/release_assurance.py` | create | baseline, run, finalize, show, performance-record/evaluate CLI; 실제 smoke는 실행하지 않음 |
| `scripts/changed_line_coverage.py` | modify | U1~U4 manifest-plan-baseline binding, pre-run freeze, missing coverage source failure와 union denominator |
| `tests/test_release_assurance_models.py` | create | closed schema, revision binding, safe fields와 invalid state tests |
| `tests/test_release_assurance_catalog.py` | create | 73 IDs, phase membership, unique collected pytest selector와 missing/duplicate result tests |
| `tests/test_release_assurance_evidence.py` | create | baseline/final 분리, lock, atomicity, crash recovery, immutable finalize, retention/locator tests |
| `tests/test_release_assurance_evaluator.py` | create | automation/docs/coverage/defect final predicate와 new-revision reverify tests |
| `tests/test_release_assurance_performance.py` | create | 18 fixed trials, fingerprints, UTC/monotonic fields, median/transition/outcome tests |
| `tests/test_release_assurance_documentation.py` | create | README seven topics, executable commands, smoke separation와 credential gate tests |
| `tests/test_release_assurance_integration.py` | create | CLI, JUnit evidence, catalog mapping, final bundle, rollback retrieval의 end-to-end tests |
| `tests/test_release_assurance_security.py` | create | model/tool/log/error/assertion/traceback/stdout/stderr/runner report canary와 network fence tests |
| `tests/test_changed_line_coverage.py` | modify | prior claim union, plan/baseline admission, freeze drift, missing JSON source, backward compatibility tests |
| `tests/test_network_isolation.py` | modify | U4 deliberate bypass와 release evidence counter integration |
| `README.md` | modify | 세 도구, 설정/실행, session·delegated credential, tests/coverage, 별도 live smoke와 NFR8 절차 |
| `.gitignore` | modify | generated `.release-assurance/`, `.coverage`, `coverage.json` 제외 |

`requirements.txt`의 `pytest==9.1.1`과 `coverage==7.17.0`, 기존 `pytest.ini`, FakeModel/MockTransport fixture를 재사용한다. 새 dependency, formatter, linter, type checker, CI provider, container, IaC 또는 cloud resource는 추가하지 않는다.

## Implementation Plan

- [x] **Step 1 — 계약·catalog와 현재 source topology를 고정한다.** Functional/NFR/Infrastructure Design과 C-03~C-07을 대조해 73개 automation check와 REL.07의 phase를 고정하고, 각 check를 고유한 stable pytest node selector에 연결할 inventory를 만든다. 기존 test 수집으로 selector 후보를 검증하며 누락된 계약은 U4 targeted test로 계획한다. Infrastructure review의 R-04는 baseline receipt와 final run을 분리하는 구현 불변식으로 명시한다. **Trace:** US4.1, US5.1; AC4.1.1–AC4.1.6, AC5.1.1–AC5.1.6; BR4.1–BR4.15; C-03~C-07.
- [x] **Step 2 — 별도 변경 전 baseline receipt를 만든다.** 애플리케이션 변경 전에 exact `.venv/bin/python -m pytest -q` 전체 suite를 실행하고 baseline `SourceSnapshot`, normalized command/digest, environment fingerprint, total/pass/fail/skip, exit status, sanitized output digest를 `.release-assurance/baselines/<snapshot>/<receipt-id>/`에 atomic finalize한다. baseline 실패·skip은 숨기지 않고 이후 final 비교 입력으로만 보존한다. **Trace:** US5.1 / AC5.1.2, AC5.1.4; BR4.8, BR4.9, BR4.15; NFR5.1, NFR5.4.
- [x] **Step 3 — release evidence model과 catalog를 구현한 뒤 테스트한다.** Closed Pydantic/dataclass 경계로 source snapshot, BaselineReceipt, ReleaseAssuranceRun, VerificationEvidence, RegressionExecutionEvidence, CoverageAssessment, DefectRoute, DocumentationAssurance와 exact 74-entry catalog(automation 73 + REL.07)를 구현한다. current run에는 final phase만 허용하고 baseline은 locator/digest reference로 분리한다. 각 구성요소당 5~8개 이상으로 unknown/secret field, duplicate ID, invalid state, revision mismatch, count invariant와 stable selector uniqueness를 테스트한다. **Trace:** US4.1, US5.1; AC4.1.1–AC4.1.6; BR4.1, BR4.2, BR4.13–BR4.15; NFR1.5, NFR3.8, NFR5.3–NFR5.6.
- [x] **Step 4 — 원자적 evidence repository를 구현한 뒤 테스트한다.** `.release-assurance/pending/<run-id>` single-writer lock, owner-only directory, temp+flush/fsync+`os.replace`, final manifest digest, pending→final atomic rename, finalize 후 write 거부, predecessor/baseline locator lookup과 7-day pending/90-day+ final retention eligibility를 구현한다. crash point, concurrent writer, partial evidence, digest tamper, cross-revision mixing, rollback retrieval을 테스트한다. **Trace:** US5.1 / AC5.1.4; BR4.13–BR4.15; NFR3.8, NFR4.6, NFR6.3–NFR6.5.
- [x] **Step 5 — manifest-union coverage admission/freeze를 구현한 뒤 테스트한다.** 기존 flat invocation을 보존하면서 U1~U4 각 manifest·approved plan·attempt source baseline의 one-to-one binding, 승인 변경 미claim, plan 밖 claim, baseline 이후 승인 밖 변경, workspace 밖 path를 fail-closed 처리한다. coverage 전 sorted union/digest를 atomic freeze하고 gate에서 bytes를 재검증한다. union source가 coverage JSON에 없으면 반드시 실패하고 prior manifest claim도 denominator에 포함한다. backward-compatibility를 포함해 5~8개 이상 경계와 matrix tests를 실행한다. **Trace:** US5.1 / AC5.1.2, AC5.1.4; BR4.8, BR4.15; NFR6.1–NFR6.4; REL.03.
- [x] **Step 6 — regression/JUnit collector와 secret/network probes를 구현한 뒤 테스트한다.** normalized command와 actual argv digest, Python/pytest/coverage/lock/environment fingerprint, exit status와 JUnit counts를 수집하고 raw output은 secret scan 뒤 digest만 보존한다. model/tool/result/log/error/assertion/traceback/stdout/stderr/runner-report canary 각각을 독립 boundary ID로 검증하고 process network default-deny/bypass result를 evidence에 결합한다. **Trace:** US4.1, US5.1; AC4.1.2–AC4.1.4, AC4.1.6; BR4.2, BR4.7–BR4.9; NFR1.1–NFR1.6, NFR5.1–NFR5.4; REL.01, REL.02, REL.04, REL.05.
- [x] **Step 7 — release evaluator와 defect router를 구현한 뒤 테스트한다.** C03/C04/C05/REL.01~REL.06의 exact 73 evidence, final regression exit/count, coverage >=80, REL.07/documentation, open blocking defect 0을 phase별로 평가한다. missing/stale/duplicate/invalid evidence는 terminal `blocked`, 모두 current면 `release_ready`로 atomic finalize한다. repair revision은 predecessor lineage만 읽고 fresh evidence로만 `reverified` 처리한다. **Trace:** US4.1, US5.1; AC4.1.1–AC4.1.6, AC5.1.2, AC5.1.4; BR4.13–BR4.15; NFR5.5–NFR5.6, NFR6.3, NFR6.5, NFR7.9.
- [x] **Step 8 — NFR8 performance recorder를 구현한 뒤 테스트한다.** UTC observation time, source snapshot/deployment, anonymized role, browser/device/OS/viewport/network/cache fingerprint, method/scenario/trial 1~3, generated-data ref, monotonic times, completion event, result/failure와 transition count를 closed schema로 기록한다. 18개 사전 지정 trial을 교체하지 않고 조건 불일치는 `invalid`, 미실행은 `not_measured`, 정상 실패/median/transition 실패는 `not_met`, 모든 조건 통과만 `met`로 판정한다. **Trace:** US5.1 / AC5.1.3, AC5.1.6; BR4.12, BR4.15; NFR8.1–NFR8.6.
- [x] **Step 9 — documentation verifier와 provider-independent CLI를 구현한 뒤 테스트한다.** baseline receipt, final run create/record/finalize/show, coverage freeze/gate, performance record/evaluate를 explicit subcommand로 제공한다. CLI는 미해결 placeholder, credential 값 출력, implicit live call을 거부한다. README 일곱 topic과 실제 명령을 verifier가 검사하고 `scripts/agent_smoke.py`는 별도 explicit target/user/credential 절차로만 문서화한다. **Trace:** US5.1 / AC5.1.1–AC5.1.6; BR4.10, BR4.11; NFR5.6; REL.07.
- [x] **Step 10 — 73개 catalog와 기존 U1~U3 회귀를 통합 검증한다.** pytest collect/JUnit node ID를 catalog selector와 정확히 일치시키고 missing/duplicate selector를 실패시킨다. exact-three-tool registry, delegated authority, retry/refresh, lifecycle/concurrency, create/update 안전성, API/UI/history/model/accessibility와 documentation을 각각 자기 check ID의 evidence로 만든다. U1~U3 expectation을 바꾸거나 skip/xfail로 통과시키지 않는다. **Trace:** US4.1 / AC4.1.1–AC4.1.6; US5.1 / AC5.1.2, AC5.1.4; C-03~C-07; REL.01~REL.07.
- [x] **Step 11 — U4-scoped tests와 changed-line coverage를 실행한다.** `unit-test-instructions.md`의 exact explicit-path command를 실행하고 실패·skip을 수선한다. final source set을 고정한 뒤 U1~U4 manifest/plan/baseline binding을 freeze하고 `.venv/bin/python -m coverage run --source=app,scripts -m pytest ...`, coverage JSON과 union gate를 실행한다. missing source, input drift, executable line 0 또는 80% 미만을 완화하지 않는다. **Trace:** US5.1 / AC5.1.2, AC5.1.4; BR4.7, BR4.8, BR4.15; NFR5.1, NFR6.1–NFR6.4.
- [x] **Step 12 — final revision run과 전체 회귀·문서를 완결한다.** 구현 완료 content에서 새 final `SourceSnapshot`과 `ReleaseAssuranceRun`을 만들고 Step 2 baseline receipt locator/digest를 비교 입력으로만 연결한다. baseline과 같은 normalized full-suite command/environment로 final regression을 실행하고 coverage, 73 evidence, REL.07, defect 0을 확인한 뒤 bundle을 finalize한다. README와 `.gitignore`를 검증하고 실제 smoke/NFR8 결과는 수행하지 않았다면 `not_measured`로 명시한다. `code-summary.md`, `source-manifest.json`, `traceability.json`에 실제 결과와 미완료 evidence를 정직하게 기록한다. **Trace:** US4.1, US5.1; 모든 U4 AC; BR4.8–BR4.15; REL.01~REL.07.

## Test File Plan

| Test file | Component coverage | Standard-strategy volume |
|---|---|---|
| `tests/test_release_assurance_models.py` | closed schema, source/revision binding, safe field와 state invariants | 5–8+ cases plus invalid-field matrix |
| `tests/test_release_assurance_catalog.py` | exact 74 catalog, 73 automation membership, unique collected selectors | 5–8+ cases plus 74-row parameterization |
| `tests/test_release_assurance_evidence.py` | baseline/final separation, atomic repository, lock/crash/tamper/retention/retrieval | 8+ cases |
| `tests/test_release_assurance_evaluator.py` | completeness, regression, coverage, docs, defect와 terminal predicate | 8+ cases plus failure matrix |
| `tests/test_release_assurance_performance.py` | fingerprints, fixed trials, medians, transitions와 four outcomes | 8+ cases plus scenario matrix |
| `tests/test_release_assurance_documentation.py` | README topics, command consistency, smoke separation | 5–8+ cases |
| `tests/test_release_assurance_integration.py` | CLI→JUnit/catalog→coverage→final bundle→retrieval end-to-end | 5–8+ cases |
| `tests/test_release_assurance_security.py` | all secret/test-failure surfaces and network isolation | 8+ cases plus boundary matrix |
| `tests/test_changed_line_coverage.py` | union, plan/baseline admission, freeze drift, missing source, legacy CLI | 8+ new/updated cases |
| `tests/test_network_isolation.py` | default-deny and deliberate bypass evidence | 3+ existing/updated cases |

Parameterized catalog와 canary matrices는 표시된 숫자보다 많은 pytest case를 만들 수 있다. 숫자를 맞추기 위해 named contract boundary를 합치거나 생략하지 않는다.

## Completion Criteria

- baseline은 별도 finalized receipt이고 final current-run evidence에 포함되거나 복사되지 않는다. final run은 구현 완료 content-addressed source snapshot에만 결합된다.
- Required Verification Catalog는 74개(C03 15 + C04 25 + C05 27 + REL 7)이며 automation completeness는 REL.07을 제외한 73개다. 각 automation check는 하나의 고유 collected pytest selector와 current passed evidence를 가진다.
- U1~U4 manifest claim은 각 approved plan과 attempt baseline에 결합되고 coverage 전에 freeze된다. prior claims가 denominator에 포함되고 coverage JSON의 union source 누락은 실패한다.
- final regression은 baseline과 동일한 normalized command/environment를 사용하고 exit 0, failed 0, skipped 0이다. 실제 OpenAI/ITSM network attempt와 secret canary exposure는 0이다.
- evidence bundle은 single-writer, atomic record/finalize, immutable final, predecessor/baseline locator/digest와 최소 retention 규칙을 지킨다. terminal/UI는 bundle projection만 사용한다.
- release predicate는 automation 73/73, coverage >=80%, REL.07/documentation passed, open blocking defect 0일 때만 `release_ready`다.
- NFR8은 full field schema와 18 fixed-trial 판정을 구현하되 실제 환경에서 실행하지 않았다면 성공으로 간주하지 않는다.
- README 명령이 실제 CLI와 일치하고 기본 자동화와 explicit live smoke를 분리한다. 새 CI/CD, cloud resource, service, runtime database나 dependency를 추가하지 않는다.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "test-after",
  "source": "team",
  "ordering": "각 테스트 가능한 계층을 구현한 직후 그 계층의 pytest 테스트를 작성·실행하고, 마지막에 실제 OpenAI 호출이 없는 전체 회귀 테스트를 실행한다.",
  "scope": "feature",
  "test_strategy": "standard",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra`, `classic` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: test-after\n- **Ordering**: 각 테스트 가능한 계층을 구현한 직후 그 계층의 pytest 테스트를 작성·실행하고, 마지막에 실제 OpenAI 호출이 없는 전체 회귀 테스트를 실행한다.\n- **Methodology evidence**: 저장소에는 pytest 통합·회귀 테스트, FakeModel, `httpx.MockTransport` 패턴이 있지만 테스트 선작성 이력은 입증되지 않았으며, 팀은 현재 구조와 조직 기본값에 맞춰 `test-after`를 선택했다.\n- 세 function tool의 schema·호출, ITSM v2 계약, 사용자 위임과 가시성, 토큰 갱신, 비밀정보 비노출, 등록 멱등성, 수정 `If-Match`, 오류 정제, 기존 사용자 전환·세션·대화 이력·고정 모델 회귀를 자동화 테스트로 다룬다.\n- 실제 OpenAI API와 실제 ITSM은 호출하지 않고 FakeModel과 MockTransport를 사용한다. 문서화된 기존 37개 테스트 기준선은 코드 변경 전후에 재실행한다.\n- feature 범위에는 조직 기준인 80% line coverage floor를 적용한다. 현재 저장소에는 coverage 측정 도구나 임계값 설정이 없으므로, 이 기능의 테스트·검증 설계에서 측정 방법을 구체화해야 한다."
    },
    {
      "layer": "project",
      "text": "- R-17은 runtime infrastructure 추가가 아니라 기존 promotion gate에 deterministic concurrency evidence를 추가하는 변경으로 해석했다. barrier event, direct row count, response/publication counter가 blocking evidence다. (learned 2026-10-25) \n\n- 테스트는 시간 기반 flaky race 대신 controllable Runner history-write barrier와 fake clock을 사용한다. 실제 경쟁 순서를 결정적으로 고정하면서 production lock 경계를 그대로 통과시킨다. (learned 2026-10-25) \n\n- NFR3.2와 credential refresh 보강은 새 runtime resource가 아니라 기존 승격 경로의 blocking test contract로 반영했다. confirmation CAS, U2 ledger isolation, crash-before-bind, pre-call/401 shared refresh budget을 각각 관찰 가능한 counter와 snapshot으로 검증한다. (learned 2026-10-25) \n\n- brownfield의 기존 60초 token refresh margin과 server UTC clock을 pre-call usability predicate로 명시하고, gateway-only accessor의 preflight를 첫 public gateway call 내부이지만 첫 socket I/O 이전의 단계로 고정했다. (learned 2026-10-25) \n\n- whole-application 80% threshold를 새로 만들지 않고 changed-source JSON을 U1의 유일한 coverage 판정으로 삼았다. network 차단은 특정 CI provider 방화벽 대신 pytest process의 DNS/TCP default-deny fixture와 deliberate bypass probe로 증명한다. (learned 2026-10-25)"
    }
  ],
  "obligations": {
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
    ],
    "scope_floor": [
      "Meet an 80% line-coverage floor.",
      "Run the selected tests in CI before merge."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "test-after",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Data model / database behavior - implement.",
      "Data model / database behavior - write and run its tests after implementation.",
      "Repository / data access - implement.",
      "Repository / data access - write and run its tests after implementation.",
      "Business logic - implement.",
      "Business logic - write and run its tests after implementation.",
      "API / endpoint - implement.",
      "API / endpoint - write and run its tests after implementation.",
      "Frontend behavior - implement.",
      "Frontend behavior - write and run its tests after implementation.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:064ee5cc387154391a720806c9fb88310bb87df6291570937ed25a9136f4d036",
  "contract_sha256": "sha256:7c1a2133be59b30537538045547c2115814b810c08e1659e4f43987ab18922ae"
}
```
