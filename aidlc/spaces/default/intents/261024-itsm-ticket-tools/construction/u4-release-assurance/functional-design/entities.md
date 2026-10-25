# U4 출시 보증 엔터티 모델

## Sources

- `inception/units-generation/unit-of-work.md`
- `inception/units-generation/unit-of-work-story-map.md`
- `inception/user-stories/stories.md`
- `inception/requirements-analysis/requirements.md`
- `inception/domain-design/components.md`
- `inception/contract-design/contract-summary.md`

## Entity Model

```yaml
entities:
  - name: ReleaseAssuranceRun
    description: 하나의 소스 revision에 대해 U1~U3 조립 결과와 출시 조건을 판정하는 보증 실행
    identifier: assurance_run_id
    attributes:
      - {name: assurance_run_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: source_revision, logical_type: immutable_revision_identifier, required: true, unique: false}
      - {name: started_at, logical_type: utc_datetime, required: true, unique: false}
      - {name: completed_at, logical_type: utc_datetime, required: false, unique: false}
      - {name: status, logical_type: enum, required: true, unique: false, allowed_values: [draft, preflight_ready, automated_verified, documentation_verified, release_ready, blocked], default: draft}
      - {name: environment_profile, logical_type: non_secret_text, required: true, unique: false, constraints: "실행 환경과 의존성 version을 재현할 수 있어야 한다"}
      - {name: predecessor_assurance_run_id, logical_type: opaque_identifier, required: false, unique: false, references: ReleaseAssuranceRun.assurance_run_id}
      - {name: blocking_reason, logical_type: safe_text, required: false, unique: false, constraints: "비밀값과 원본 외부 오류를 포함하지 않는다"}
    entity_constraints:
      - release_ready는 모든 필수 VerificationEvidence가 통과하고 미해결 blocking DefectRoute가 없을 때만 가능하다
      - source_revision이 바뀌면 기존 release_ready 판정을 재사용하지 않고 새 실행을 만든다
      - blocked는 해당 source_revision 실행의 terminal 상태이며 수선된 revision은 predecessor_assurance_run_id로 이전 실행을 가리키는 새 ReleaseAssuranceRun을 만든다
      - 실패 또는 미실행 검사를 통과로 간주하지 않는다

  - name: RequiredVerificationCase
    description: 공유 계약과 출시 기준에서 파생된 유한한 필수 검사 catalog 항목
    identifier: check_id
    attributes:
      - {name: check_id, logical_type: stable_identifier, required: true, unique: true}
      - {name: contract_source, logical_type: enum, required: true, unique: false, allowed_values: [C-03, C-04, C-05, release]}
      - {name: procedure_key, logical_type: stable_identifier, required: true, unique: false}
      - {name: category, logical_type: enum, required: true, unique: false, allowed_values: [assembly, lifecycle, security, network, contract, regression, coverage, accessibility]}
      - {name: required_for_release, logical_type: boolean, required: true, unique: false, default: true}
    entity_constraints:
      - catalog는 functional-spec.md의 Required Verification Catalog와 정확히 일치한다
      - source revision 안에서 catalog 항목을 추가·삭제하거나 required_for_release를 완화하면 기존 evidence는 재사용할 수 없다
      - release_ready에는 required_for_release인 각 check_id별 passed evidence가 정확히 하나 있어야 한다

  - name: VerificationEvidence
    description: 하나의 필수 검증 항목이 무엇을 어떤 격리 조건에서 실행해 어떤 결과를 냈는지 기록하는 증거
    identifier: evidence_id
    attributes:
      - {name: evidence_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: assurance_run_id, logical_type: opaque_identifier, required: true, unique: false, references: ReleaseAssuranceRun.assurance_run_id}
      - {name: check_id, logical_type: stable_identifier, required: true, unique: false, references: RequiredVerificationCase.check_id}
      - {name: category, logical_type: enum, required: true, unique: false, allowed_values: [assembly, lifecycle, security, network, contract, regression, coverage, accessibility, documentation]}
      - {name: result, logical_type: enum, required: true, unique: false, allowed_values: [passed, failed, not_run]}
      - {name: command_or_procedure, logical_type: non_secret_text, required: true, unique: false}
      - {name: observed_counts, logical_type: key_value_measurements, required: false, unique: false, constraints: "요청 수, refresh 수, 외부 화면 전환 수처럼 판정에 필요한 값만 포함한다"}
      - {name: evidence_digest, logical_type: sha256, required: true, unique: false}
      - {name: recorded_at, logical_type: utc_datetime, required: true, unique: false}
    entity_constraints:
      - assurance_run_id와 check_id 조합은 한 실행에서 유일하다
      - passed는 명시된 절차가 완료되고 관찰값이 판정 기준을 충족한 경우에만 허용된다
      - 비밀 canary 원문, credential, Authorization 값과 원본 problem detail은 증거에 저장하지 않는다

  - name: RegressionExecutionEvidence
    description: 변경 전 기준선과 완료본 전체 suite 실행을 같은 shape로 비교하는 증거
    identifier: regression_evidence_id
    attributes:
      - {name: regression_evidence_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: assurance_run_id, logical_type: opaque_identifier, required: true, unique: false, references: ReleaseAssuranceRun.assurance_run_id}
      - {name: phase, logical_type: enum, required: true, unique: false, allowed_values: [baseline, final]}
      - {name: source_revision, logical_type: immutable_revision_identifier, required: true, unique: false}
      - {name: test_command, logical_type: non_secret_text, required: true, unique: false}
      - {name: total_count, logical_type: non_negative_integer, required: true, unique: false, min: 0}
      - {name: passed_count, logical_type: non_negative_integer, required: true, unique: false, min: 0}
      - {name: failed_count, logical_type: non_negative_integer, required: true, unique: false, min: 0}
      - {name: skipped_count, logical_type: non_negative_integer, required: true, unique: false, min: 0}
      - {name: exit_status, logical_type: integer, required: true, unique: false}
      - {name: output_digest, logical_type: sha256, required: true, unique: false}
      - {name: executed_at, logical_type: utc_datetime, required: true, unique: false}
    entity_constraints:
      - assurance_run_id와 phase 조합은 유일하다
      - total_count는 passed_count, failed_count, skipped_count와 그 밖의 명시적으로 보고된 결과 count의 합과 일치한다
      - final은 failed_count 0, skipped_count 0, exit_status 0이어야 통과한다
      - baseline과 final은 같은 test command와 실행 환경 profile을 사용해야 한다

  - name: CoverageAssessment
    description: 변경된 애플리케이션 소스 집합과 line coverage 판정을 고정하는 보증 기록
    identifier: coverage_assessment_id
    attributes:
      - {name: coverage_assessment_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: assurance_run_id, logical_type: opaque_identifier, required: true, unique: false, references: ReleaseAssuranceRun.assurance_run_id}
      - {name: source_manifest_digest, logical_type: sha256, required: true, unique: false}
      - {name: source_manifest_paths, logical_type: ordered_set_of_workspace_relative_paths, required: true, unique: false, constraints: "승인된 U1~U3 source manifest의 합집합과 U4가 변경한 애플리케이션 경로를 포함하고 중복·테스트·문서·생성 파일을 제외한다"}
      - {name: covered_lines, logical_type: non_negative_integer, required: true, unique: false, min: 0}
      - {name: executable_lines, logical_type: non_negative_integer, required: true, unique: false, min: 1}
      - {name: percentage, logical_type: decimal_percentage, required: true, unique: false, min: 0, max: 100}
      - {name: threshold, logical_type: decimal_percentage, required: true, unique: false, min: 80, max: 100, default: 80}
      - {name: result, logical_type: enum, required: true, unique: false, allowed_values: [passed, failed]}
    entity_constraints:
      - percentage는 covered_lines를 executable_lines로 나눈 값에서 결정한다
      - source_manifest_paths는 승인된 U1~U3 manifest 합집합과 U4 애플리케이션 변경 경로에서 결정하며 coverage 실행 전에 고정한다
      - manifest에 포함되어야 할 파일을 사후 제외해 threshold를 맞추지 않는다

  - name: DefectRoute
    description: U4에서 발견한 결함을 계약 또는 구현 소유 Unit에 되돌리는 차단 기록
    identifier: defect_route_id
    attributes:
      - {name: defect_route_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: assurance_run_id, logical_type: opaque_identifier, required: true, unique: false, references: ReleaseAssuranceRun.assurance_run_id}
      - {name: failed_check_id, logical_type: stable_identifier, required: true, unique: false}
      - {name: owning_unit, logical_type: enum, required: true, unique: false, allowed_values: [u1-ticket-read-skeleton, u2-ticket-write, u3-ticket-update, u4-release-assurance]}
      - {name: contract_reference, logical_type: stable_reference, required: true, unique: false}
      - {name: severity, logical_type: enum, required: true, unique: false, allowed_values: [blocking, non_blocking]}
      - {name: status, logical_type: enum, required: true, unique: false, allowed_values: [open, repaired, reverified]}
      - {name: repair_evidence_id, logical_type: opaque_identifier, required: false, unique: false, references: VerificationEvidence.evidence_id}
    entity_constraints:
      - blocking 결함이 open 또는 repaired 상태이면 ReleaseAssuranceRun은 release_ready가 될 수 없다
      - repaired는 완료가 아니며 같은 실패 검사를 새 소스 revision에서 통과해 reverified가 되어야 한다

  - name: DocumentationAssurance
    description: README와 분리된 실제 연동 smoke 절차가 필수 내용을 포함하는지 판정하는 기록
    identifier: documentation_assurance_id
    attributes:
      - {name: documentation_assurance_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: assurance_run_id, logical_type: opaque_identifier, required: true, unique: false, references: ReleaseAssuranceRun.assurance_run_id}
      - {name: readme_topics, logical_type: set_of_enum, required: true, unique: false, allowed_values: [feature, configuration, run, security_boundary, tests, coverage, smoke_separation]}
      - {name: smoke_prerequisites_documented, logical_type: boolean, required: true, unique: false}
      - {name: explicit_credentials_required, logical_type: boolean, required: true, unique: false}
      - {name: default_automation_uses_real_services, logical_type: boolean, required: true, unique: false, default: false}
      - {name: result, logical_type: enum, required: true, unique: false, allowed_values: [passed, failed]}
    entity_constraints:
      - readme_topics는 허용된 일곱 항목을 모두 포함해야 passed가 가능하다
      - smoke 절차는 기본 자동화와 구분되고 명시적 credential과 대상 환경 없이는 실행되지 않아야 한다

  - name: PerformanceMeasurementSession
    description: NFR8의 동일 조건 비교를 묶는 실제 환경 측정 세션
    identifier: measurement_session_id
    attributes:
      - {name: measurement_session_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: source_revision, logical_type: immutable_revision_identifier, required: true, unique: false}
      - {name: environment, logical_type: non_secret_text, required: true, unique: false}
      - {name: anonymized_role, logical_type: non_secret_text, required: true, unique: false}
      - {name: device_browser_network_profile, logical_type: non_secret_text, required: true, unique: false}
      - {name: status, logical_type: enum, required: true, unique: false, allowed_values: [planned, measuring, complete, invalid]}
      - {name: invalid_reason, logical_type: safe_text, required: false, unique: false}
    entity_constraints:
      - 같은 세션의 Assistant와 기존 ITSM 방식은 동일 계정 역할, 장치, 브라우저, 배포 version과 network 조건을 사용한다
      - 방식별 warm-up 1회는 trial과 중앙값에서 제외한다

  - name: PerformanceTrial
    description: 한 방식과 시나리오의 단일 monotonic-clock 측정 결과
    identifier: trial_id
    attributes:
      - {name: trial_id, logical_type: opaque_identifier, required: true, unique: true}
      - {name: measurement_session_id, logical_type: opaque_identifier, required: true, unique: false, references: PerformanceMeasurementSession.measurement_session_id}
      - {name: method, logical_type: enum, required: true, unique: false, allowed_values: [assistant, existing_itsm_ui]}
      - {name: scenario, logical_type: enum, required: true, unique: false, allowed_values: [read, create, update]}
      - {name: trial_number, logical_type: integer, required: true, unique: false, min: 1, max: 3}
      - {name: generated_data_reference, logical_type: opaque_non_secret_reference, required: true, unique: false}
      - {name: measured_at, logical_type: utc_datetime, required: true, unique: false}
      - {name: monotonic_start, logical_type: monotonic_timepoint, required: true, unique: false}
      - {name: monotonic_end, logical_type: monotonic_timepoint, required: true, unique: false}
      - {name: duration_seconds, logical_type: non_negative_decimal, required: true, unique: false, min: 0}
      - {name: success, logical_type: boolean, required: true, unique: false}
      - {name: failure_reason, logical_type: safe_text, required: false, unique: false}
      - {name: external_screen_transitions, logical_type: non_negative_integer, required: true, unique: false, min: 0}
    entity_constraints:
      - measurement_session_id, method, scenario, trial_number 조합은 유일하다
      - duration_seconds는 monotonic_end와 monotonic_start의 차이다
      - 각 method와 scenario 조합은 사전 지정된 trial_number 1, 2, 3을 정확히 한 번씩만 가지며 실패 trial을 추가 trial로 교체하지 않는다
      - 세 trial 중 하나라도 실패하거나 완료 사건에 도달하지 못하면 해당 시나리오의 성과 목표는 미충족이며 성공 표본만의 중앙값을 계산하지 않는다

relationships:
  - {from: ReleaseAssuranceRun, to: VerificationEvidence, cardinality: one_to_many, direction: owns}
  - {from: RequiredVerificationCase, to: VerificationEvidence, cardinality: one_to_many, direction: classifies}
  - {from: ReleaseAssuranceRun, to: RegressionExecutionEvidence, cardinality: one_to_many, direction: owns}
  - {from: ReleaseAssuranceRun, to: CoverageAssessment, cardinality: one_to_one, direction: owns}
  - {from: ReleaseAssuranceRun, to: DefectRoute, cardinality: one_to_many, direction: owns}
  - {from: ReleaseAssuranceRun, to: DocumentationAssurance, cardinality: one_to_one, direction: owns}
  - {from: PerformanceMeasurementSession, to: PerformanceTrial, cardinality: one_to_many, direction: owns}
```

## Entity Summary

`ReleaseAssuranceRun`은 특정 소스 revision의 출시 판정을 소유하며 `blocked`로 끝난 실행을 수선된 revision에 재사용하지 않는다. `RequiredVerificationCase`가 유한한 release-blocking catalog를 정의하고, 각 항목의 결과는 `VerificationEvidence`에 1:1로 남는다. 변경 전·후 전체 suite는 `RegressionExecutionEvidence`, coverage 계산은 `CoverageAssessment`, 실패의 소유권과 재검증 상태는 `DefectRoute`, 문서 완결성은 `DocumentationAssurance`로 분리한다. NFR8은 자동화 테스트의 가짜 성과값으로 닫지 않고, 실제 환경에서 실행할 `PerformanceMeasurementSession`과 `PerformanceTrial`의 재현 가능한 기록 계약으로 유지한다.

ITSM의 티켓, 세션 credential, 등록 원장과 수정 실행 record는 U1~U3의 소유 엔터티이며 U4가 복제하거나 재정의하지 않는다.

