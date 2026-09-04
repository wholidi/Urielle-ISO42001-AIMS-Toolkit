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

## Portfolio scenarios

Phase 3.2 adds three persistent Clause 04 scenarios for review demonstrations:

| Scenario | Evidence state | Human disposition | Report |
|---|---|---|---|
| `SCN-01-COMPLETE` | Four structured references | No findings require disposition | `FINAL` |
| `SCN-02-INCOMPLETE` | Missing and partial evidence | Two findings remain pending | `DRAFT` |
| `SCN-03-REVIEWED` | Missing, partial, and flagged evidence | Accepted, modified, and rejected | `FINAL` |

Run all scenarios from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_clause04_portfolio_scenarios
```

The scenario definitions are stored in `MVP_1/scenarios/clause04/`. Generated
portfolio artifacts are stored in
`MVP_1/reports/portfolio/clause04/<scenario-id>/`. Each scenario persists its
input, evidence decisions, findings, human-review records, execution events,
acceptance summary, and governed Markdown report.

Scenario timestamps are fixed test metadata. Production components retain UTC
wall-clock timestamps unless a clock is explicitly supplied. This makes the
portfolio artifacts byte-for-byte reproducible without changing normal runtime
behavior or Clause 04 scoring.

## Design boundaries

- The frozen deterministic Clause 04 engine remains the readiness-scoring
  authority.
- The agentic workflow does not recalculate readiness.
- Invalid workflow and human-review inputs fail closed.
- Human dispositions are externally supplied and are never invented.
- No LLM or external model participates in the governed acceptance path.
- A referenced document is not represented as independently verified evidence.
- A `FINAL` report means no generated finding remains pending; it is not a
  certification or conformity decision.
