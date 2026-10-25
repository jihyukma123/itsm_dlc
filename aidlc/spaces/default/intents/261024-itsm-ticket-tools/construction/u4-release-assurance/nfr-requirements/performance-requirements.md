# U4 Performance Requirements

## Sources

- `inception/requirements-analysis/requirements.md`의 `NFR4`, `NFR7`, `NFR8`
- `construction/u4-release-assurance/functional-design/functional-spec.md`
- `inception/contract-design/contract-summary.md`의 transport policy

## Requirements

| ID | Requirement | Target | Measurement | Blocking evidence |
|---|---|---|---|---|
| NFR4.1 | 티켓 목록 한 page의 응답 범위를 제한한다. | 기본 20건, 최소 1건, 최대 100건 | 경계값 1·20·100·101과 continuation 회귀 | MockTransport 요청·응답 count와 page projection |
| NFR4.2 | 긴 결과는 조용히 잘라내지 않고 continuation으로 제공한다. | `has_more=true`이면 server-bound continuation reference 제공률 100%; raw upstream cursor 노출 0건 | 다중 page와 변경 filter/sort 재사용 거부 | cursor issue/resolve 및 tamper test |
| NFR7.1 | read/list의 전체 호출 시간과 시도 수를 제한한다. | HTTP 시도 최대 2회, 첫 retry 전 250ms, 최대 경과 `2 × ITSM_TIMEOUT_SECONDS + 0.25초` | fake clock과 request counter | timeout/transport/500·502·503·504 matrix |
| NFR7.2 | create의 mutation 시도 예산을 단일 ledger count로 제한한다. | same key·same bytes POST 최대 2회; 새 key 재시도 0회 | request bytes digest, key identity, attempt count | ambiguous·401·reconcile 경로 통합 counter |
| NFR7.3 | update는 안전하지 않은 자동 재전송을 하지 않는다. | 일반 PATCH 자동 retry 0회; 권위 있는 no-apply 401 복구 뒤 동일 PATCH 최종 1회만 허용 | PATCH counter와 `If-Match` byte identity | conflict·timeout·response-loss matrix |
| NFR7.4 | rate limit은 서버가 기다리지 않는다. | 429 sleep 0회, automatic retry 0회, 검증된 `Retry-After` 즉시 반환 | fake clock 변화량과 request counter | read/create/update 429 test |
| NFR8.1 | 대표 read/create/update는 Assistant 안에서 외부 ITSM 화면 전환 없이 완료한다. | Assistant trial의 external screen transition 0회 | 실제 환경 trial record | 각 방식·시나리오별 사전 지정 trial 1·2·3 |
| NFR8.2 | Assistant 방식의 중앙 완료 시간은 기존 ITSM UI보다 짧아야 한다. | 세 시나리오 각각 `median(assistant) < median(existing UI)` | monotonic clock | 동일 조건의 성공 trial 3+3개 |
| NFR8.3 | 측정 표본을 성공 결과로 대체 선택하지 않는다. | 방식·시나리오별 trial 번호 1·2·3을 정확히 한 번; 추가 대체 trial 0회 | measurement ledger uniqueness | 정상 조건의 실패 trial은 목표 미충족으로 보존 |
| NFR8.4 | 측정 조건 위반과 업무 실패를 구분한다. | 환경 조건 위반=`invalid`, 정상 조건 실패=`not_met`, 미실행=`not_measured` | record completeness와 environment fingerprint | 상태별 사유와 UTC 측정 시각 |

## Measurement Protocol

- 방식별 warm-up 1회는 측정과 중앙값에서 제외한다.
- 동일 account role, 권한, browser, device, source revision, deployment와 network를 사용한다.
- 각 trial 전에 생성형 일회용 data로 같은 초기 상태를 복원한다.
- trial 실패는 같은 번호의 새 실행으로 교체하지 않는다. 성공한 세 trial이 모두 있을 때만 중앙값을 계산한다.
- 실제 환경 결과가 없으면 `NFR8.1`~`NFR8.4`를 달성했다고 주장하지 않는다.

## Constraints

- 새 throughput, 동시 사용자 또는 availability 목표를 임의로 만들지 않는다.
- 자동화 test duration은 사용자 성과 duration의 대체 지표가 아니다.
- 실제 smoke와 성과 측정은 기본 FakeModel/MockTransport suite와 분리한다.

## Assumptions & Open Questions

None.

