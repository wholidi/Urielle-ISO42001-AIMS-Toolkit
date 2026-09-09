# ADR-0003: Clause-Neutral Governed Assessment Extension

- Status: Accepted for Toolkit Release 0.2 implementation
- Decision date: 2026-09-09
- Scope: Toolkit Release 0.2 — ISO/IEC 42001 Clause 05 Leadership
- Decision owner: Urielle-AI
- Related decisions: ADR-0001, ADR-0002

## Context

The repository contains a complete governed Clause 04 workflow and a set of
manual Clause 05 templates. Clause 04 runtime contracts and component types are
currently tied to Clause 04 identifiers, its deterministic result type, and its
authoritative readiness score.

Copying the complete Clause 04 workflow for Clause 05 would duplicate
governance behavior and create two implementations of evidence handling,
finding disposition, event recording, and report-state control. Replacing the
Clause 04 implementation would put the frozen baseline and its regression
history at risk.

Clause 05 also requires a stronger separation between file integrity and human
judgement. A single policy may support several questions, but acceptance for
one question must not establish sufficiency for another.

## Decision

Toolkit Release 0.2 will add a clause-neutral governed assessment seam and a
Clause 05-specific deterministic layer.

The implementation will:

1. Preserve the existing Clause 04 engine, contracts, default workflow sequence,
   authoritative scores, and public interfaces.
2. Reuse shared deterministic capabilities through compatibility-preserving
   wrappers or extracted services.
3. Add new clause-neutral contracts rather than broadening the existing Clause
   04 version 1 contracts in place.
4. Record evidence acceptance against a specific question-evidence mapping.
5. Keep assessment planning, integrity verification, evidence acceptance,
   requirement evaluation, finding disposition, and report status as separate
   records and decisions.
6. Add a thin Clause 05 adapter and configuration rather than a second copy of
   the Clause 04 workflow.
7. Use no LLM or external model in the governed acceptance path.

## Clause 04 compatibility boundary

Before shared behavior is extracted, characterization tests must establish:

- the authoritative Clause 04 score;
- coverage of 4.1 through 4.4;
- normalized deterministic result content;
- the existing default sequential workflow order.

All existing Clause 04 tests must continue to pass. The Clause 04 score will not
be recalculated by any new shared or Clause 05 component.

## Clause 05 assessment boundary

Clause 05 will evaluate atomic questions under 5.1, 5.2, and 5.3. It will not
infer:

- leadership commitment from policy existence;
- policy approval from document status or filename;
- communication from a distribution list alone;
- implementation from an approved policy alone;
- responsibility, authority, appointment, or understanding from a role title;
- completed reporting from a reporting schedule.

These judgements require explicit human content review and acceptance. The
deterministic layer may summarize accepted mappings and identify missing,
rejected, inconsistent, or unresolved evidence.

## Evidence lifecycle boundary

The Phase 4 vocabulary remains authoritative:

`REFERENCED`, `FILE_PRESENT`, `INTEGRITY_VERIFIED`, `CONTENT_REVIEWED`,
`ACCEPTED`, `REJECTED`, and `UNABLE_TO_ESTABLISH`.

File presence, a matching digest, structured metadata, or confidence cannot
produce acceptance. Content review and acceptance remain explicit human acts.
Finding disposition remains a different human decision.

## Reporting boundary

Clause 05 reports will summarize per-question support and finding status. The
initial release will not create a Clause 05 numeric readiness score. A `FINAL`
report means only that no generated finding remains pending; it is not an audit
opinion, conformity determination, or certification conclusion.

## Governance configuration

Every implemented deterministic runtime component must appear in the component
registry and permission matrix. Permissions remain default-deny with deny
precedence. Deterministic orchestration and governed report generation are
permitted capabilities; external model invocation, generative text creation,
autonomous finding disposition, and automated human approval remain prohibited.

## Consequences

### Positive

- Clause 04 remains stable and independently testable.
- Clause 05 adds capability without duplicating the complete workflow.
- Evidence reused across questions cannot be accepted globally by accident.
- Human accountability remains visible in the record chain.
- The design can later support other clauses through separately approved work.

### Trade-offs

- Compatibility wrappers temporarily leave both Clause 04-specific and
  clause-neutral contracts in the repository.
- New components require explicit governance registration and permissions.
- Human review data is more granular because acceptance is mapping-specific.

## Explicit exclusions

This decision does not authorize work on other clauses, OCR, automatic document
interpretation, LLM-based sufficiency decisions, certification conclusions,
reviewer authentication, cloud integrations, a user interface, a commercial
SaaS product, or changes to Clause 04 scoring.
