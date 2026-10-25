# Performance Test Instructions

## Sources

- `construction/u4-release-assurance/nfr-requirements/performance-requirements.md`
- `construction/u4-release-assurance/nfr-design/performance-design.md`
- `construction/u4-release-assurance/code-generation/code-summary.md`
- `construction/build-and-test/build-and-test-questions.md`

## Automated Policy Checks in Build and Test

Fake clock과 request counter로 다음 결정적 budget을 검증한다.

- read/list HTTP 시도 최대 2회, retry 시 delay 정확히 0.25초
- 최대 read 경과시간 `2 × ITSM_TIMEOUT_SECONDS + 0.25초`
- create POST는 모든 복구 원인을 합쳐 최대 2회이며 동일 key·bytes 유지
- update PATCH는 기본 1회, 권위 있는 no-apply 401 뒤에만 동일 PATCH 최종 1회 추가
- 429 sleep 0회, automatic retry 0회
- page limit 기본 20, 최소 1, 최대 100, raw cursor 노출 0건

이 검증은 각 Unit exact suite와 전체 회귀에 포함된다.

## Real-Environment NFR8 Validation

사용자가 선택한 대로 실제 NFR8 성과 측정은 예정된 Performance Validation에서 수행한다. Build and Test에서는 실행하지 않으며 `Unverified`로 남긴다.

필수 준비물:

- 명시적 대상 환경과 source revision/deployment
- 익명화한 동일 account role과 권한
- 테스트 사용자 credential의 안전한 제공 방식
- browser/device/OS/viewport/network/cache fingerprint
- 각 trial에 사용할 생성형 일회용 data와 cleanup 절차
- read/create/update별 Assistant와 기존 UI warm-up 1회
- 방식·시나리오별 고정 trial 1·2·3

## Measurement and Pass Criteria

- Assistant 방식의 외부 ITSM 화면 전환 0회
- read/create/update 각각 `median(assistant) < median(existing UI)`
- 실패 trial을 교체하지 않고 그대로 `not_met`로 보존
- 미실행은 `not_measured`, 조건 위반은 `invalid`
- UTC 시각과 monotonic start/end, duration, result, transition count를 모두 기록

실제 환경 결과가 없으면 NFR8을 `Met`으로 표시하지 않는다.
