# U4 Scalability Requirements

## Sources

- `inception/requirements-analysis/requirements.md`의 `NFR4`
- `aidlc/spaces/default/codekb/itsm_dlc/technology-stack.md`
- `inception/contract-design/contract-summary.md`

## Requirements

| ID | Requirement | Target | Evidence |
|---|---|---|---|
| NFR4.3 | 목록 크기는 bounded page로 유지한다. | 기본 20, 최대 100 | limit 경계와 page-size assertion |
| NFR4.4 | page 진행 상태는 server-bound continuation으로 유지한다. | raw cursor model 노출 0건; filter/sort/actor mismatch 수락 0건 | issue/resolve round-trip, tamper, lifecycle cleanup tests |
| NFR4.5 | U4는 기존 단일-process 배포에 새 scaling topology를 추가하지 않는다. | 새 service, queue, cache, worker, CI/CD 또는 cloud resource 0개 | source/config manifest review |
| NFR4.6 | local assurance evidence는 업무 payload와 credential을 복제하지 않는다. | ticket body·canonical mutation bytes·credential·Authorization persistence 0건 | evidence schema inspection과 secret scan |

## Capacity Position

- 새로운 throughput 또는 concurrent-user SLO는 승인된 요구사항에 없다.
- 기능 목록 응답의 최대 100건과 기존 timeout이 현재 capacity guard다.
- 단일-process conversation serialization은 기존 runtime 가정이다. 다중-process coordination은 이번 Unit에서 주장하거나 구현하지 않으며 향후 topology 변경 시 재설계가 필요하다.
- U4의 검증 catalog는 test case 수에 비례하되 production request path에 상시 부하를 추가하지 않는다.

## Growth and Trigger Conditions

다음 사건은 새 요구사항과 설계 검토를 촉발하지만 이번 출시의 자동 scaling action은 아니다.

- 단일 process에서 여러 process/instance로 배포 topology 변경
- page 최대 100건 또는 cursor 계약 변경
- server-session SQLite와 agent-history SQLite의 분리·공유 storage 변경
- 새로운 ticket tool 또는 별도 Agent 추가

## Assumptions & Open Questions

None.

