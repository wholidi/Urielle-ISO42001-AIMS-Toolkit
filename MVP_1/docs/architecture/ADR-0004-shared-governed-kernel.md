# ADR-0004: Clause-neutral shared governed kernel

- Status: Accepted and implemented for Toolkit Release 0.2 Step 3
- Decision date: 2026-09-16
- Scope: Clause-neutral v2 record evaluation only
- Related decisions: ADR-0001, ADR-0002, ADR-0003

## Context

Step 2 added closed v2 contracts that separate assessment planning, evidence
mapping, file integrity, human acceptance, requirement assessment, finding
disposition, execution events, and report state. The existing runtime remains
tightly coupled to Clause 04 v1 types and its authoritative readiness score.

Changing the Clause 04 runtime to consume the new contracts would create a
migration risk. Registering new runtime actors or actions during this step
would also enter the permission-expansion work reserved for Step 5.

## Decision

Step 3 adds a pure, clause-neutral Python library under
`agentic_assessment.shared_kernel`. It validates and relates existing v2
records but is not an enabled runtime component and receives no governance
permission.

The kernel provides:

- deterministic identifiers derived from canonical governed inputs;
- safe file-presence and SHA-256 verification without content interpretation;
- a fail-closed lifecycle state machine;
- question- and mapping-specific recording of externally supplied human
  evidence acceptance;
- deterministic requirement outcomes based only on linked acceptance records;
- stable draft findings with separate human disposition;
- workflow-only report status;
- contiguous, deterministic v2 execution events with explicit timestamps.

The existing `Clause04Adapter` remains the complete compatibility seam. Clause
04 does not import or call the shared kernel.

## Lifecycle decision

A lifecycle identity is derived from `assessment_id`, `mapping_id`, and
`evidence_id`. This lets two questions use the same evidence item without
sharing an acceptance decision.

Valid transitions are:

```text
REFERENCED -> FILE_PRESENT -> INTEGRITY_VERIFIED -> CONTENT_REVIEWED
     |              |                 |
     +--------------+-----------------+-> UNABLE_TO_ESTABLISH

CONTENT_REVIEWED -> ACCEPTED
CONTENT_REVIEWED -> REJECTED
```

`ACCEPTED`, `REJECTED`, and `UNABLE_TO_ESTABLISH` are terminal. Skipped,
regressive, conflicting, and terminal-state transitions fail closed.
Deterministic actors may record only deterministic states. Human states require
an identified human and comments. Acceptance and rejection are created
atomically with a matching question-specific acceptance record.

## Determinism

Finding and event identifiers use SHA-256 of canonical JSON. Finding ordering
uses question, requirement, requirement-assessment, and finding identifiers.
Event sequence is contiguous and starts at one. Timestamps are explicit inputs
and remain outside identifier derivation, so production can retain traceable
UTC time while tests use a fixed value.

## Governance boundary

The kernel is not registered in `agent_registry.yaml`, receives no entry in
`permission_matrix.yaml`, and adds no human-approval action. The current
default-deny configuration therefore continues to block any unregistered
runtime use. Step 5 must authorize and integrate any future caller.

## Consequences

- Clause 04 behavior, hashes, schemas, and public interfaces remain isolated.
- Matching hashes cannot establish support.
- Acceptance for one question cannot support another question.
- `FINAL` describes workflow state only.
- The library cannot by itself run a Clause 05 assessment.

## Exclusions

This decision adds no Clause 05 question bank, evidence map, adapter,
clause-specific evaluator, workflow, scenario, report renderer, permission,
package-version change, model integration, or certification conclusion.
