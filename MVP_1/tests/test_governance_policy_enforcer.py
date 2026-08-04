"""Tests for deterministic and fail-closed policy enforcement."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from governance.config_loader import (
    ConfigurationLoader,
    GovernanceConfiguration,
)
from governance.policy_enforcer import (
    PolicyDecisionType,
    PolicyEnforcer,
)


MVP_ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_ROOT = MVP_ROOT / "governance"


def load_configuration() -> GovernanceConfiguration:
    return ConfigurationLoader(GOVERNANCE_ROOT).load()


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


def test_explicitly_allowed_action_is_allowed() -> None:
    enforcer = PolicyEnforcer(load_configuration())

    decision = enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.ALLOW
    assert decision.permitted is True


def test_registry_prohibited_action_is_denied() -> None:
    enforcer = PolicyEnforcer(load_configuration())

    decision = enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="CALL_EXTERNAL_MODEL",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False
    assert "prohibited" in decision.reason.lower()


def test_unregistered_component_is_denied() -> None:
    enforcer = PolicyEnforcer(load_configuration())

    decision = enforcer.evaluate(
        component_id="governance.unknown_component",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert "not registered" in decision.reason.lower()


def test_unknown_resource_is_denied() -> None:
    enforcer = PolicyEnforcer(load_configuration())

    decision = enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="UNKNOWN_RESOURCE",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert "no permission entry" in decision.reason.lower()


def test_unknown_action_is_denied_by_default() -> None:
    enforcer = PolicyEnforcer(load_configuration())

    decision = enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="UNREGISTERED_ACTION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert "default decision" in decision.reason.lower()


def test_disabled_component_is_denied() -> None:
    configuration = copy_configuration(load_configuration())

    component = next(
        item
        for item in configuration.agent_registry["components"]
        if item["component_id"] == "governance.policy_enforcer"
    )
    component["enabled"] = False

    enforcer = PolicyEnforcer(configuration)

    decision = enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert "disabled" in decision.reason.lower()


def test_explicit_deny_takes_precedence_over_allow() -> None:
    configuration = copy_configuration(load_configuration())

    permission = next(
        item
        for item in configuration.permission_matrix["permissions"]
        if item["component_id"] == "governance.policy_enforcer"
    )

    permission["denied_actions"].append("CHECK_ACTION_PERMISSION")

    enforcer = PolicyEnforcer(configuration)

    decision = enforcer.evaluate(
        component_id="governance.policy_enforcer",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert "explicitly denied" in decision.reason.lower()


def test_governed_action_requires_human_approval() -> None:
    configuration = copy_configuration(load_configuration())

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

    enforcer = PolicyEnforcer(configuration)

    decision = enforcer.evaluate(
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


def test_blank_identifiers_are_denied() -> None:
    enforcer = PolicyEnforcer(load_configuration())

    decision = enforcer.evaluate(
        component_id="",
        resource="GOVERNANCE_POLICY",
        action="CHECK_ACTION_PERMISSION",
    )

    assert decision.decision is PolicyDecisionType.DENY
    assert decision.permitted is False
