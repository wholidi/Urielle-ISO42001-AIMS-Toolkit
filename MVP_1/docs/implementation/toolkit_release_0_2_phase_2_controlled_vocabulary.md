# Toolkit Release 0.2 Phase 2 — Clause-neutral v2 vocabulary

Schema version: `2.0.0`

Scope: contracts only; no Clause 05 question bank, evaluator, shared kernel, or workflow

## Record boundaries

| Record | Responsibility | Must not establish |
|---|---|---|
| Assessment plan | Scope and question selection | Evidence support |
| Evidence manifest | Safe relative file references | Presence, integrity, or sufficiency |
| Evidence mapping | One question-to-item relationship | Acceptance |
| Lifecycle record | File state or explicit human review state | Cross-question acceptance |
| Acceptance record | Human decision for one assessment, question, mapping, and item | Finding disposition |
| Requirement assessment | Deterministic outcome based on acceptance-record identifiers | Certification |
| Finding | Condition, criteria, and separate human disposition | Evidence acceptance |
| Execution event | Ordered workflow facts | Assessment conclusions |
| Report state | `DRAFT` or `FINAL` workflow state | Certification or conformity |

## Controlled values

- Evidence lifecycle: `REFERENCED`, `FILE_PRESENT`, `INTEGRITY_VERIFIED`,
  `CONTENT_REVIEWED`, `ACCEPTED`, `REJECTED`, `UNABLE_TO_ESTABLISH`.
- Evidence acceptance: `ACCEPTED`, `REJECTED`; decision maker is always `HUMAN`.
- Requirement outcome: `SUPPORTED`, `UNSUPPORTED`, `UNRESOLVED`, `NOT_APPLICABLE`.
- Finding disposition: `PENDING`, `ACCEPTED`, `MODIFIED`, `REJECTED`.
- Finding status: `DRAFT`, `RESOLVED`.
- Report status: `DRAFT`, `FINAL`; conclusion type is always `WORKFLOW_STATE_ONLY`.

## Fail-closed rules

- Paths are repository-relative, use `/`, and reject absolute paths,
  backslashes, and parent traversal.
- Deterministic actors can record file states only. Human review states require comments.
- Acceptance requires an identified human reviewer, timestamp, and rationale.
- `SUPPORTED` requires at least one question-specific acceptance-record ID; a
  digest or lifecycle record cannot substitute for it.
- A pending finding is always `DRAFT`. Finding disposition is independent from
  evidence acceptance.
- A `FINAL` report has neither pending findings nor unresolved requirements.
  `FINAL` is not a certification conclusion.
- Every contract rejects unknown fields and unlisted vocabulary.
