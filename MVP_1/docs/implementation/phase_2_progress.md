# Phase 2 Progress Record

## Purpose

This record documents the Phase 2 deterministic governance enforcement layer: the configuration contracts, fail-closed enforcement code, and acceptance tests that were merged to `main` after Phase 1's assessment contracts.

## Phase 2.0 — Scope and constraint

Status: Passed
Merge commit: 5f096955 (5f0969555b0beb590419caceb3a51f32e4be5eb8)
Main merge commit: 91a3763
Files merged: 25
Full pytest suite: 132 passed
Frozen Clause 4 tree ID: d8531b048382779c9c1a2d93620756d449630c9f
Protected paths: Unchanged (`04_Context/`, `05_Leadership/`, `Evidence_Repository/`, `MVP_1/clause_04_context/`)

Phase 2 introduces deterministic governance configuration, fail-closed policy enforcement, and fail-closed startup validation. Phase 2 does not introduce a supervisor, a specialist assessment agent, a report or finding generator, or any LLM/external model integration.

## Phase 2.1 — Governance configuration contracts

Status: Passed
Schemas added:

- `MVP_1/governance/schemas/agent_registry.schema.json`
- `MVP_1/governance/schemas/permission_matrix.schema.json`
- `MVP_1/governance/schemas/human_approval_rules.schema.json`
- `MVP_1/governance/schemas/model_use_record.schema.json`

Configuration instances added:

- `MVP_1/governance/agent_registry.yaml` (registry version 0.2.0)
- `MVP_1/governance/permission_matrix.yaml` (matrix version 0.2.0)
- `MVP_1/governance/human_approval_rules.yaml` (rules version 0.2.0)
- `MVP_1/governance/model_use_record.yaml` (record version 0.2.0)

Result: All four governance configuration documents validate against their JSON Schemas (draft 2020-12) and against the Phase 1 controlled vocabulary conventions (uppercase snake case, closed enumerations).

## Phase 2.2 — Component registry

Status: Passed
File: `MVP_1/governance/agent_registry.yaml`
Default execution mode: `DETERMINISTIC_ONLY`

Registered components:

- `governance.configuration_loader` — implementation: `governance.config_loader.ConfigurationLoader`
- `governance.policy_enforcer` — implementation: `governance.policy_enforcer.PolicyEnforcer`
- `governance.audit_logger` — implementation: `governance.audit_logger.AuditLogger`
- `governance.schema_validator` — implementation: `governance.schema_validator.SchemaValidator`

Each entry declares `allowed_actions`, `prohibited_actions`, and `human_approval_required`. Every registered component is currently marked `enabled: true` and `execution_mode: DETERMINISTIC_ONLY`.

**Open item:** `governance.audit_logger.AuditLogger` and `governance.schema_validator.SchemaValidator` are registered and enabled in this file, but no corresponding Python module exists in the Phase 2 codebase as merged. No test currently imports or exercises either implementation path. This is a registry/implementation mismatch that should be resolved — either by implementing the two modules or by marking them `enabled: false` — before the registry is treated as an accurate runtime inventory. See Phase 3 scope.

## Phase 2.3 — Permission matrix

Status: Passed
File: `MVP_1/governance/permission_matrix.yaml`
Default decision: `DENY`
Deny precedence: `true`
Unregistered component decision: `DENY`

Each registered component has a corresponding permission entry scoped to one resource, with explicit `allowed_actions`, `denied_actions`, and `human_approval_actions`. No component has a default allow; every permitted action is enumerated individually.

## Phase 2.4 — Human approval rules

Status: Passed
File: `MVP_1/governance/human_approval_rules.yaml`
Default decision: `REQUIRE_HUMAN_APPROVAL`
Self-approval prohibited: `true`
Approval bypass prohibited: `true`

Six approval rules defined (HAR-001 through HAR-006), covering acceptance, modification, and rejection of assessment findings, confirmation of not-applicable status, evidence-decision approval, and policy-decision override. Every rule requires a reason, an evidence reference, and disallows automated approval. Overriding a policy decision (HAR-006) requires two approvals from a defined role set.

## Phase 2.5 — Model-use record

Status: Passed
File: `MVP_1/governance/model_use_record.yaml`
Execution mode: `DETERMINISTIC_ONLY`
Model use status: `NOT_IN_USE`
External model calls allowed: `false`
Generative model calls allowed: `false`
Reviewed by role: `AI_GOVERNANCE_LEAD`
Review date: 2026-08-03
Next review trigger: `BEFORE_ANY_MODEL_INTEGRATION`

Prohibited capabilities recorded for this phase: `EXTERNAL_MODEL_INVOCATION`, `GENERATIVE_TEXT_CREATION`, `AUTONOMOUS_FINDING_GENERATION`, `AUTONOMOUS_HUMAN_APPROVAL`, `SUPERVISOR_ORCHESTRATION`, `REPORT_GENERATION`.

This record is the explicit statement that Phase 2 authorizes deterministic governance configuration and enforcement only, and that the Sequential Supervisor described in ADR-0001 has not been authorized or implemented as of this phase.

## Phase 2.6 — Fail-closed policy enforcer

Status: Passed
File: `MVP_1/governance/policy_enforcer.py`

`PolicyEnforcer.evaluate()` returns one of `ALLOW`, `DENY`, `REQUIRE_HUMAN_APPROVAL` for a given `(component_id, resource, action)` triple. Evaluation order is fail-closed:

1. Reject malformed or empty identifiers.
2. Deny if the component is not registered.
3. Deny if the component is registered but disabled.
4. Deny if the component's execution mode is not `DETERMINISTIC_ONLY`.
5. Deny if the action is in the component's `prohibited_actions`.
6. Deny if no permission entry exists for the component/resource pair.
7. Deny if the action is in the permission entry's `denied_actions` (explicit deny always wins, including on overlapping or malformed policy data).
8. Require human approval if the action is listed as an approval action or matches a human-approval rule.
9. Allow only if the action is explicitly listed in `allowed_actions`.
10. Otherwise deny by default.

## Phase 2.7 — Fail-closed startup validator

Status: Passed
File: `MVP_1/governance/startup_validator.py`

`initialize_governance()` loads all four governance configuration documents and raises `GovernanceStartupError` before constructing a runtime unless every one of the following holds: default execution mode is deterministic-only; every enabled component is deterministic-only; the permission matrix defaults to deny with deny precedence and denies unregistered components; the approval-rules default is `REQUIRE_HUMAN_APPROVAL` with self-approval and approval-bypass prohibited and every rule mandatory and non-automatable; and the model-use record remains deterministic-only, not-in-use, with external and generative model calls disabled.

If any constraint fails, the runtime does not start.

## Phase 2.8 — Governance fixtures and acceptance tests

Status: Passed
Valid fixtures: `MVP_1/tests/fixtures/governance/valid/` (agent registry, human approval rules, model-use record, permission matrix)
Invalid fixtures: `MVP_1/tests/fixtures/governance/invalid/` (same four documents, each with an injected violation)
Acceptance suite: `MVP_1/tests/test_governance_phase2_acceptance.py`

Acceptance tests confirm, among other properties: the runtime starts only in `DETERMINISTIC_ONLY` mode with `model_use_status: NOT_IN_USE`; an explicitly permitted action is allowed; an unregistered component is denied; a call to `CALL_EXTERNAL_MODEL` is denied; and an action with no explicit allow entry is denied by default.

## Phase 2.9 — Full regression

Status: Passed
Command: `python -m pytest -q` (run from `MVP_1/`)
Result: 132 passed
Clause 04 deterministic baseline: Unaffected — `MVP_1/clause_04_context/` was not modified during Phase 2
Protected paths: Unchanged

Phase 2 remains governance-configuration-only. No supervisor, specialist component, report generator, finding generator, or LLM/external model integration has been implemented or authorized. See ADR-0002 for the architectural decision record covering this layer, and the addendum to ADR-0001 for the current implementation status of the Sequential Supervisor decision.
