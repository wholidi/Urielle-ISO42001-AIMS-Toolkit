# Toolkit Release 0.2 Phase 3 - Shared governed kernel

## Purpose

Phase 3 implements the deterministic relationships between the frozen v2
contracts. It remains clause-neutral and does not execute a Clause 05 workflow.

## Components

| Module | Responsibility |
|---|---|
| `records.py` | Immutable values with exact v2 serialization |
| `validation.py` | Schema validation, canonical identifiers, and linked-record checks |
| `lifecycle.py` | Safe file integrity and valid lifecycle transitions |
| `acceptance.py` | Externally supplied, human-only, question-specific acceptance |
| `requirements.py` | Deterministic requirement outcome from linked acceptance records |
| `findings.py` | Stable draft finding identity, ordering, and deduplication |
| `report_state.py` | `DRAFT` or workflow-only `FINAL` derivation |
| `events.py` | Explicitly authorized, ordered v2 event construction |

## Evaluation boundary

The kernel uses no content interpretation. A requirement becomes `SUPPORTED`
only when at least one `ACCEPTED` record matches the assessment, question,
mapping, evidence item, and terminal lifecycle. A present file, matching hash,
reviewed lifecycle, metadata field, or acceptance from another question cannot
support it.

All in-scope mappings explicitly rejected by humans produce `UNSUPPORTED`.
Missing, incomplete, or unresolved acceptance produces `UNRESOLVED`.
The kernel does not infer `NOT_APPLICABLE`.

## Findings and report status

`UNSUPPORTED` and `UNRESOLVED` outcomes produce deterministic `DRAFT/PENDING`
findings. Evidence acceptance cannot dispose a finding. A report remains
`DRAFT` while any finding is pending, any requirement is unresolved, or an
unsupported requirement lacks its finding. `FINAL` always uses
`WORKFLOW_STATE_ONLY` and is not a conformity or certification conclusion.

## Timestamps and repeatability

Callers provide timestamps. Identifiers and ordering do not depend on those
timestamps. Fixed test timestamps therefore produce byte-stable results while
a future authorized runtime may supply current UTC timestamps for traceability.

## Governance status

Phase 3 creates a library, not a registered runtime actor. No registry,
permission-matrix, approval-rule, or model-use configuration changes are made.
Runtime integration remains denied by default until separately authorized in
Phase 5.

## Validation

Run focused Phase 3 tests from `MVP_1`:

```powershell
python -m pytest tests/test_shared_kernel_integrity.py tests/test_shared_kernel_lifecycle.py tests/test_shared_kernel_acceptance.py tests/test_shared_kernel_linked_records.py tests/test_shared_kernel_findings.py tests/test_shared_kernel_report_state.py tests/test_shared_kernel_events.py tests/test_shared_kernel_determinism.py tests/test_phase03_compatibility.py
```
