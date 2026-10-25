# Cross-Unit Traceability

## Sources

- U1~U4 `code-generation/traceability.json`
- U1~U4 `code-generation/source-manifest.json`
- `aidlc engine sensor-traceability --stage build-and-test`

## Verdict

**FAIL** — 기능과 자동화 테스트 파일은 workspace에 존재하고 679개 전체 회귀가 통과했지만, U4 traceability의 일부 target 문자열이 여러 경로와 설명을 한 문자열에 결합해 파일 존재 확인에 실패했다. 그 결과 19개 상위 requirement/acceptance element가 uncovered로 계산됐다.

## Covered Unit Paths

| Unit | Covered acceptance criteria | Representative targets |
|---|---|---|
| u1-ticket-read-skeleton | AC1.1.1~AC1.1.6, AC1.2.1~AC1.2.5 | `app/ticketing/`, read/gateway/presentation/lifecycle tests |
| u2-ticket-write | AC2.1.1~AC2.1.6 | create models/repository/operations/tool/integration tests |
| u3-ticket-update | AC3.1.1~AC3.1.6 | update models/repository/operations/tool/integration tests |
| u4-release-assurance | AC4.1.1~AC4.1.6, AC5.1.2, AC5.1.4 | release assurance, security, integration and lifecycle tests |

## Uncovered Elements

- Functional: `FR1.1`, `FR1.2`, `FR1.3`, `FR7.3`, `FR7.4`, `FR7.5`
- Non-functional groups: `NFR1`, `NFR2`, `NFR3`, `NFR4`, `NFR5`, `NFR6`, `NFR7`, `NFR8`, `NFR9`
- Acceptance criteria: `AC5.1.1`, `AC5.1.3`, `AC5.1.5`, `AC5.1.6`

## Findings

| ID | Owning Unit | Target evidence | Finding |
|---|---|---|---|
| AC5.1.1 | u4-release-assurance | `README.md`, `tests/test_release_assurance_documentation.py` | traceability target가 두 경로를 한 문자열로 기록해 존재 검사 실패 |
| AC5.1.3 | u4-release-assurance | `app/release_assurance/performance.py`, `tests/test_release_assurance_performance.py` | traceability target가 두 경로를 한 문자열로 기록해 존재 검사 실패 |
| AC5.1.5 | u4-release-assurance | README live-smoke section | 설명이 file path에 합쳐져 존재 검사 실패 |
| AC5.1.6 | u4-release-assurance | finalized performance evidence | `not_measured` 설명이 file path에 합쳐지고 실제 NFR8도 미측정 |

## Required Repair

U4 `traceability.json`의 각 coverage target을 sensor가 검사할 수 있는 단일 실제 path로 정규화하고, 여러 target은 별도 행으로 분리해야 한다. NFR8 actual evidence는 예정된 Performance Validation이 완료될 때까지 `Unverified`로 유지한다.

## Text Fallback

U1 read, U2 write, U3 update의 기능 경로와 U4 자동화 검증은 구현·테스트됐다. U4의 문서·성과 측정 관련 네 acceptance criterion은 target 표현 오류와 실제 NFR8 미측정 때문에 최종 교차 추적성 판정을 통과하지 못했다.
