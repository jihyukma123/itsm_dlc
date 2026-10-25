# Build and Test Questions

## Sources

- `construction/u1-ticket-read-skeleton/code-generation/code-generation-plan.md`
- `construction/u1-ticket-read-skeleton/code-generation/unit-test-instructions.md`
- `construction/u1-ticket-read-skeleton/code-generation/code-summary.md`
- `construction/u2-ticket-write/code-generation/code-generation-plan.md`
- `construction/u2-ticket-write/code-generation/unit-test-instructions.md`
- `construction/u2-ticket-write/code-generation/code-summary.md`
- `construction/u3-ticket-update/code-generation/code-generation-plan.md`
- `construction/u3-ticket-update/code-generation/unit-test-instructions.md`
- `construction/u3-ticket-update/code-generation/code-summary.md`
- `construction/u4-release-assurance/code-generation/code-generation-plan.md`
- `construction/u4-release-assurance/code-generation/unit-test-instructions.md`
- `construction/u4-release-assurance/code-generation/code-summary.md`
- `aidlc-state.md`

## Questions

### Q1. 실제 환경 NFR8 성과 측정을 어느 단계에서 실행할까요?

현재 자동화는 FakeModel, `httpx.MockTransport`, 네트워크 기본 차단을 사용하며 실제 OpenAI·ITSM 호출을 금지합니다. 실제 NFR8 측정에는 대상 환경, 테스트 사용자, credential, 생성 데이터와 정리 절차에 대한 명시적 선택이 필요합니다.

- A. 예정된 Performance Validation에서 실행한다 (Recommended)
- B. Build and Test에서 지금 실행한다 — 대상 환경과 credential 제공이 필요하다
- X. Other (please specify)

[Answer]: A. 예정된 Performance Validation에서 실행한다 (Recommended)

## Assumptions & Open Questions

- CI에서 테스트를 실행하는 의무는 이 계획에 포함된 후속 `ci-pipeline` 단계가 소유한다.
- Build and Test는 현재 저장소에서 U1~U4 exact test 명령, 전체 회귀, 80% coverage, 73개 automation catalog, 네트워크·비밀정보 경계를 재검증한다.

## Consolidated Summary Confirmation

- 실제 환경의 NFR8 성과 측정은 예정된 Performance Validation 단계에서 실행한다.
- Build and Test에서는 FakeModel, `httpx.MockTransport`, 네트워크 기본 차단을 유지하면서 저장소 내 자동화 검증을 실행한다.
- 후속 CI Pipeline 단계가 merge 전 테스트 실행 의무를 구현한다.

Does this all look correct before I generate the artifact?

- Looks correct
- Request changes

[Answer]: Looks correct
