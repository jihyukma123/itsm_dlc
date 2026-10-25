# U4 Tech Stack Decisions

## Sources

- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md`
- `inception/practices-discovery/team-practices.md`
- `inception/contract-design/contract-summary.md`
- `inception/requirements-analysis/requirements.md`

## Decisions

| Decision | Selection | Rationale | NFR impact |
|---|---|---|---|
| Runtime | Python 3.13 | 기존 application과 test runtime을 보존한다. | NFR5.2 |
| Web framework | FastAPI 0.162.0, Starlette 1.10.0, Uvicorn 0.54.0 | 기존 API·DI·response model 동작을 유지한다. | NFR5.2 |
| Schema validation | Pydantic 2.14.1 | 기존 API와 tool input/output의 명시적 validation 경계다. | NFR1.2, NFR3.3 |
| Agent runtime | openai-agents 0.24.0, openai 3.37.0 | 기존 Agent·Runner·SQLiteSession, 고정 model/reasoning을 유지한다. | NFR5.2, NFR5.3 |
| ITSM transport | httpx 0.28.1 | 기존 AsyncClient lifecycle과 MockTransport 계약 검증을 재사용한다. | NFR1.4, NFR7.1~NFR7.4 |
| Persistence | 기존 server-session SQLite와 Agents SDK SQLiteSession | U1~U3 namespace ownership과 단일 배포를 보존한다. | NFR3.1~NFR3.8 |
| Automated test | pytest 9.1.1, FakeModel, `httpx.MockTransport` | 실제 OpenAI·ITSM 없이 결정적 계약·회귀 검증이 가능하다. | NFR1.4, NFR5.1 |
| Coverage | `coverage==7.17.0`과 `scripts/changed_line_coverage.py` | `requirements.in`/`requirements.txt`에 고정된 기존 의존성과 manifest-aware project script로 80% changed-line floor를 재현한다. formatter·linter·type checker나 새 CI stack 도입이 아니다. | NFR6.1, NFR6.2, NFR6.4 |
| Browser | 기존 build 없는 JavaScript·HTML·CSS | 새 UI나 bundler 없이 기존 접근성·API 호환을 검증한다. | NFR5.2, NFR9.1~NFR9.3 |

## Fixed Product Configuration

- model `gpt-6-luna`, reasoning effort `high`, SDK tracing 비활성을 유지한다.
- 실제 OpenAI와 실제 ITSM은 기본 automated suite에서 호출하지 않는다.
- 새 formatter, linter, type checker, CI/CD provider, container, cloud IaC 또는 monitoring stack을 이번 Unit의 필수 요소로 추가하지 않는다.
- 실제 연동 smoke는 명시적 credential과 대상 environment가 있을 때만 별도 절차로 실행한다.

## Coverage Execution Contract

1. `.venv/bin/python -m coverage run --branch --source=app -m pytest -q`로 전체 suite coverage data를 생성한다.
2. `.venv/bin/python -m coverage json -o coverage.json`으로 기계 판정 입력을 만든다.
3. `.venv/bin/python scripts/changed_line_coverage.py --base <approved-base-revision> --coverage-json coverage.json --source-manifest <u4-source-manifest.json> --prior-source-manifest <u1-source-manifest.json> --prior-source-manifest <u2-source-manifest.json> --prior-source-manifest <u3-source-manifest.json> --approved-plan <u4-approved-plan.md> --source-baseline <attempt-source-baseline.tsv> --include 'app/**/*.py' --fail-under 80`으로 manifest-bound changed application line coverage를 판정한다.
4. `<...>` 값은 Code Generation이 승인된 plan과 현재 attempt receipt에서 확정하는 경로이며 임의 revision이나 빈 manifest로 대체하지 않는다.
5. evidence에는 tool version, base revision, tested revision, manifest digest·paths, covered/executable changed lines, percentage, threshold와 각 command exit status를 기록한다.

## Alternatives Rejected

- 새 test runner 또는 browser framework: 기존 pytest/FakeModel/MockTransport만으로 요구된 계약과 UI 회귀를 검증할 수 있고 새 의존성은 범위 밖이다.
- 별도 release evidence service: 기존 단일 application·repository 범위를 벗어나며 새 runtime infrastructure가 된다.
- 실제 외부 API를 자동화 gate에 사용: 비결정성, 비용, credential 노출과 의도하지 않은 mutation 위험이 있다.

## Assumptions & Open Questions

None.

