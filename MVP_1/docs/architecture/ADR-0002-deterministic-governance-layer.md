# ADR-0002: Deterministic Governance Enforcement Layer for the Clause 4 Agentic Pilot

- Status: Accepted
- Decision date: 2026-08-03
- Scope: MVP_1 — Phase 2, governance configuration and enforcement
- Decision owner: Urielle-AI
- Related: Supersedes no prior decision; extends [ADR-0001](./ADR-0001-sequential-supervisor.md)

## Context

ADR-0001 established the Sequential Supervisor pattern for MVP_1 and defined a Human oversight section listing the conditions under which the workflow must route to human review. ADR-0001 did not specify a concrete enforcement mechanism for those conditions, and Phase 1 built only the assessment data contracts (`assessment_plan`, `evidence_decision`, `finding`, `execution_event`) — no supervisor, no specialist component, and no policy enforcement existed at the end of Phase 1.

Before any supervisor, specialist agent, or model integration is authorized, MVP_1 requires a deterministic control layer that can:

- register every runtime component and its permitted actions;
- deny any action that is not explicitly permitted;
- make human-approval requirements enforceable rather than descriptive;
- refuse to start if any safety invariant does not hold;
- record, in an auditable and versioned form, that no model is currently in use.

Phase 2 builds this layer. It does not build the supervisor itself.

## Decision

MVP_1 will use a deterministic, fail-closed governance enforcement layer, implemented in `MVP_1/governance/`, consisting of:

- an **agent registry** (`agent_registry.yaml`) naming every runtime component, its execution mode, and its allowed and prohibited actions;
- a **permission matrix** (`permission_matrix.yaml`) mapping each component and resource to explicitly allowed and denied actions, with a default decision of `DENY` and deny precedence over allow;
- a set of **human approval rules** (`human_approval_rules.yaml`) defining, per action, the minimum approvals, eligible approval roles, and mandatory reason and evidence-reference requirements, with self-approval and approval bypass explicitly prohibited and automated approval explicitly disallowed;
- a **model-use record** (`model_use_record.yaml`) stating the current execution mode, model-use status, and which capabilities remain prohibited until a future review;
- a **policy enforcer** (`policy_enforcer.py`) that evaluates a `(component, resource, action)` triple against the above and returns `ALLOW`, `DENY`, or `REQUIRE_HUMAN_APPROVAL`, never executing the action itself;
- a **startup validator** (`startup_validator.py`) that refuses to construct a runtime unless every configured safety invariant holds.

Every governance configuration document is validated against a JSON Schema before use. Fixtures exist for both valid and deliberately invalid configurations, and an acceptance test suite (`test_governance_phase2_acceptance.py`) exercises the fail-closed behavior directly.

This layer sits ahead of, and is a precondition for, the Sequential Supervisor in ADR-0001: any future supervisor or specialist component must be registered in the agent registry and evaluated through the policy enforcer before it may act, and any human-review routing described in ADR-0001's "Human oversight" section is enforced through the human-approval rules defined here rather than left as prose.

## Rationale

1. A fail-closed default (`DENY` unless explicitly `ALLOW`ed) means an unregistered or misconfigured future component cannot silently act.
2. Making human-approval requirements data-driven and enforced, rather than descriptive text in an ADR, closes the gap between what ADR-0001 says must happen and what the system will actually permit.
3. A separate governance layer, built and tested before any supervisor or model integration exists, allows the enforcement mechanism itself to be validated in isolation.
4. Recording model-use status explicitly, with a defined review trigger, prevents model integration from being introduced implicitly or incrementally without a documented review.
5. This ordering — enforcement layer before orchestration layer — reduces the risk that a supervisor is built first and governance retrofitted around it.

## Alternatives considered

### Build the supervisor and governance together

Rejected because it would make it harder to test and audit the enforcement logic independently of orchestration logic, and would risk the enforcement layer being shaped around whatever the supervisor happens to need rather than around explicit safety invariants.

### Enforce governance policy only through code review and process, without a runtime enforcer

Rejected because process-only enforcement is not fail-closed: a future change could grant a component broader access without any automatic check, and there would be no automated regression coverage for a permission regression.

### Allow-by-default permission matrix

Rejected because it would require every future prohibited action to be anticipated and explicitly listed, rather than requiring every future permitted action to be explicitly justified.

### Permit automated or self-approval for low-risk actions

Rejected for MVP_1. All human-approval rules in this phase require a non-automated, non-self approval, since no basis yet exists for classifying any governed action as low-risk.

## Consequences

### Positive

- Any future supervisor, specialist agent, or model integration must pass through an explicit, tested, fail-closed permission check before it can act.
- Human-review requirements from ADR-0001 are now enforceable, not just descriptive.
- Model-use status is explicit, versioned, and reviewable, rather than implicit in what code happens to be deployed.
- The enforcement layer has its own acceptance test suite, independent of any future supervisor tests.

### Trade-offs

- Every new component or action added in future phases requires a corresponding registry entry, permission entry, and (where applicable) approval rule before it can function — this is deliberate friction.
- The governance layer does not yet enforce the read-only and write boundaries described in ADR-0001 (e.g. protection of `04_Context/`, `05_Leadership/`, `Evidence_Repository/`) at the file-system level; those remain enforced by convention and manual review in this phase.

### Known implementation gap

The agent registry currently declares two enabled, deterministic-only components — `governance.audit_logger.AuditLogger` and `governance.schema_validator.SchemaValidator` — for which no implementation module exists in the Phase 2 codebase, and which no test currently exercises. This does not violate the fail-closed behavior of the policy enforcer or startup validator (neither is invoked by name at runtime), but it does mean the registry is not yet a fully accurate description of implemented components. This should be resolved in Phase 3, either by implementation or by correcting the registry to reflect `enabled: false` until built.

## Future evolution

Phase 3 and later phases must, before any supervisor or specialist-agent code is introduced:

- resolve the audit-logger and schema-validator registry gap noted above;
- register the eventual Sequential Supervisor and each specialist component in the agent registry with explicit, minimal allowed actions;
- extend the permission matrix and human-approval rules to cover supervisor and specialist-component actions rather than governance-configuration actions alone;
- decide whether file-system-level enforcement of the ADR-0001 read-only and write boundaries is added to this layer, or remains a separate control.

That evolution must be documented through separate architecture decision records or explicit amendments, consistent with the practice established here.
