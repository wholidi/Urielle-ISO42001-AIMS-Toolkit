"""Deterministic, fail-closed governance policy enforcement."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from governance.config_loader import GovernanceConfiguration


class PolicyDecisionType(str, Enum):
    """Possible deterministic policy outcomes."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"


@dataclass(frozen=True)
class PolicyDecision:
    """Immutable result of a deterministic permission evaluation."""

    component_id: str
    resource: str
    action: str
    decision: PolicyDecisionType
    reason: str
    approval_rule_id: str | None = None

    @property
    def permitted(self) -> bool:
        """Return true only for an explicit ALLOW decision."""

        return self.decision is PolicyDecisionType.ALLOW


class PolicyEnforcer:
    """Evaluate governance actions without executing them."""

    def __init__(self, configuration: GovernanceConfiguration) -> None:
        self.configuration = configuration

        self._components = {
            component["component_id"]: component
            for component in configuration.agent_registry["components"]
        }

        self._permissions = {
            (
                permission["component_id"],
                permission["resource"],
            ): permission
            for permission in configuration.permission_matrix["permissions"]
        }

        self._approval_rules = {
            rule["action"]: rule
            for rule in configuration.human_approval_rules["rules"]
        }

    def evaluate(
        self,
        *,
        component_id: str,
        resource: str,
        action: str,
    ) -> PolicyDecision:
        """Return a deterministic, fail-closed policy decision."""

        if not self._is_valid_identifier(component_id):
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Component identifier is missing or invalid.",
            )

        if not self._is_valid_identifier(resource):
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Resource identifier is missing or invalid.",
            )

        if not self._is_valid_identifier(action):
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Action identifier is missing or invalid.",
            )

        component = self._components.get(component_id)

        if component is None:
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Component is not registered.",
            )

        if component["enabled"] is not True:
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Component is registered but disabled.",
            )

        if component["execution_mode"] != "DETERMINISTIC_ONLY":
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Component execution mode is not deterministic-only.",
            )

        component_prohibited = set(component["prohibited_actions"])

        if action in component_prohibited:
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Action is prohibited by the component registry.",
            )

        permission = self._permissions.get((component_id, resource))

        if permission is None:
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="No permission entry exists for this component and resource.",
            )

        denied_actions = set(permission["denied_actions"])
        allowed_actions = set(permission["allowed_actions"])
        approval_actions = set(permission["human_approval_actions"])

        # Explicit deny always wins, including malformed overlapping policy data.
        if action in denied_actions:
            return self._deny(
                component_id=component_id,
                resource=resource,
                action=action,
                reason="Action is explicitly denied by the permission matrix.",
            )

        approval_rule = self._approval_rules.get(action)

        if action in approval_actions or approval_rule is not None:
            rule_id = (
                approval_rule["rule_id"]
                if approval_rule is not None
                else None
            )

            return PolicyDecision(
                component_id=component_id,
                resource=resource,
                action=action,
                decision=PolicyDecisionType.REQUIRE_HUMAN_APPROVAL,
                reason="Action requires explicit human approval.",
                approval_rule_id=rule_id,
            )

        if action in allowed_actions:
            return PolicyDecision(
                component_id=component_id,
                resource=resource,
                action=action,
                decision=PolicyDecisionType.ALLOW,
                reason="Action is explicitly allowed.",
            )

        return self._deny(
            component_id=component_id,
            resource=resource,
            action=action,
            reason="Action is not explicitly allowed; default decision is DENY.",
        )

    @staticmethod
    def _is_valid_identifier(value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())

    @staticmethod
    def _deny(
        *,
        component_id: str,
        resource: str,
        action: str,
        reason: str,
    ) -> PolicyDecision:
        return PolicyDecision(
            component_id=component_id,
            resource=resource,
            action=action,
            decision=PolicyDecisionType.DENY,
            reason=reason,
        )
