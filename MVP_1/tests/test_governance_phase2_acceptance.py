"""End-to-end acceptance tests for Phase 2 governance controls."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from governance.config_loader import GovernanceConfiguration
from governance.policy_enforcer import (
    PolicyDecisionType,
    PolicyEnforcer,
)
from governance.startup_validator import initialize_governance


MVP_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_ROOT = MVP_ROOT / "governance"


def copy_configuration(
    configuration: GovernanceConfiguration,
) -> GovernanceConfiguration:
    return GovernanceConfiguration(
        agent_registry=deepcopy(configuration.agent_registry),
        permission_matrix=deepcopy(configuration.permission_matrix),
        human_approval_rules=deepcopy(
            configuration.human_approval_rules
        ),
        model_use_record=deepcopy(configuration.model_use_record),
    )


def test_phase_2_runtime_starts_in_deterministic_only_mode() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    assert runtime.ready is True
    assert runtime.execution_mode == "DETERMINISTIC_ONLY"
    assert runtime.model_use_status == "NOT_IN_USE"


def test_phase_2_allows_only_explicitly_permitted_action() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    decision = runtime.policy_enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.ALLOW
    assert decision.permitted is True


def test_phase_2_denies_unregistered_component() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    decision = runtime.policy_enforcer.evaluate(
        component_id="governance.unregistered_component",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False


def test_phase_2_denies_external_model_action() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    decision = runtime.policy_enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="CALL_EXTERNAL_MODEL",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False


def test_phase_2_denies_unknown_action_by_default() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)

    decision = runtime.policy_enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="UNKNOWN_ACTION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False


def test_phase_2_deny_precedence_overrides_allow() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)
    configuration = copy_configuration(runtime.configuration)

    permission = next(
        item
        for item in configuration.permission_matrix["permissions"]
        if item["component_id"] == "governance.policy_enforcer"
    )

    permission["denied_actions"].append("CHECK_ACTION_PERMISSION")

    decision = PolicyEnforcer(configuration).evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False


def test_phase_2_governed_action_requires_human_approval() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)
    configuration = copy_configuration(runtime.configuration)

    component = next(
        item
        for item in configuration.agent_registry["components"]
        if item["component_id"] == "governance.policy_enforcer"
    )

    permission = next(
        item
        for item in configuration.permission_matrix["permissions"]
        if item["component_id"] == "governance.policy_enforcer"
    )

    component["allowed_actions"].append("ACCEPT_ASSESSMENT_FINDING")
    permission["allowed_actions"].append("ACCEPT_ASSESSMENT_FINDING")

    decision = PolicyEnforcer(configuration).evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="ACCEPT_ASSESSMENT_FINDING",
    )

    assert (
        decision.decision
        is PolicyDecisionType.REQUIRE_HUMAN_APPROVAL
    )
    assert decision.permitted is False
    assert decision.approval_rule_id == "HAR-001"


def test_phase_2_runtime_has_no_model_enablement() -> None:
    runtime = initialize_governance(GOVERNANCE_ROOT)
    model_record = runtime.configuration.model_use_record

    assert model_record["model_use_status"] == "NOT_IN_USE"
    assert model_record["external_model_calls_allowed"] is False
    assert model_record["generative_model_calls_allowed"] is False

    prohibited = set(model_record["prohibited_capabilities"])

    assert "EXTERNAL_MODEL_INVOCATION" in prohibited
    assert "GENERATIVE_TEXT_CREATION" in prohibited
    assert "SUPERVISOR_ORCHESTRATION" in prohibited
    assert "REPORT_GENERATION" in prohibited
