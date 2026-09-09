# Phase 4 — Clause 04 Evidence Integrity and Provenance

## Purpose

Phase 4 closes the final planned Clause 04 capability gap: a structured filename
is no longer treated as sufficient evidence. The workflow records what can be
established deterministically and reserves content sufficiency for an explicit
human decision.

This remains a professional portfolio for reviewing an existing AI-enabled
SaaS. It is not a new SaaS product and it does not provide certification.

## Evidence lifecycle

| Status | Meaning | Authority |
|---|---|---|
| `REFERENCED` | A structured evidence identifier was supplied | Deterministic |
| `FILE_PRESENT` | A readable regular file exists within the permitted root | Deterministic |
| `INTEGRITY_VERIFIED` | Observed SHA-256 matches the declared SHA-256 | Deterministic |
| `CONTENT_REVIEWED` | A named human confirms content review | Human input |
| `ACCEPTED` | A named human accepts the evidence for the mapped question | Human input |
| `REJECTED` | A named human rejects it and records a reason | Human input |
| `UNABLE_TO_ESTABLISH` | A safe integrity conclusion cannot be established | Deterministic fail-closed result |

Each record retains ordered `status_history`; a final status therefore does not
hide the steps that preceded it.

## Trust boundaries

- File presence is not integrity.
- Integrity is not content review.
- Content review is not acceptance.
- Acceptance for one question is not ISO/IEC 42001 conformity or certification.
- Confidence is advisory and cannot elevate an evidence decision.
- Finding disposition remains separate from evidence acceptance.
- `FINAL` means no generated finding remains pending; it is not an audit opinion.

## Deterministic verifier

`EvidenceIntegrityVerifier` accepts an explicit evidence root, manifest entry,
and optional external review. It rejects absolute paths, traversal, escaped
paths, directories, unreadable files, invalid hashes, and hash mismatches. It
reads evidence only as bytes for SHA-256 and never parses or interprets content.

A present file without a declared hash stops at `FILE_PRESENT`. A review cannot
be applied until integrity is verified. Acceptance and rejection require a
named reviewer, confirmation that content was reviewed, and comments.

## Workflow integration

The seven-stage supervisor sequence is unchanged. During
`EVIDENCE_ASSESSMENT`, the assessor:

1. captures the Clause 04 evidence identifiers;
2. creates evidence-integrity records from the supplied manifest;
3. applies only externally supplied content-review records;
4. aggregates the lifecycle states into question-level evidence decisions.

Only human-accepted evidence can produce `EVIDENCED`. Missing evidence produces
`NOT_EVIDENCED`; accepted plus unresolved evidence produces
`PARTIALLY_EVIDENCED`; other referenced but unaccepted evidence produces
`REQUIRES_HUMAN_JUDGEMENT`.

## Portfolio artifacts

Each scenario now persists `evidence_integrity_records.json` alongside the
Phase 3.2 artifacts. Synthetic text fixtures exist only to demonstrate presence,
hashing, provenance, and human-decision boundaries.

- `SCN-01-COMPLETE`: four integrity-verified and human-accepted items.
- `SCN-02-INCOMPLETE`: file-present and unable-to-establish items.
- `SCN-03-REVIEWED`: content-reviewed and human-rejected items, with finding
  disposition retained as a separate process.

## Explicit exclusions

Phase 4 does not add OCR, document interpretation, LLM review, automatic
sufficiency decisions, reviewer authentication, cloud storage integration,
other ISO/IEC 42001 clauses, a UI, or a certification conclusion.

With this phase, planned Clause 04 capability development is complete. Remaining
work is release review, CI validation, and portfolio presentation.
