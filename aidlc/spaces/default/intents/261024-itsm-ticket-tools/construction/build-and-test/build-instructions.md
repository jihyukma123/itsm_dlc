# Build Instructions

## Sources

- `construction/u1-ticket-read-skeleton/code-generation/code-generation-plan.md`
- `construction/u2-ticket-write/code-generation/code-generation-plan.md`
- `construction/u3-ticket-update/code-generation/code-generation-plan.md`
- `construction/u4-release-assurance/code-generation/code-generation-plan.md`
- 각 Unit의 `unit-test-instructions.md`와 `code-summary.md`
- `aidlc-state.md`의 Construction Verification Command

## Prerequisites

- 저장소 루트 `/Users/jihyukma/Documents/c/itsm_dlc`에서 실행한다.
- Python 3.13과 저장소의 `.venv`를 사용한다.
- `requirements.txt`의 고정 버전을 사용하며 실제 OpenAI·ITSM credential은 설정하지 않는다.
- 테스트 트래픽은 FakeModel과 `httpx.MockTransport`만 사용하고 process-level network default-deny를 유지한다.

## Environment Setup

신규 서비스, container, cloud resource 또는 로컬 daemon은 필요하지 않다. 의존성 재설치가 필요할 때만 다음 명령을 사용한다.

```bash
.venv/bin/python -m pip install -r requirements.txt
```

U2 create-refresh 경로의 설정 검증은 테스트 fixture가 제공한다. 실제 secret 값을 Build and Test 환경이나 산출물에 기록하지 않는다.

## Build and Verification Commands

Python source의 import·syntax 준비 상태를 먼저 확인한다.

```bash
.venv/bin/python -m compileall -q app scripts
```

그다음 각 Unit의 exact pytest 명령을 한 번씩 실행하고, 마지막에 기록된 Construction Verification Command를 실행한다.

```bash
.venv/bin/python -m coverage run --source=app -m pytest -q
.venv/bin/python -m coverage report --fail-under=80
```

## Pass Criteria

- compileall exit code 0
- U1~U4 exact suite exit code 0
- 전체 회귀 failed 0, skipped 0, exit code 0
- application line coverage 80% 이상
- 실제 OpenAI·ITSM network attempt 0, secret canary exposure 0
- `git diff --check` 통과

## Troubleshooting

- 테스트 수가 달라지면 누락된 test file 또는 collection 오류부터 확인하고 예상 수를 낮추지 않는다.
- coverage가 80% 미만이면 누락된 실제 동작 테스트를 추가하며 threshold나 source scope를 줄이지 않는다.
- network 차단 실패는 live 호출을 허용하지 말고 MockTransport 등록과 fixture 범위를 고친다.
- 실제 환경 NFR8 측정은 이 명령에 섞지 않고 예정된 Performance Validation에서 별도 실행한다.
