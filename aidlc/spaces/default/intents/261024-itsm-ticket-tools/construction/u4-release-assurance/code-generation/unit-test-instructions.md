# U4 Release Assurance Unit Test Instructions

## Scope

이 명령은 U4가 새로 만들거나 직접 변경하는 release-assurance, coverage와 network-evidence 테스트만 실행한다. 전체 repository regression은 U4 완료 판정에서 별도로 한 번 실행하며 이 Unit-scoped 명령을 대체하지 않는다.

## Framework and Configuration

- Python 3.13
- `pytest==9.1.1`
- `coverage==7.17.0`
- 기존 `pytest.ini`, `tests/conftest.py`, FakeModel, `httpx.MockTransport`, fake clock/barrier와 autouse network deny fixture 재사용
- 새 plugin, 외부 service, 실제 OpenAI/ITSM credential 불필요

## Exact Unit Command

```bash
.venv/bin/python -m pytest -q tests/test_release_assurance_models.py tests/test_release_assurance_catalog.py tests/test_release_assurance_evidence.py tests/test_release_assurance_evaluator.py tests/test_release_assurance_performance.py tests/test_release_assurance_documentation.py tests/test_release_assurance_integration.py tests/test_release_assurance_security.py tests/test_changed_line_coverage.py tests/test_network_isolation.py
```

## Layer Commands

Test-after 순서를 지키기 위해 각 구현 layer 직후 다음 명령을 실행한다.

```bash
.venv/bin/python -m pytest -q tests/test_release_assurance_models.py tests/test_release_assurance_catalog.py
.venv/bin/python -m pytest -q tests/test_release_assurance_evidence.py tests/test_changed_line_coverage.py
.venv/bin/python -m pytest -q tests/test_release_assurance_evaluator.py tests/test_release_assurance_documentation.py
.venv/bin/python -m pytest -q tests/test_release_assurance_performance.py
.venv/bin/python -m pytest -q tests/test_release_assurance_integration.py tests/test_release_assurance_security.py tests/test_network_isolation.py
```

## Coverage Command

U4 Code Generation이 만든 source manifest와 승인 plan/source baseline, U1~U3 prior binding의 실제 경로를 사용한다. 아래 placeholder는 실행 전에 검증된 workspace-relative path와 revision으로 치환하며 literal placeholder를 shell에 전달하지 않는다.

```bash
.venv/bin/python -m coverage erase
.venv/bin/python -m coverage run --source=app,scripts -m pytest -q tests/test_release_assurance_models.py tests/test_release_assurance_catalog.py tests/test_release_assurance_evidence.py tests/test_release_assurance_evaluator.py tests/test_release_assurance_performance.py tests/test_release_assurance_documentation.py tests/test_release_assurance_integration.py tests/test_release_assurance_security.py tests/test_changed_line_coverage.py tests/test_network_isolation.py
.venv/bin/python -m coverage json -o coverage.json
.venv/bin/python scripts/changed_line_coverage.py --base <APPROVED_BASE> --coverage-json coverage.json --source-manifest <U4_MANIFEST> --prior-source-manifest <U1_MANIFEST> --prior-source-manifest <U2_MANIFEST> --prior-source-manifest <U3_MANIFEST> --approved-plan <U4_APPROVED_PLAN> --source-baseline <U4_SOURCE_BASELINE> --include='app/**/*.py' --fail-under 80 --frozen-input <RUN_DIR>/coverage-inputs.json
```

Coverage gate 구현은 `app/**/*.py`와 `scripts/**/*.py` 두 application-source pattern을 같은 frozen union에 포함할 수 있어야 한다. 기존 단일 `--include` 호출은 계속 동작해야 하며 U4 명령은 repeatable include 또는 동등한 wrapper로 두 pattern을 명시한다.

## Full Regression Comparison

변경 전에는 별도 immutable baseline receipt를 만들고, 구현 완료 후에는 content-addressed final source snapshot의 새 run에서 아래와 정확히 같은 normalized command와 environment fingerprint로 final evidence를 만든다.

```bash
.venv/bin/python -m pytest -q
```

- baseline receipt locator/digest만 final run의 비교 입력으로 사용한다.
- baseline evidence를 final run으로 복사하거나 final source revision이라고 표시하지 않는다.
- final은 exit status 0, failed 0, skipped 0이어야 한다.

## Expected Test Volume and Coverage

- Standard strategy: 구성요소별 5~8개 이상의 focused tests
- 예상 신규·변경 U4 cases: 약 45~65개, catalog/canary parameterization은 별도
- Required catalog: 총 74개, automation completeness 73개 + documentation `REL.07` 1개
- U4 및 prior manifest 합집합 changed executable application lines: 80% 이상
- unexpected real network attempts: 0
- deliberate bypass blocked: 1 이상
- secret canary exposures: 0
- skip/xfail로 필수 계약을 숨기지 않는다.

## Mocking and Isolation

- Agent 호출은 기존 FakeModel을 사용한다.
- ITSM HTTP는 `httpx.MockTransport`만 사용한다.
- 시간·retry·concurrency는 fake UTC/monotonic clock과 controllable barrier를 사용한다.
- filesystem atomicity는 `tmp_path` 안의 release bundle과 injected replace/fsync/crash seam으로 검증한다.
- pytest/JUnit 결과는 fixture XML로 파싱하되 실제 전체 suite를 Unit test마다 재실행하지 않는다. CLI end-to-end는 작은 nested fixture suite만 사용한다.
- socket/DNS는 기존 autouse default-deny를 유지하고 deliberate bypass test로 실제 차단을 증명한다.

## Test Data Management

- ticket payload와 운영 ticket ID를 fixture/code/documentation에 하드코딩하지 않는다.
- source revision과 run/receipt IDs는 test-local deterministic factory 또는 content digest로 만든다.
- distinct secret canary를 credential 종류와 output boundary마다 사용하지만 failure message에는 boundary ID만 남긴다.
- performance data는 generated reference와 익명 role만 사용하고 2 methods × 3 scenarios × 3 fixed trials를 생성한다.
- `.release-assurance/`, `.coverage`, `coverage.json`은 생성 artifact이며 VCS에 포함하지 않는다.

## Failure Handling

- missing/duplicate catalog selector, manifest/plan/baseline drift, coverage source 누락, command/environment mismatch, partial bundle, revision mismatch는 fail-closed다.
- coverage threshold나 expected count를 낮추거나 skip/xfail를 추가해 통과시키지 않는다.
- 실제 smoke와 NFR8 실측이 실행되지 않았으면 `not_measured`로 남기고 자동화 성공으로 대체하지 않는다.
