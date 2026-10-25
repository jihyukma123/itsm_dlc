# U4 Security Requirements

## Sources

- `inception/requirements-analysis/requirements.md`의 `NFR1`, `NFR2`, `NFR3`
- `inception/contract-design/contract-summary.md`의 C-01~C-07
- `construction/u4-release-assurance/functional-design/rules.md`의 BR4.2~BR4.7

## Requirements

| ID | Requirement | Target | Verification | Failure behaviour |
|---|---|---|---|---|
| NFR1.1 | credential과 비밀값은 model·tool·log·HTTP 오류·test failure 경계를 넘지 않는다. | access token, refresh credential, client secret, OpenAI API key, Authorization canary 노출 0건 | schema, model input, tool result, application log, HTTP error, pytest assertion message, traceback, captured stdout/stderr와 test runner report의 경계별 고유 canary scan | 즉시 차단하고 실패 진단에는 canary 값 대신 경계 식별자만 기록 |
| NFR1.2 | 외부 ITSM 텍스트는 구조화된 비신뢰 data로만 취급한다. | 신원·권한·확인·도구 선택·인자 변화 0건 | 지시문·HTML·Markdown 제어 문자 injection matrix | safe text fallback 또는 allowlisted projection |
| NFR1.3 | 오류는 허용 목록 정보만 노출한다. | raw problem detail, exception, request/response header 노출 0건 | 모든 오류 code와 악의적 body 주입 | 안정 code·message key·비밀 아닌 request ID만 반환 |
| NFR1.4 | 기본 자동화는 예상하지 않은 외부 network를 거부한다. | 실제 OpenAI·ITSM·DNS·TCP 호출 0건 | process default-deny fixture와 deliberate bypass probe | test 즉시 실패 |
| NFR2.1 | ticket API 호출은 현재 서버 session 사용자의 delegated credential만 사용한다. | delegated token 사용률 100%, service token ticket 호출 0건 | actor-bound capability와 outbound auth-kind counter | mutation 금지 및 authentication/permission 안전 오류 |
| NFR2.2 | 사용자 identity는 client/model 입력으로 변경되지 않는다. | username·role·permission override 성공 0건 | cross-user tool argument와 injected text test | server session identity를 유일한 권위로 사용 |
| NFR2.3 | 보이지 않는 ticket의 존재를 추론하지 않는다. | missing과 invisible 404 구분 노출 0건 | 동일 safe not_found response 비교 | 동일한 복구 안내 반환 |
| NFR3.1 | create는 확인 evidence와 CAS claim 없이는 실행되지 않는다. | 무권한 POST 0건, confirmed intent당 생성 ticket 최대 1개 | consume evidence, ledger claim, request counter | fail-closed; 새 key 발급 금지 |
| NFR3.2 | create retry는 동일 key와 byte-identical body를 유지한다. | key/bytes 변화 0건, 총 POST 최대 2회 | digest와 global attempt counter | terminal ambiguous 또는 safe failure |
| NFR3.3 | update는 검증된 strong ETag의 version을 정확히 `If-Match`로 사용한다. | 잘못된·누락·weak ETag PATCH 0건, conflict overwrite 0건 | ETag/version matrix | 최신 detail과 새 확인으로 복귀 |
| NFR3.4 | lifecycle과 concurrency는 cross-user·stale authority를 공개하지 않는다. | 권한 있는 winner 최대 1개, stale/cross-user mutation 0건 | deterministic barrier와 restart recovery | current run blocked 및 소유 Unit defect route |

## Threat Considerations

| Threat | Required control | Evidence |
|---|---|---|
| Prompt injection through ticket text | untrusted structured data boundary, server-owned identity and confirmation | injected ticket/problem payload tests |
| Credential exfiltration | opaque capability, server-only storage, redaction and canaries | schema/model/result/log/error와 assertion/traceback/stdout/stderr/test-report scan |
| Confused deputy | current-session actor binding and delegated token only | cross-user/cross-session negative tests |
| Duplicate create | ledger-first exact bytes/key, consume evidence, CAS claim | crash/reconcile/idempotent replay tests |
| Lost update | validated ETag/`If-Match`, no automatic overwrite | 412/428/ambiguous matrix |
| Hidden network use | default-deny plus bypass self-test | external attempt count 0 |

## Compliance Boundary

추가 규제 체계나 데이터 분류를 새로 가정하지 않는다. 기존 session과 ITSM 권한 경계를 보존하고, 보증 evidence에는 credential이나 원본 업무 payload 대신 digest·count·safe identifier만 남긴다.

## Assumptions & Open Questions

None.

