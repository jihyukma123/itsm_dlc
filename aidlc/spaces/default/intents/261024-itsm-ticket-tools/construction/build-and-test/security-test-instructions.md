# Security Test Instructions

## Sources

- U1~U4 `nfr-requirements/security-requirements.md`
- U1~U4 `nfr-design/security-design.md`
- 각 Unit의 `unit-test-instructions.md`

## Security Boundaries

- credential, refresh credential, client secret, OpenAI API key, Authorization, idempotency key, canonical mutation bytes와 raw `If-Match`를 공개 경계 밖으로 내보내지 않는다.
- ITSM text와 problem payload는 항상 비신뢰 data로 취급한다.
- identity·permission·confirmation은 서버 session과 durable binding만 권위로 사용한다.
- create는 consume evidence와 claim 없이 POST하지 않고, update는 검증된 strong ETag 없이는 PATCH하지 않는다.
- lifecycle cleanup 뒤 stale/cross-user authority와 old-scope history/presentation을 재생성하지 않는다.

## Commands

U1~U4 exact suite 중 security, lifecycle, gateway, operation, network-isolation test를 포함한 명령을 실행한 뒤 전체 회귀를 실행한다.

```bash
.venv/bin/python -m pytest -q
```

## Required Evidence

- secret canary exposure 0
- unexpected OpenAI·ITSM·DNS·TCP attempt 0
- deliberate bypass probe 차단 1건 이상
- delegated credential 사용률 100%, service-token ticket call 0
- invisible/missing ticket 구분 노출 0
- unauthorized POST/PATCH, duplicate create, conflict overwrite, second refresh 각각 0
- malicious external text의 identity·permission·tool·confirmation 영향 0
- 오류 결과가 allowlisted safe schema를 통과하고 raw provider detail 노출 0

## Failure Handling

비밀 값 자체를 실패 산출물에 복사하지 않는다. 경계 ID, 안전한 count와 digest만 기록하고, 발견 즉시 해당 test와 전체 release 판정을 실패시킨다.
