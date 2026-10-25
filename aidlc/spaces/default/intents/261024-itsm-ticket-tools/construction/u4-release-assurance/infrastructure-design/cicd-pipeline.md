# U4 CI/CD Pipeline Design

## Sources

- `../nfr-design/reliability-design.md`
- `../nfr-design/observability-design.md`
- `../nfr-design/security-design.md`
- `../functional-design/functional-spec.md`
- `infrastructure-specification.md`
- `monitoring-design.md`

## Pipeline Boundary

저장소에는 프로젝트 소유 CI workflow나 deployment IaC가 없고 팀은 새 CI/CD를 만들지 않기로 확정했다. 따라서 이 문서는 공급자 설정이 아니라 기존 저장소 밖 승격 경로가 실행해야 하는 portable blocking contract를 정의한다. U4 Code Generation은 이를 실행·검증할 repository test/helper와 README 명령을 구현한다.

## Reproducible Execution Profile

| Field | Required value/evidence |
|---|---|
| Runtime | Python 3.13 version string과 executable identity |
| Dependencies | `requirements.txt`의 pinned versions; `pytest==9.1.1`, `coverage==7.17.0`을 evidence에 기록 |
| Source identity | tested source revision과 approved coverage base revision |
| Environment fingerprint | OS, architecture, Python, pytest, coverage, dependency-lock digest, locale/timezone, relevant non-secret config names/digest |
| Network | 기본 automation은 FakeModel/MockTransport와 pytest process default-deny |
| Secret handling | 실제 값은 evidence/output에 기록하지 않고 secret presence와 canary boundary ID만 허용 |
| Clock/concurrency | fake clock, controllable barrier와 deterministic scheduler fixture 사용 |

## Command Registry

명령은 argument vector를 POSIX shell 실행 전 형태로 정규화하고 UTF-8 bytes의 SHA-256을 계산한다. evidence는 아래 command ID, exact normalized text, digest, tool version, start/end UTC와 exit status를 모두 보존한다.

| Command ID | Normalized command | Purpose |
|---|---|---|
| `REGRESSION_FULL_V1` | `.venv/bin/python -m pytest -q` | baseline과 final의 동일 전체 회귀 명령 |
| `COVERAGE_FREEZE_V1` | `.venv/bin/python scripts/changed_line_coverage.py --freeze-output <RUN_DIR>/coverage-inputs.json --source-manifest <U4_MANIFEST> --approved-plan <U4_APPROVED_PLAN> --source-baseline <U4_SOURCE_BASELINE> --prior-source-manifest <U1_MANIFEST> --prior-approved-plan <U1_APPROVED_PLAN> --prior-source-baseline <U1_SOURCE_BASELINE> --prior-source-manifest <U2_MANIFEST> --prior-approved-plan <U2_APPROVED_PLAN> --prior-source-baseline <U2_SOURCE_BASELINE> --prior-source-manifest <U3_MANIFEST> --prior-approved-plan <U3_APPROVED_PLAN> --prior-source-baseline <U3_SOURCE_BASELINE> --include='app/**/*.py'` | 각 Unit의 claim·승인 source set·attempt baseline을 대조하고 coverage 전 immutable input bundle 고정 |
| `COVERAGE_ERASE_V1` | `.venv/bin/python -m coverage erase` | stale coverage data 제거 |
| `COVERAGE_RUN_V1` | `.venv/bin/python -m coverage run --source=app -m pytest -q` | 전체 suite를 통한 application coverage 수집 |
| `COVERAGE_JSON_V1` | `.venv/bin/python -m coverage json -o coverage.json` | pinned coverage 7.17 JSON 생성 |
| `COVERAGE_GATE_V1` | `.venv/bin/python scripts/changed_line_coverage.py --base <APPROVED_BASE> --coverage-json coverage.json --source-manifest <U4_MANIFEST> --prior-source-manifest <U1_MANIFEST> --prior-source-manifest <U2_MANIFEST> --prior-source-manifest <U3_MANIFEST> --approved-plan <U4_APPROVED_PLAN> --source-baseline <U4_SOURCE_BASELINE> --include='app/**/*.py' --fail-under 80 --frozen-input <RUN_DIR>/coverage-inputs.json` | frozen U1~U4 binding과 현재 bytes를 재검증한 manifest 합집합 changed executable line 판정 |
| `LIVE_SMOKE_V1` | `.venv/bin/python scripts/agent_smoke.py --base-url <EXPLICIT_TARGET> --user <EXPLICIT_TEST_USER>` | 사람이 별도로 선택한 실제 연동 smoke; 기본 automation에서 실행 금지 |

`<U1_MANIFEST>`~`<U4_MANIFEST>`, 각 `<U*_APPROVED_PLAN>`, 각 `<U*_SOURCE_BASELINE>`, `<RUN_DIR>`와 `<APPROVED_BASE>`는 shell에 미해결 placeholder로 전달하지 않는다. 기존 승격 runner가 검증한 workspace-relative 실제 경로/revision으로 치환한 뒤 치환된 normalized command와 digest를 evidence에 기록한다. Code Generation은 기존 flat invocation을 유지하면서 `--freeze-output`, 반복 가능한 `--prior-approved-plan`/`--prior-source-baseline`, `--frozen-input`을 additive하게 구현하거나 같은 계약의 wrapper를 제공해야 한다.

## Stage-to-Gate Mapping

| Stage | Action | Blocking gate/evidence |
|---|---|---|
| 1. Baseline preflight | 구현 전 clean baseline source revision, pinned dependencies와 environment fingerprint를 고정하고 exclusive baseline lock/ID를 만든다. | source/env/command fingerprint가 하나라도 없으면 baseline 실행 금지 |
| 2. Baseline regression receipt | 구현 전에 `REGRESSION_FULL_V1`을 실행하고 결과를 별도 immutable baseline receipt로 finalize한다. | exit 0, failed 0, skipped 0; normalized command/digest/count/output digest, baseline revision과 receipt locator/digest 필수 |
| 3. Implement/test-after | 각 testable layer 구현 직후 관련 pytest subset을 실행한다. baseline receipt는 read-only이며 이 단계의 변경을 같은 run에 쓰지 않는다. | 관련 C03/C04/C05/REL check가 개별 ID로 통과해야 함 |
| 4. Final-run preflight | 구현 완료 뒤 final tested source revision을 고정하고 새 `ReleaseAssuranceRun`을 만든다. baseline receipt locator/digest와 predecessor locator/digest를 비교 입력으로 결합하고, baseline 실행 payload를 복사하지 않는 current-run `BaselineReceiptReference(check_id=REL.01)`를 만든다. | final revision/env/binding fingerprint, immutable baseline receipt 또는 reference identity 검증이 하나라도 실패하면 current run 생성 금지 |
| 5. Final regression | final run에서 baseline과 정확히 같은 `REGRESSION_FULL_V1`과 environment profile을 실행한다. | exit 0, failed 0, skipped 0; baseline receipt와 command ID/digest/environment 동일, final source revision 일치 |
| 6. Coverage input freeze | `COVERAGE_FREEZE_V1`로 U1~U4 claim을 각 승인 source set과 attempt baseline에 대조하고 manifest/binding digest와 sorted union을 원자적으로 고정한다. | 승인 변경 미claim, plan 밖 claim, baseline 이후 승인 밖 변경, binding 배열 불일치 시 즉시 실패 |
| 7. Coverage collect | frozen input 생성 뒤 ERASE → RUN → JSON을 순서대로 실행하고 각 command status를 기록한다. | 세 command 모두 exit 0, coverage version 7.17.0 |
| 8. Manifest-union gate | `COVERAGE_GATE_V1`이 frozen digest와 현재 manifest/plan/baseline bytes를 재검증한 뒤 판정한다. | input drift 0, coverage JSON에 union source 전부 존재, >= 80% |
| 9. Security/release evaluation | NetworkFence, SecretBoundaryProbe, final revision에 직접 생성된 72개 evidence와 `REL.01` baseline reference 1개를 합성해 73개 automation outcome 및 open defect를 평가한다. | final 72/72와 REL.01 reference 1/1, missing/duplicate/fail 0, network 0, bypass blocked 1, secret exposure 0, defect 0 |
| 10. Documentation | README topic, automation/live-smoke 분리와 명령 일치를 REL.07로 검증한다. | REL.07과 DocumentationAssurance passed; 실패 시 terminal `blocked` |
| 11. Atomic finalize/promotion handoff | required current-run evidence digest set과 terminal predicate를 lock 아래 검증하고 pending directory를 final path로 atomic rename한 뒤 archive digest/locator를 기존 승격 경로에 전달한다. | finalized `release_ready` bundle과 final source revision이 일치할 때만 승격 가능 |
| 12. Optional live validation | 사람이 credential/target/test data/cleanup과 실행 의사를 명시한 경우에만 smoke와 NFR8을 별도 실행한다. | 결과는 별도 상태이며 자동화 실패를 덮거나 `release_ready` evidence를 대체하지 않음 |

## Coverage Gate Contract

1. U1~U4마다 `source-manifest.json`, 승인된 `code-generation-plan.md`의 Planned Source Set, 해당 attempt의 engine source-baseline TSV를 한 binding으로 받는다. 세 반복 배열은 Unit ID와 개수가 정확히 일치해야 한다.
2. 각 manifest claim이 자기 승인 source set 안에 있는지, 승인 set에서 baseline 이후 변경된 application path가 claim되지 않았는지, baseline 이후 승인 밖 application 변경이 없는지 fail-closed로 검사한다.
3. application source claim만 허용하고 test, docs, generated file과 workspace 밖 경로를 거부한다.
4. coverage 실행 전에 binding path/content digest, 각 manifest digest, sorted union path set과 union digest를 `<RUN_DIR>/coverage-inputs.json`에 temp+fsync+replace로 고정한다.
5. ERASE/RUN/JSON 뒤 gate 시작 시 모든 binding bytes와 union을 다시 계산해 frozen digest와 비교한다. 불일치하면 coverage result를 폐기한다.
6. approved base와 tested revision 사이의 union source changed executable lines를 계산한다. prior manifest claim도 denominator에 포함한다.
7. union의 application source가 coverage JSON에 없으면 changed-line 수가 0으로 보이더라도 `missing coverage source: <path>`로 실패한다.
8. denominator 0은 union에 실제 application change가 없음을 모든 Unit baseline/plan 대조로 증명한 경우만 통과한다.
9. output에는 tool version, freeze/run/json/gate command ID·digest·exit status, revisions, 모든 binding path/digest, manifests, sorted paths, line counts, percentage, threshold를 포함한다.
10. 기존 U1~U3 단일-manifest flat invocation 의미는 유지한다. 새 freeze와 prior plan/baseline union 검증은 additive하다.

## Regression Evidence Contract

- baseline은 구현 전 revision의 별도 immutable `BaselineRegressionReceipt`이고 final은 구현 완료 revision의 current `ReleaseAssuranceRun` evidence다. 두 revision의 evidence를 한 run에 저장하거나 baseline record를 final run으로 복사하지 않는다.
- final run은 current revision에 결합된 `BaselineReceiptReference` 하나로 baseline receipt locator/digest를 검증하고 실제 normalized command text와 digest, environment fingerprint를 비교한다. 이 reference에는 baseline locator/digest/revision, expected command/environment digest와 validation result/time만 허용하며 baseline count, output digest, 시작/종료 시각 또는 전체 실행 record를 넣지 않는다. 사람이 붙인 label만 같은 것은 동일 명령으로 인정하지 않는다.
- `REL.01`은 `BaselineReceiptReference` validator가 locator/digest로 별도 receipt를 역참조해 receipt의 exit 0·failed 0·skipped 0과 immutable finalize를 확인할 때만 passed다. 그 reference 1개와 final revision의 C03/C04/C05 및 REL.02~REL.06 evidence 72개가 합쳐져 catalog 73개를 이룬다.
- final run의 `RegressionExecutionEvidence`는 phase=`final` 하나뿐이다. Functional Design이 말하는 phase=`baseline` 실행 record는 별도 baseline receipt에 보존되고, final run에는 locator/digest relationship만 존재한다.
- stdout/stderr 원문 대신 secret scan을 통과한 output digest와 count를 저장한다. 실패 보고에는 check ID와 safe message만 둔다.
- baseline receipt와 final evidence의 Python, pytest, dependency-lock, OS/architecture, locale/timezone, non-secret configuration fingerprint가 같아야 비교 가능하다.
- exit status, total, passed, failed, skipped가 모두 필수다. parser가 count를 얻지 못하면 evidence는 invalid다.
- 일부 subset 성공은 `REGRESSION_FULL_V1`을 대체하지 않는다.
- final source revision은 current run 생성 뒤 불변이다. 구현 수선 또는 어떤 source write라도 발생하면 그 run을 재사용하지 않고 새 revision/new run에서 final regression 이후 모든 evidence를 다시 만든다.

## Release Predicate and Defect Routing

```text
final_revision_automation_current(72/72)
AND REL.01_baseline_reference_current(1/1)
AND referenced_immutable_baseline_receipt_valid
AND regression_final_valid
AND coverage_commands_all_exit_zero
AND manifest_union_coverage >= 80
AND network_and_secret_boundaries_passed
AND REL.07_and_documentation_passed
AND open_blocking_defects = 0
AND authoritative_bundle_finalized_atomically
```

위 첫 두 항목을 합성한 automation catalog count만 73/73으로 표시한다. final revision evidence 72개와 REL.01 reference 1개를 모두 current run identity에 결합하되, baseline 실행 payload는 별도 receipt에만 남는다. 어느 항목이든 거짓이면 현재 revision run은 terminal `blocked`, 모두 참이면 `release_ready`다. 실패는 check ID, owning Unit, C-01~C-07 reference와 연결한다. 수선된 revision은 predecessor finalized-bundle locator/digest를 가진 새 run에서 전체 catalog, full regression, coverage, documentation을 새로 실행한다. 현재 predicate는 predecessor evidence를 입력으로 사용하지 않는다.

## Deployment, Promotion, and Rollback

- 이 Unit은 blue-green/canary/rolling/recreate 중 새 방식을 선택하지 않는다. 기존 저장소 밖 배포 방식과 환경 보호를 유지한다.
- staging 승격 전 finalized bundle archive의 locator/digest와 `release_ready`를 blocking input으로 사용한다.
- production 승격은 기존 조직 절차의 별도 사람 승인을 유지한다. U4는 승인자를 추측하거나 자동 승인하지 않는다.
- 배포 전 rollback 기준은 기존 정상 revision과 promotion receipt가 가리키는 finalized bundle이다. 배포 오류 시 archive locator/digest로 bundle을 검증한 뒤 기존 배포 경로로 직전 정상 revision을 재승격하고, 실패 revision은 새 evidence 없이 재사용하지 않는다.
- schema ownership과 migration order가 변하지 않으므로 U4 자체 rollback용 migration은 없다.

## Secrets Management

- CI/승격 환경의 credential 주입 방식은 기존 경로가 소유한다. 저장소·command text·artifact·log에 값을 넣지 않는다.
- 기본 자동화는 실제 OpenAI/ITSM credential 없이 통과해야 한다.
- live smoke는 credential 존재만 확인하고 값은 출력하지 않으며 explicit target과 test user를 요구한다.
- secret canary failure는 `secret boundary violation: <boundary-id>`만 출력한다.

## NFR8 Measurement Gate

NFR8은 승격 자동화와 분리하되 비교 규칙은 고정한다.

1. session 시작 시 UTC observation time, source revision, deployment ID, anonymized account role, browser name/version, device class, OS, viewport, network profile, cache state를 고정한다.
2. method(`assistant`, `existing_ui`) × scenario(`read`, `create`, `update`)마다 warm-up 1회를 제외하고 trial 1·2·3을 사전 생성한다.
3. 각 trial은 generated-data reference, monotonic start/end, duration, completion event, success/failure reason, screen transitions를 기록한다.
4. browser/device/OS/deployment/role/network/cache fingerprint가 하나라도 달라지거나 필수 field가 없으면 전체 session은 `invalid`다.
5. 정상 조건 실패는 해당 번호를 `not_met`으로 보존하며 replacement trial을 금지한다. 미실행은 `not_measured`다.
6. 한 scenario의 두 method 모두 지정된 세 trial이 성공한 경우만 각 median을 계산한다.
7. Assistant median이 existing UI보다 짧고 Assistant trial 세 개의 external screen transition이 모두 0일 때만 scenario가 `met`이다.

## Assumptions & Open Questions

None.
