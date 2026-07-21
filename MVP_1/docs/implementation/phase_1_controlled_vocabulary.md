# Phase 1 Controlled Vocabulary

Status: Proposed for Phase 1 schema implementation
Schema version: 1.0.0
Branch: feature/agentic-clause04-phase1

## Applicability status

- `APPLICABLE`
- `NOT_APPLICABLE`
- `REVIEW_REQUIRED`

## Evidence decision

- `EVIDENCED`
- `PARTIALLY_EVIDENCED`
- `NOT_EVIDENCED`
- `NOT_APPLICABLE`
- `REQUIRES_HUMAN_JUDGEMENT`

## Preliminary finding severity

- `LOW`
- `MEDIUM`
- `HIGH`
- `REVIEW_REQUIRED`

## Human review disposition

- `PENDING`
- `ACCEPTED`
- `MODIFIED`
- `REJECTED`

`PENDING` means that no human disposition has been recorded.

## Workflow state

- `INITIALISED`
- `SCOPE_PENDING`
- `VALIDATING`
- `ASSESSING_EVIDENCE`
- `GENERATING_FINDINGS`
- `REPORT_DRAFTED`
- `REVIEW_PENDING`
- `COMPLETED`
- `FAILED`

## Execution-event status

- `STARTED`
- `SUCCEEDED`
- `FAILED`
- `BLOCKED`
- `AWAITING_HUMAN_REVIEW`

## Design rules

1. Contract values use uppercase snake case.
2. Schemas reject vocabulary values not listed here.
3. `REVIEW_REQUIRED` represents unresolved applicability or severity.
4. `REQUIRES_HUMAN_JUDGEMENT` is reserved for evidence decisions.
5. Finding disposition is separate from workflow approval action.
6. Workflow state describes the assessment run.
7. Event status describes one execution event.
8. Controlled values may change only through a versioned schema change.
