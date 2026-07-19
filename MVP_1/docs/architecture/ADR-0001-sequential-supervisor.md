# ADR-0001: Sequential Supervisor Pattern for the Clause 4 Agentic Pilot

- Status: Accepted
- Decision date: 2026-07-19
- Scope: MVP_1 — ISO/IEC 42001 Clause 4
- Decision owner: Urielle-AI

## Context

MVP_1 introduces an agentic assessment capability around the existing deterministic Clause 4 implementation.

The current implementation already provides:

- structured Clause 4 questions;
- human responses;
- input validation;
- rule-based response scoring;
- evidence-reference extraction;
- gap detection;
- readiness calculation;
- evidence-record generation;
- readiness-report generation.

The pilot must add agentic capabilities without replacing, duplicating, or silently modifying this deterministic logic.

The pilot must also provide an auditable execution path showing:

- which component acted;
- which input was used;
- which output was produced;
- why the workflow progressed;
- when human review was required;
- whether evidence was accepted, rejected, or marked insufficient.

## Decision

MVP_1 will use a sequential supervisor pattern.

A single supervisor will coordinate a defined sequence of specialist activities:

```text
Assessment request
        |
        v
Assessment planning
        |
        v
Question selection
        |
        v
Deterministic Clause 4 execution
        |
        v
Evidence assessment
        |
        v
Finding generation
        |
        v
Human-review decision
        |
        v
Report generation
```

Each specialist component will return structured output to the supervisor.

The supervisor will determine whether the workflow:

- proceeds;
- retries within an approved limit;
- requests human review;
- stops safely;
- produces the final report.

## Deterministic boundary

The existing Clause 4 implementation remains authoritative for:

- input validation;
- response scoring;
- evidence-reference extraction;
- gap detection;
- readiness calculation;
- deterministic report content.

The supervisor and specialist agents must not recreate these functions.

The agentic layer may enrich the deterministic result with:

- evidence verification decisions;
- confidence and uncertainty;
- findings;
- human-review status;
- provenance;
- audit logs.

## Integration boundary

The intended integration is:

```text
Agentic supervisor
        |
        v
Clause 4 adapter or approved interface
        |
        v
Existing clause_04_context implementation
        |
        v
Deterministic baseline result
        |
        v
Agentic enrichment
```

The existing demo runner must not be treated as the final agentic interface because it writes runtime-generated records into tracked source locations.

A future adapter should invoke approved deterministic functions while redirecting generated outputs to dedicated MVP_1 runtime locations.

## Read-only boundary

The following repository-level locations are authoritative manual source inputs and must be treated as read-only during MVP_1 execution:

- `04_Context/`
- `05_Leadership/`
- `Evidence_Repository/`

The following inputs must also remain immutable during an assessment run:

- original human responses;
- submitted evidence;
- deterministic Clause 4 source files.

Corrections must be stored as:

- new versions;
- annotations;
- review decisions;
- derived assessment records.

The original source input must not be overwritten.

## Write boundary

Runtime-generated content must be written only to approved MVP_1 locations, including:

- `MVP_1/reports/`
- `MVP_1/runtime/`
- `MVP_1/audit_logs/`

The agentic workflow must not write into:

- `04_Context/`
- `05_Leadership/`
- `Evidence_Repository/`
- `MVP_1/clause_04_context/`

## Human oversight

The supervisor must route a case to human review when:

- evidence is missing;
- evidence cannot be opened or read;
- evidence relevance is uncertain;
- conflicting evidence is detected;
- confidence falls below an approved threshold;
- a material finding is proposed;
- the workflow cannot continue safely;
- a requested action would modify a source record.

## Rationale

The sequential-supervisor pattern was selected because MVP_1 covers one clause and follows a predictable assessment lifecycle.

It provides:

1. A clear execution order.
2. A single control point for audit logging.
3. Easier regression comparison with the frozen baseline.
4. Explicit human-review gates.
5. Lower coordination complexity than peer-to-peer agents.
6. Reduced risk of circular or inconsistent delegation.
7. A suitable foundation for later multi-clause orchestration.

## Alternatives considered

### Independent peer agents

Rejected for MVP_1 because peer-to-peer delegation would make execution order, ownership, and audit reconstruction unnecessarily complex.

### Fully autonomous planner

Rejected because the Clause 4 workflow is already known and does not require unconstrained planning.

### One monolithic agent

Rejected because it would combine planning, evidence assessment, finding generation, and reporting into one opaque decision boundary.

### Replace the deterministic implementation

Rejected because this would remove the existing regression baseline and introduce unnecessary scoring and validation risk.

### Duplicate the existing Clause 4 workflow inside the supervisor

Rejected because the current runner already coordinates deterministic validation, scoring, gap detection, readiness calculation, and report generation.

The supervisor must coordinate these functions rather than reproduce them.

## Consequences

### Positive

- Predictable execution.
- Clear responsibility.
- Easier testing.
- Stronger audit traceability.
- Controlled human escalation.
- Minimal disruption to the frozen Clause 4 implementation.

### Trade-offs

- Lower flexibility than dynamic multi-agent planning.
- The supervisor may become a coordination bottleneck.
- Multi-clause support will require routing and cross-clause coordination.

These trade-offs are acceptable for the single-clause MVP_1 pilot.

## Future evolution

MVP_2 may extend the pattern with:

- a clause router;
- Clause 4 and Clause 5 specialist workflows;
- cross-clause dependency analysis;
- shared evidence assessment;
- consolidated findings;
- multi-clause reporting.

That evolution must be documented through a separate architecture decision.
