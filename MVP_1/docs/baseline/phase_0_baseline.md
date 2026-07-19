# Phase 0 Baseline Record

## Purpose

This record freezes the existing deterministic ISO/IEC 42001 Clause 4 implementation before introducing the agentic assessment layer.

## Repository boundary

The repository-level folders are the authoritative manual framework:

- `04_Context/`
- `05_Leadership/`
- `Evidence_Repository/`

The executable agentic pilot is contained within:

- `MVP_1/`

## MVP_1 scope

MVP_1 covers ISO/IEC 42001 Clause 4 only.

Clause 5 and other clauses remain outside the MVP_1 execution scope.

## Frozen deterministic implementation

The existing implementation is located at:

- `MVP_1/clause_04_context/`

The agentic pilot must not duplicate or silently modify its:

- questions;
- validation rules;
- gap-detection logic;
- scoring rules;
- readiness calculation;
- report-generation logic.

## Execution baseline

Runner:

```powershell
cd MVP_1
python -m clause_04_context.run_clause04_demo
```

Test command:

```powershell
cd MVP_1
python -m pytest -q
```

Verified results:

- Rule-based readiness score: `100.0%`
- Existing test suite: `73 passed`
- Structural, response-quality, and evidence-reference gaps: none detected

## Regression artifacts

The Phase 0 regression artifacts are stored under:

- `MVP_1/reports/regression/phase_0/pytest_summary.txt`
- `MVP_1/reports/regression/phase_0/clause04_demo_console.txt`
- `MVP_1/reports/regression/phase_0/clause04_baseline_report.md`
- `MVP_1/reports/regression/phase_0/clause04_baseline_report.sha256.txt`

## Accepted limitation

The current implementation records evidence references but does not independently verify:

- whether the referenced file exists;
- whether its contents support the response;
- provenance and ownership;
- relevance to the applicable Clause 4 requirement;
- sufficiency and completeness.

The future Evidence Assessor will address this limitation.

## Read-only source boundary

During the MVP_1 pilot, these locations are treated as read-only:

- `04_Context/`
- `05_Leadership/`
- `Evidence_Repository/`
- original human-response files;
- submitted source evidence;
- `MVP_1/clause_04_context/` during runtime.

Generated outputs must be written inside approved MVP_1 output locations, including:

- `MVP_1/reports/`
- `MVP_1/runtime/`
- `MVP_1/audit_logs/`

## Runtime-output observation

The existing Clause 4 demo refreshes timestamps in:

- `MVP_1/clause_04_context/evidence/clause4_evidence_records.json`

It also regenerates:

- `MVP_1/reports/clause4_readiness_report.md`

For Phase 0, these generated changes were preserved as regression artifacts and then restored so that the frozen implementation remained unchanged.

Future agentic execution should redirect generated evidence decisions and audit records to dedicated runtime or reporting directories.

## Phase 0 exit criteria

Phase 0 is complete when:

1. The feature branch exists.
2. The existing test suite passes.
3. The Clause 4 demo executes successfully.
4. The baseline report and checksum are preserved.
5. Existing package imports and execution flow are documented.
6. Duplicate orchestration risk is reviewed.
7. Evidence and human responses are designated read-only.
8. The sequential-supervisor architecture decision is recorded.
