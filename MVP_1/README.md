# MVP_1 — Governed Agentic Clause 04 Assessment

`MVP_1` is the executable part of the Urielle ISO/IEC 42001 AIMS Toolkit. It
combines a frozen deterministic Clause 04 readiness engine with governed
orchestration, evidence decisions, finding generation, explicit human review,
and auditable report generation.

The implementation is an audit-readiness and portfolio demonstration. It does
not provide certification, make certification decisions, or replace qualified
human review.

## Requirements

- Python 3.11 or newer
- `pip`

## Clean-clone installation

From the repository root:

```bash
python -m venv .venv
```

Activate the environment.

Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Linux or macOS:

```bash
source .venv/bin/activate
```

Install the executable MVP and its test dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e "./MVP_1[dev]"
```

## Validation

Run the complete test suite from the repository root:

```bash
python -m pytest MVP_1/tests
```

Run the governed Clause 04 acceptance demonstration:

```bash
python -m scripts.run_agentic_clause04_demo
```

The demonstration writes its report, execution-event log, and acceptance
summary to `MVP_1/reports/evidence/agentic_clause04/`.

## Design boundaries

- The frozen deterministic Clause 04 engine remains the readiness-scoring
  authority.
- The agentic workflow does not recalculate readiness.
- Invalid workflow and human-review inputs fail closed.
- Human dispositions are externally supplied and are never invented.
- No LLM or external model participates in the governed acceptance path.
- A referenced document is not represented as independently verified evidence.