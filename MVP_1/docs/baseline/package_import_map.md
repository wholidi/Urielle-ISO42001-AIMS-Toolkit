# Clause 4 Package and Execution Map

## Current execution command

From the inner `MVP_1` directory:

```powershell
python -m clause_04_context.run_clause04_demo
```

## Test command

```powershell
python -m pytest -q
```

## Existing deterministic package

The authoritative deterministic Clause 4 implementation is:

- `clause_04_context/`

This package remains frozen during the MVP_1 agentic pilot.

## Import inventory

The Phase 0 import inventory is stored at:

- `reports/regression/phase_0/python_import_inventory.txt`

## Existing execution flow

The current Clause 4 demo already coordinates:

1. Loading Clause 4 questions and human responses.
2. Validating the question and response inputs.
3. Matching questions to responses.
4. Calculating rule-based response-quality scores.
5. Creating evidence records.
6. Detecting structural, response-quality, and evidence-reference gaps.
7. Calculating the Clause 4 readiness score.
8. Generating the readiness report.
9. Writing evidence records.

The detailed Phase 0 review is stored at:

- `reports/regression/phase_0/orchestration_review.txt`

## Authoritative implementation ownership

The existing deterministic functions remain authoritative:

- Input validation: `clause_04_context/validator/input_validator.py`
- Response scoring: `clause_04_context/validator/validator.py`
- Evidence-record creation: `clause_04_context/schema/evidence.py`
- Gap detection and readiness: `clause_04_context/fabric/gap_detector.py`
- Current deterministic orchestration: `clause_04_context/run_clause04_demo.py`

## Agentic integration rule

Future agentic modules must invoke approved interfaces from the existing Clause 4 package.

They must not:

- duplicate deterministic scoring logic;
- recreate validation rules;
- recreate gap-detection rules;
- introduce a second Clause 4 readiness calculation;
- overwrite source responses or evidence;
- silently modify deterministic output.

## Intended execution boundary

```text
Agentic supervisor
        |
        v
Clause 4 adapter or approved package interface
        |
        v
Existing clause_04_context implementation
        |
        v
Deterministic baseline result
        |
        v
Agentic evidence assessment and findings
```

The agentic layer may enrich the deterministic result with:

- evidence decisions;
- confidence and uncertainty;
- findings;
- human-review status;
- provenance;
- execution logs.

## Duplicate-orchestration conclusion

The existing demo already performs deterministic Clause 4 sequencing.

The future supervisor will control higher-level workflow progression and specialist-agent delegation, while existing validators, gap detectors, scoring functions, and readiness calculations remain authoritative.

The supervisor must coordinate the deterministic package rather than reproduce its internal business logic.

## Runtime-output observation

The existing demo writes timestamped evidence records to:

- `clause_04_context/evidence/clause4_evidence_records.json`

It also regenerates:

- `reports/clause4_readiness_report.md`

The frozen demo remains unchanged for regression purposes.

Future agentic execution should redirect derived evidence decisions, execution logs, and generated findings to dedicated MVP_1 output locations such as:

- `reports/`
- `runtime/`
- `audit_logs/`

## Evidence Assessor boundary

The current deterministic implementation extracts evidence references from human-response text.

It does not independently verify:

- file existence;
- file readability;
- provenance;
- relevance;
- ownership;
- content sufficiency;
- whether the evidence actually supports the response.

Those checks belong to the future Evidence Assessor.
