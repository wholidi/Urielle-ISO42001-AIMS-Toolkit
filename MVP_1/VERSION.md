# MVP1 Clause 04 Pilot

Current Version: MVP1-Clause04-Pilot-v1.0  
Status: Frozen / Released Clause 04 rule-based pilot baseline

Release Artifact:
- MVP1-Clause04-Pilot-v1.0.zip

Release Scope:
- ISO/IEC 42001 Clause 04 only
- Rule-based readiness and evidence traceability pilot
- Not certification readiness
- Not independent audit assurance

---

## v1.0 Release Summary

MVP1-Clause04-Pilot-v1.0 is the frozen baseline for the Clause 04 pilot.

It covers:

- Clause 4.1 — Understanding the organization and its context
- Clause 4.2 — Understanding the needs and expectations of interested parties
- Clause 4.3 — Determining the scope of the AI management system
- Clause 4.4 — AI management system

Current validation:

- Runner command: `python -m clause_04_context.run_clause04_demo`
- Runner result: PASS
- Rule-based readiness score: 100.0%
- Final runner result: No structural, response-quality, or evidence-reference gaps detected in the loaded Clause 04 pilot scope.
- End-to-end tests: 9 passed
- Gap detector tests: 11 passed
- Full pytest suite: 73 passed

Generated outputs:

- Markdown report: `reports/clause4_readiness_report.md`
- JSON evidence records: `clause_04_context/evidence/clause4_evidence_records.json`

---

## Included Capabilities

- Clause 04 question bank
- Manual human response input
- Defensive input validation
- Rule-based response quality scoring
- Clause 04 structural coverage checks
- Missing structured evidence reference detection
- Gap detection
- Markdown readiness report generation
- JSON evidence record generation
- Evidence traceability fields:
  - `expected_evidence`
  - `actual_evidence_references`
  - `response_source_type`
  - `confidence_type`
- Atomic individual output writes
- Pytest test suite

---

## Accepted v1.0 Pilot Limitations

- Evidence references are extracted from human responses but not independently verified.
- Referenced evidence files are not checked for existence.
- Referenced evidence file contents are not validated.
- Validator remains rule-based and heuristic.
- Owner and date fields are checked syntactically, not semantically.
- Report and JSON outputs are written atomically as individual files, but not as one transaction pair.
- This pilot covers Clause 04 only.
- This pilot does not provide certification readiness or independent audit assurance.

---

## Version History

### MVP1-Clause04-Pilot-v0.1

Status: Initial working baseline

Completed:
- Clause 4 question bank
- Manual human response input
- Clause-aware deterministic validator
- Evidence record generation
- Markdown readiness report
- JSON evidence output
- Gap detection
- Initial Clause 4 readiness score: 100%

Limitation:
- Only Clause 4.1–4.3 were included.
- Clause 4.4 was missing, so the 100% readiness score was not valid for complete Clause 4 coverage.

---

### MVP1-Clause04-Pilot-v0.2

Status: Working Clause 4 baseline

Completed:
- Added Clause 4.1 question and response
- Added Clause 4.2 question and response
- Added Clause 4.3 question and response
- Added Clause 4.4 question and response
- Confirmed Clause 4 coverage from 4.1 to 4.4
- Markdown readiness report
- JSON evidence records

Fix from Codex review:
- Added missing Clause 4.4 so readiness no longer reflects only 4.1–4.3.

---

### MVP1-Clause04-Pilot-v0.3

Status: Validator hardening baseline

Completed:
- Replaced simple keyword scoring with stricter rule-based response quality scoring
- Added negation and gap-language detection
- Added regex-based evidence, owner, date, and clause relevance checks
- Increased auditor review threshold
- Reduced risk of vague or misleading responses scoring too highly

Result:
- Clause 4 readiness changed from 100.0% to 97.5%
- Score became more conservative and audit-honest

Limitation:
- Evidence files are referenced but not verified directly.

---

### MVP1-Clause04-Pilot-v0.4

Status: Structural coverage control baseline

Completed:
- Added structural coverage gap detection
- Added required subclause checks for Clause 4.1, 4.2, 4.3, and 4.4
- Added duplicate question ID detection
- Added duplicate response ID detection
- Added unexpected response ID detection
- Added missing response detection
- Readiness score is capped when structural coverage gaps are found

Validation:
- Temporarily removed C4-Q04 from the question bank
- System correctly detected missing Clause 4.4
- System correctly capped readiness at 74.0%
- Removed orphan C4-Q05 response
- Final run returned: No gaps detected

---

### MVP1-Clause04-Pilot-v0.5

Status: Evidence traceability baseline

Completed:
- Improved evidence schema audit traceability
- Added `expected_evidence` to each evidence record
- Added `actual_evidence_references` extracted from human responses
- Added `response_source_type`
- Changed `confidence_type` to `rule_based_response_quality`

Result:
- JSON evidence records now preserve both expected evidence and cited evidence references

Limitation:
- Evidence references are extracted but not verified against actual files.

---

### MVP1-Clause04-Pilot-v0.6

Status: Defensive input validation baseline

Completed:
- Added defensive input validation for question and response files
- Added required field checks for questions
- Added required field checks for responses
- Added duplicate ID detection before scoring
- Added unexpected response ID detection before scoring
- Added missing response detection before scoring
- Improved JSON parsing error messages
- Updated `match_response()` to avoid silently selecting the first duplicate

Result:
- Malformed or misaligned input files now fail early with clearer messages

---

### MVP1-Clause04-Pilot-v0.7

Status: Output responsibility cleanup baseline

Completed:
- Separated Markdown report generation from JSON evidence record saving
- Removed evidence-saving side effect from `generate_markdown_report()`
- Moved output saving responsibility into `main()`
- Added atomic file writing using temporary files before replacement

Result:
- Output generation is cleaner and less coupled
- Failed writes are less likely to leave partially written output files

---

### MVP1-Clause04-Pilot-v0.8

Status: Audit-honest report wording baseline

Completed:
- Renamed report title to `ISO/IEC 42001 Clause 4 Rule-based Readiness Report`
- Renamed readiness section to `Clause 4 Rule-based Readiness Score`
- Renamed per-question score to `Rule-based Response Quality Score`
- Added disclaimer that the score is not certification or full audit assurance
- Replaced “No major gaps detected” with pilot-scope wording
- Added expected evidence and actual evidence references to the Markdown report

Result:
- Generated artifacts no longer imply certification readiness or full audit assurance

---

### MVP1-Clause04-Pilot-v0.9

Status: Test-backed Clause 04 pilot baseline

Completed:
- Added pytest test suite for Clause 04 pilot
- Added Clause 04 coverage tests
- Added validator scoring tests
- Added gap detector tests
- Added input validator tests
- Added evidence schema tests
- Added end-to-end generation tests

Validation:
- Clause 04 coverage tests: 5 passed
- Validator tests: 15 passed
- Gap detector tests: 9 passed
- Input validator tests: 21 passed
- Evidence schema tests: 12 passed
- End-to-end tests: 7 passed
- Total tests passed: 69

---

### MVP1-Clause04-Pilot-v0.9.1

Status: Report structure regression fix

Completed:
- Fixed Markdown report generation indentation issue
- Ensured each Clause 04 record shows its own Actual Evidence References section
- Ensured each Clause 04 record shows its own Response section
- Ensured the report always includes the `## Gaps` heading
- Added end-to-end regression test for report structure
- Updated C4-Q03 response to include structured evidence reference: `Clause4_AIMS_Scope_Statement.xlsx`

Validation:
- End-to-end tests: 8 passed
- Full pytest suite: 70 passed

---

### MVP1-Clause04-Pilot-v0.9.2

Status: Evidence-reference gap hardening

Completed:
- Added gap detection for missing structured evidence references
- Added regression tests for records that have expected evidence but no extracted evidence reference
- Confirmed JSON evidence records and Markdown report generation still work

Validation:
- Gap detector tests: 11 passed
- Full pytest suite: 72 passed

---

### MVP1-Clause04-Pilot-v0.9.3

Status: Final release polish before v1.0

Completed:
- Clarified console wording to avoid overstating assurance
- Added generated report disclaimer that evidence references are extracted and not independently verified
- Updated report wording for Actual Evidence References
- Added per-section alignment test to confirm each evidence reference appears under the correct Clause 04 question section
- Aligned report no-gap wording with console no-gap wording

Validation:
- End-to-end tests: 9 passed
- Full pytest suite: 73 passed

---

### MVP1-Clause04-Pilot-v1.0

Status: Frozen / Released Clause 04 rule-based pilot baseline

Completed:
- Frozen Clause 04 pilot as v1.0
- Release artifact: `MVP1-Clause04-Pilot-v1.0.zip`
- No High risks found in final Codex review
- No remaining code blocker identified for v1.0 freeze

Validation:
- Runner command passed: `python -m clause_04_context.run_clause04_demo`
- Rule-based readiness score: 100.0%
- Final runner result: No structural, response-quality, or evidence-reference gaps detected in the loaded Clause 04 pilot scope.
- Full pytest suite passed: 73 tests