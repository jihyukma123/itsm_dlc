## Review

**Verdict:** NOT-READY
**Reviewer:** aidlc-architecture-reviewer-agent
**Date:** 2026-10-25T17:38:15Z
**Iteration:** 1
**Verdict Dictated:** no

### Findings

| ID | Severity | Location | Finding | Required action | Status |
|---|---|---|---|---|---|
| R-01 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u4-release-assurance/functional-design/functional-spec.md > Workflow 2, Workflow 3, Workflow 4; entities.md > VerificationEvidence | C-03의 `verification_owned_by_u4.required_contract_tests`와 C-04·C-05의 `verification_manifest.required_cases`가 유한한 필수 검사 목록을 정의하지만, U4 설계는 이를 넓은 서술형 단계로만 축약한다. `VerificationEvidence.check_id`에도 허용된 필수 검사 catalog가 없어서 BR4.13의 “모든 필수 evidence”가 무엇인지 계산할 수 없다. 특히 cursor exact-query·tamper, pending variant round-trip, update replacement rollback, presentation correlation, create/update의 상세 refresh·crash·tamper 사례가 누락되어도 현재 상태 모델은 `release_ready`를 허용할 수 있다. AC5.1.3의 변경 전 기준선과 완료본 비교도 generic `observed_counts`에만 기대므로 전체 suite와 source-manifest coverage 증거의 필수 shape가 정해지지 않았다. | C-03, C-04, C-05의 모든 필수 case를 안정적인 `check_id` catalog로 열거하고 각 case를 workflow와 evidence에 1:1로 매핑하라. 기준선·완료본 test command와 pass/fail/skip count, 변경 source manifest의 구성 규칙, coverage 계산 evidence도 필수 항목으로 정의하고 catalog가 완전하지 않으면 `release_ready`를 금지하라. | New |
| R-02 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u4-release-assurance/functional-design/entities.md > ReleaseAssuranceRun constraints; functional-spec.md > Release Assurance State Machine | `ReleaseAssuranceRun.source_revision`은 immutable이고 revision이 바뀌면 새 run을 만든다고 정의했지만, state machine은 `blocked --> draft` 전이를 “새 source revision”으로 같은 run 안에서 수행한다. 수선 뒤 evidence와 defect를 어느 run/revision에 귀속할지 두 권위 정의가 충돌하며, 잘못 구현하면 이전 revision의 evidence가 새 판정에 섞인다. | `blocked`를 해당 run의 terminal 상태로 만들고 수선된 revision에는 새 `ReleaseAssuranceRun`을 생성해 이전 run/defect를 참조하도록 하거나, 같은 run을 재사용하려면 `source_revision` 불변 조건을 제거하고 모든 evidence를 revision별로 강제 분리하라. 한 방식만 source of truth로 남겨라. | New |
| R-03 | Major | aidlc/spaces/default/intents/261024-itsm-ticket-tools/construction/u4-release-assurance/functional-design/entities.md > PerformanceTrial constraints; rules.md > BR4.12; functional-spec.md > Workflow 6 | NFR8은 방식·시나리오별로 정해진 세 trial을 수행하고 각 trial의 성공 여부와 실패 사유를 기록하도록 요구한다. 현재 설계는 “정확히 성공한 세 trial”이 있어야 중앙값을 계산한다고 규정해 실패 trial을 추가 실행으로 대체할 수 있게 하며, 성공한 표본만 선택해 성과를 과대평가할 수 있다. Workflow 6도 실패 trial이 목표 실패인지, session invalid인지, 대체 가능한지 결정하지 않는다. | 각 방식·시나리오에 사전 지정된 정확히 세 측정 trial만 허용하고 실패 trial을 교체하지 못하게 하라. 실패 또는 완료 사건 미도달 시 해당 시나리오의 성과 목표를 미충족으로 판정하는 규칙과, 환경 조건 위반으로 session을 invalid 처리하는 경우를 구분해 중앙값 계산·기록 방식을 명시하라. | New |

### Validation Tool Results

| Tool | Result | Interpretation |
|---|---|---|
| `aidlc engine sensor-traceability` | PASS: gaps 0, orphans 0, invalid targets 0 | AC4.1.1~AC4.1.6과 AC5.1.1~AC5.1.6의 선언 및 BR target 참조는 구조적으로 유효하다. |
| `aidlc engine sensor-required-sections` | PASS: H2 13개 | Functional spec의 문서 shape와 필수 section 구조는 유효하다. |
| YAML safe-load | PASS: `entities.md`, `rules.md` | 두 source-of-truth YAML block은 구문상 유효하다. |
| `jq empty` | PASS: `traceability.json` | JSON은 구문상 유효하다. |
| Mermaid CLI | NOT RUN: workspace에 `mmdc` 실행 파일이 없음 | 두 diagram은 수동으로 문법을 점검했으며, 도구 부재만으로 verdict를 낮추지 않았다. |
| linter / type-check | N/A: TypeScript·JavaScript snippet 없음 | 이 설계 산출물에는 해당 code-shape 검사가 적용되지 않는다. |

### Summary

AC-to-rule 추적과 문서 구조는 건전하지만, release-ready 판정을 닫는 필수 검사 catalog가 계약보다 느슨하고 revision 귀속과 NFR8 표본 규칙에 상충이 있다. 이 세 부분을 고정해야 구현자가 누락 없는 보증과 편향 없는 성과 판정을 만들 수 있다.
