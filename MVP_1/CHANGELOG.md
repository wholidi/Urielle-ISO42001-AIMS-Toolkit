# Changelog

## MVP1-Agentic-Phase3.1-RC1

Date: 2026-09-03

Status: **Release candidate — remote CI validation pending**

### Added
- Reproducible Python project metadata in `MVP_1/pyproject.toml`.
- Explicit Python 3.11+ compatibility and bounded runtime dependencies.
- Optional `dev` dependency group containing pytest.
- Installed-package data declarations for schemas, governance configuration,
  question-bank data, and demo responses.
- Clean-clone setup and validation guide in `MVP_1/README.md`.
- GitHub Actions test and acceptance-demo matrix for Python 3.11–3.13.
- Explicit `scripts` package for `python -m` execution after installation.

### Fixed
- Removed duplicate execution-event writes and duplicate confirmation output
  from `scripts/run_agentic_clause04_demo.py`.
- Corrected indentation in acceptance-summary construction without changing its
  contract or contents.

### Local validation
- Python source compilation passed.
- Project metadata parsed successfully.
- Git diff whitespace validation passed.

### Pending acceptance
- Push the release candidate and require the GitHub Actions matrix to pass.
- Do not mark Phase 3.1 complete until all supported Python jobs and the real
  governed acceptance demonstration are green.

---

## MVP1-Agentic-Phase3

Date: 2026-08-26

Status: **Complete — governed end-to-end Agentic Clause 04 MVP**

### Added
- Schema-bound runtime validation for governed agentic contracts.
- Deterministic `SequentialSupervisor` orchestration under `PolicyEnforcer`.
- Execution-event contract binding across supervisor lifecycle events.
- `Clause04Adapter` to invoke and normalize the frozen deterministic Clause 04 assessment engine without duplicating scoring logic.
- `EvidenceAssessor` and governed `EvidenceDecision` generation.
- Deterministic `FindingGenerator`.
- Explicit `HumanReviewService` integration for externally supplied ACCEPTED / MODIFIED / REJECTED human dispositions.
- `ReportGenerator` supporting auditable DRAFT / FINAL report lifecycle behavior.
- `Clause04Workflow` integrating all declared workflow stages.
- End-to-end Agentic Clause 04 test suite.
- Real-input acceptance runner: `scripts/run_agentic_clause04_demo.py`.
- Persistent acceptance evidence under `reports/evidence/agentic_clause04/`:
  - `CLAUSE04-DEMO-001_FINAL.md`
  - `CLAUSE04-DEMO-001_execution_events.json`
  - `CLAUSE04-DEMO-001_acceptance_summary.json`

### Changed
- Refactored the Clause 04 runner so deterministic assessment calculation can be called through the adapter while file I/O and console/report concerns remain outside the calculation boundary.
- Preserved the frozen deterministic Clause 04 readiness score as the authoritative score throughout the governed workflow.
- Added explicit traceability from assessment identity to evidence decisions, findings, execution events, and final report output.

### Validation
- Focused Agentic Clause 04 end-to-end tests: **9 passed**.
- Full regression suite: **232 passed**.
- Acceptance run command: `python -m scripts.run_agentic_clause04_demo`.
- Acceptance workflow state: **COMPLETED**.
- Declared workflow stages completed: **7/7**.
- Execution events recorded: **16**.
- Report status: **FINAL**.
- Deterministic Clause 04 readiness score preserved: **100.0%**.
- Governed evidence decisions generated: **4**.
- Findings: **0**.
- Pending findings: **0**.

### Governance Properties
- Deterministic control remains authoritative for Clause 04 readiness scoring.
- The agentic workflow does not recalculate the readiness score.
- Invalid workflow and review inputs fail closed.
- Human review is explicit; the workflow does not invent or auto-approve human dispositions.
- No LLM or external model is used in the governed acceptance path.
- Execution events remain schema-valid and auditable.
- Report generation does not make a certification decision or provide independent audit assurance.

### Accepted Phase 3 Limitations
- Scope remains ISO/IEC 42001 Clause 04 only.
- Evidence references may originate from human responses and are not independently verified by the agentic reporting layer.
- Referenced evidence files and their contents are not independently validated by this workflow.
- Reviewer identity/authentication remains external to `HumanReviewService`.
- The Phase 3 MVP proves governed orchestration and traceability; it does not replace an accredited certification audit.

---

## MVP1-Governance-Phase2-v0.2.0

Date: 2026-08-03

Status: Deterministic governance enforcement layer merged to main

### Added
- Component registry: `governance/agent_registry.yaml`.
- Permission matrix with default-deny and deny-precedence: `governance/permission_matrix.yaml`.
- Human approval rules requiring non-automated, non-self approval: `governance/human_approval_rules.yaml`.
- Model-use record confirming `NOT_IN_USE` status: `governance/model_use_record.yaml`.
- Fail-closed policy enforcer: `governance/policy_enforcer.py`.
- Fail-closed startup validator: `governance/startup_validator.py`.
- Governance configuration loader: `governance/config_loader.py`.
- JSON Schemas for all four governance configuration documents.
- Valid and invalid governance configuration fixtures.
- Phase 2 acceptance test suite: `tests/test_governance_phase2_acceptance.py`.

### Validation
- Full pytest suite: 132 passed.
- Phase 2 implementation commit: `5f096955` (`5f0969555b0beb590419caceb3a51f32e4be5eb8`).
- Main merge commit: `91a3763`.
- Frozen Clause 04 tree unchanged: `d8531b048382779c9c1a2d93620756d449630c9f`.
- Protected paths unchanged: `04_Context/`, `05_Leadership/`, `Evidence_Repository/`, `MVP_1/clause_04_context/`.

### Documentation
- Added `docs/architecture/ADR-0002-deterministic-governance-layer.md`.
- Added implementation status addendum to `docs/architecture/ADR-0001-sequential-supervisor.md`.
- Added `docs/implementation/phase_2_progress.md`.

### Accepted Phase 2 Limitations
- No supervisor, specialist agent, or orchestration layer exists yet.
- No report or finding generator exists yet.
- No LLM or external model integration exists yet; `model_use_status` remains `NOT_IN_USE`.
- `governance.audit_logger.AuditLogger` and `governance.schema_validator.SchemaValidator` are registered as enabled components but have no corresponding implementation module. No test currently exercises either.
- File-system-level enforcement of the ADR-0001 read-only and write boundaries is not yet implemented in the governance layer; those boundaries remain enforced by convention and manual review.

---

## MVP1-Agentic-Phase1-v0.1.0

Date: Not recorded in source documents; predates the Phase 2 merge (commit `91a3763`). See `docs/implementation/phase_1_progress.md` for checkpoint-level detail.

Status: Assessment data contracts merged; contract-only, no runtime behavior added

### Added
- `agentic_assessment` package skeleton: `agentic_assessment/__init__.py` (package version 0.1.0).
- Controlled vocabulary definition: `docs/implementation/phase_1_controlled_vocabulary.md` (schema version 1.0.0).
- Four JSON Schema contracts, JSON Schema draft 2020-12, schema version 1.0.0:
  - `agentic_assessment/schemas/assessment_plan.schema.json`
  - `agentic_assessment/schemas/evidence_decision.schema.json`
  - `agentic_assessment/schemas/finding.schema.json`
  - `agentic_assessment/schemas/execution_event.schema.json`
- Valid and invalid fixtures for all four contracts.
- Contract validation test suite: `tests/test_agentic_assessment_schemas.py`.

### Validation
- New contract tests: 12 passed.
- Complete regression suite at Phase 1 completion: 85 passed.
- Clause 04 rule-based readiness unchanged: 100.0%.
- Frozen Clause 04 tree unchanged: `d8531b048382779c9c1a2d93620756d449630c9f`.
- Protected paths unchanged.

### Accepted Phase 1 Limitations
- Contract-only; no supervisor, specialist component, report generator, or LLM integration was introduced.
- No governance enforcement of these contracts existed until Phase 2.

---

## MVP1-Clause04-Pilot-v1.0

Date: 2026-07-12

Status: Frozen / Released Clause 04 rule-based pilot baseline

### Released
- Frozen Clause 04 pilot as v1.0.
- Release artifact: `MVP1-Clause04-Pilot-v1.0.zip`.

### Validation
- Runner command passed: `python -m clause_04_context.run_clause04_demo`.
- Rule-based readiness score: 100.0%.
- Final runner result: No structural, response-quality, or evidence-reference gaps detected in the loaded Clause 04 pilot scope.
- End-to-end tests: 9 passed.
- Gap detector tests: 11 passed.
- Full pytest suite: 73 passed.

### Included
- Clause 04 coverage from 4.1 to 4.4.
- Rule-based response quality scoring.
- Structural coverage gap detection.
- Missing structured evidence reference gap detection.
- Markdown report generation.
- JSON evidence record generation.
- Evidence traceability fields.
- Defensive input validation.
- End-to-end regression tests.
- Per-section report alignment test confirming each evidence reference appears under the correct Clause 04 question section.

### Accepted Pilot Limitations
- Evidence references are extracted but not independently verified.
- Referenced evidence files are not checked for existence.
- Referenced evidence file contents are not validated.
- Validator remains rule-based and heuristic.
- Owner and date fields are checked syntactically, not semantically.
- Report and JSON outputs are written atomically as individual files, but not as one transaction pair.
- This is not certification readiness or independent audit assurance.

### Freeze Assessment
- No High risks found in final Codex review.
- No remaining code blocker identified for v1.0 freeze.

---

## MVP1-Clause04-Pilot-v0.9.3

Date: 2026-07-12

Status: Final release polish before v1.0

### Changed
- Clarified console wording to avoid overstating assurance.
- Added generated report disclaimer that evidence references are extracted and not independently verified.
- Updated report wording for Actual Evidence References.
- Aligned report no-gap wording with console no-gap wording.

### Added
- Added per-section alignment test to confirm each evidence reference appears under the correct Clause 04 question section.

### Validation
- End-to-end tests: 9 passed.
- Full pytest suite: 73 passed.

---

## MVP1-Clause04-Pilot-v0.9.2

Date: 2026-07-12

Status: Evidence-reference gap hardening

### Fixed
- Added gap detection for missing structured evidence references.
- Added regression tests for records that have expected evidence but no extracted evidence reference.
- Confirmed Markdown report structure remains complete after the previous report-generation fix.
- Confirmed JSON evidence records and Markdown report generation still work.

### Validation
- Gap detector tests: 11 passed.
- Full pytest suite: 72 passed.
- Runner completed successfully.
- Rule-based readiness score: 100.0%.
- Final result: No structural, response-quality, or evidence-reference gaps detected in the loaded Clause 04 pilot scope.

### Accepted v1.0 Pilot Limitations
- Evidence references are extracted but not verified against actual files.
- Evidence file contents are not validated.
- Validator remains rule-based and heuristic.
- Owner and date fields are checked syntactically, not semantically.
- Report and JSON outputs are written atomically as individual files, but not as a single transaction pair.

---

## MVP1-Clause04-Pilot-v0.9.1

Date: 2026-07-12

Status: Report structure regression fix

### Fixed
- Fixed Markdown report generation indentation issue.
- Ensured each Clause 04 record shows its own Actual Evidence References section.
- Ensured each Clause 04 record shows its own Response section.
- Ensured the report always includes the `## Gaps` heading.
- Added end-to-end regression test to prevent incomplete report generation.
- Updated C4-Q03 response to include structured evidence reference: `Clause4_AIMS_Scope_Statement.xlsx`.

### Validation
- Runner completed successfully.
- Readiness score: 100.0%.
- Final result: No gaps detected.
- End-to-end tests: 8 passed.
- Full pytest suite: 70 passed.

### Result
- Codex High finding resolved.
- Markdown audit artifact is now structurally complete.
- JSON evidence records and Markdown report are aligned.

---

## MVP1-Clause04-Pilot-v0.9

Date: 2026-07-08

Status: Test-backed Clause 04 pilot baseline

### Added
- Added pytest test suite for Clause 04 pilot.
- Added Clause 04 coverage tests.
- Added validator scoring tests.
- Added gap detector tests.
- Added input validation tests.
- Added evidence schema tests.
- Added end-to-end generation tests.

### Validation
- Clause 04 coverage tests: 5 passed.
- Validator tests: 15 passed.
- Gap detector tests: 9 passed.
- Input validator tests: 21 passed.
- Evidence schema tests: 12 passed.
- End-to-end tests: 7 passed.

### Result
- Total tests passed: 69.
- Clause 04 pilot is now test-backed.
- Main runner still completes successfully.
- Final readiness score remains 97.5%.
- Final run reports: No gaps detected.

### Current Limitation
- Evidence references are extracted but not verified against actual files.
- Score remains a pilot readiness indicator, not an independent audit conclusion.

---

## MVP1-Clause04-Pilot-v0.8

Date: 2026-07-08

### Changed
- Updated Markdown report wording to avoid overstating audit assurance.
- Renamed report title to ISO/IEC 42001 Clause 4 Rule-based Readiness Report.
- Renamed the readiness section to Clause 4 Rule-based Readiness Score.
- Added disclaimer that the score is based on the loaded Clause 4 question set, rule-based response checks, and structural coverage checks.
- Replaced “No major gaps detected” with pilot-scope wording.
- Added expected evidence and actual evidence references to the Markdown report.

### Fixed
- Corrected report generation indentation issue after adding expected/actual evidence sections.
- Ensured report writing remains inside generate_markdown_report().
- Confirmed repeated runs complete successfully.

### Validation
- Ran `python -m clause_04_context.run_clause04_demo`.
- Final readiness score: 97.5%.
- Final result: No gaps detected.
- Markdown report and JSON evidence records generated successfully.
- Added dedicated Clause 04 coverage test file.
- `pytest` collected 5 tests and 5 passed.

### Result
- Codex point 8 resolved.
- Generated artifacts are now more audit-honest.
- The report no longer implies certification readiness or full audit assurance.

### Current Limitation
- Evidence references are extracted but not verified against actual files.
- Score remains a pilot readiness indicator, not an independent audit conclusion.

---

## MVP1-Clause04-Pilot-v0.7

Date: 2026-07-08

### Changed
- Separated Markdown report generation from JSON evidence record saving.
- Removed evidence saving side effect from generate_markdown_report().
- Moved output saving responsibility into main().
- Added atomic file writing for report and evidence outputs using temporary files before replacement.

### Result
- Output generation is cleaner and less coupled.
- Evidence JSON and Markdown report writing are now handled as separate responsibilities.
- Failed writes are less likely to leave partially written output files.

### Current Limitation
- Output files are still generated locally only.
- Evidence references are still extracted but not verified against actual files.

---

## MVP1-Clause04-Pilot-v0.6

Date: 2026-07-08

### Fixed
- Added defensive input validation for Clause 4 question and response files.
- Added required field checks for question records.
- Added required field checks for response records.
- Added duplicate question ID detection before scoring.
- Added duplicate response ID detection before scoring.
- Added unexpected response ID detection before scoring.
- Added missing response detection before scoring.
- Improved JSON parsing errors with file name, line, and column.
- Updated match_response() to avoid silently selecting the first duplicate.

### Result
- Malformed or misaligned input files now fail early with clear messages.
- The pilot is more reliable for future unit testing and Codex review.

### Current Limitation
- Evidence references are still extracted but not verified against actual files.

---

## MVP1-Clause04-Pilot-v0.5

Date: 2026-07-08

### Fixed
- Improved evidence schema audit traceability.
- Added expected_evidence into each evidence record.
- Added actual_evidence_references extracted from human responses.
- Changed confidence_type to rule_based_response_quality.
- Preserved response_source_type separately from evidence references.

### Result
- JSON evidence records now identify both the expected evidence and the cited evidence reference.
- The system no longer only records assertions about evidence; it now preserves structured evidence references.

### Current Limitation
- Evidence references are extracted but not yet verified against actual files.
- Evidence file existence and content validation remain future work.

---

## MVP1-Clause04-Pilot-v0.4

Date: 2026-07-08

### Fixed
- Added structural coverage gap detection for Clause 4.
- Added required subclause coverage checks for Clause 4.1, 4.2, 4.3, and 4.4.
- Added detection for missing required subclauses.
- Added detection for unexpected response IDs.
- Added detection for duplicate question IDs.
- Added detection for duplicate response IDs.
- Added detection for missing responses for valid questions.
- Readiness score is now capped when structural coverage gaps are found.

### Validation
- Temporarily removed C4-Q04 from the question bank.
- System correctly detected missing Clause 4.4.
- System correctly capped readiness at 74.0%.
- Removed orphan C4-Q05 response from the human response file.
- Restored clean Clause 4 coverage from C4-Q01 to C4-Q04.
- Final run completed with readiness score of 97.5%.
- Final run reported: No gaps detected.

### Result
- Codex finding resolved: gap detection can now identify missing coverage and unexpected response IDs.
- Clause 4 pilot is now more audit-honest because the system can no longer silently omit a required subclause.

### Current Limitation
- Evidence files are still referenced but not directly verified.
- The score remains a rule-based response quality/readiness score, not full audit assurance.

---

## MVP1-Clause04-Pilot-v0.3

Date: 2026-07-06

### Changed
- Replaced simple substring-based validator with stricter rule-based response quality scoring.
- Added negation and gap-language detection.
- Added regex-based evidence, owner, date, and clause relevance checks.
- Increased auditor review threshold.
- Reduced risk of vague or misleading responses scoring too highly.

### Result
- Clause 4 readiness changed from 100.0% to 97.5%.
- Score is now more conservative and more audit-honest.

### Notes
- Evidence files are still not verified directly.
- Score should not yet be treated as audit assurance.

---

## MVP1-Clause04-Pilot-v0.2

Date: 2026-07-06

### Added
- Added Clause 4.4 question and response.
- Confirmed Clause 4 coverage from 4.1 to 4.4.
- Added JSON evidence record output.

### Fixed
- Corrected invalid 100% readiness issue caused by missing Clause 4.4.

---

## MVP1-Clause04-Pilot-v0.1

Date: 2026-07-04

### Added
- Initial Clause 4 pipeline.
- Question bank for Clause 4.1 to 4.3.
- Manual response input.
- Deterministic validator.
- Gap detector.
- Markdown readiness report.

### Status
- First working pilot baseline.
