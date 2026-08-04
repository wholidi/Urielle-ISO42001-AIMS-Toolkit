"""Fail-closed startup validation for deterministic governance controls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from governance.config_loader import (
    ConfigurationLoader,
    GovernanceConfiguration,
    GovernanceConfigurationError,
)
from governance.policy_enforcer import PolicyEnforcer


class GovernanceStartupError(RuntimeError):
    """Raised when governance controls cannot start safely."""


@dataclass(frozen=True)
class GovernanceRuntime:
    """Validated deterministic governance runtime context."""

    configuration: GovernanceConfiguration
    policy_enforcer: PolicyEnforcer
    ready: bool = True
    execution_mode: str = "DETERMINISTIC_ONLY"
    model_use_status: str = "NOT_IN_USE"


def initialize_governance(
    governance_root: Path | str | None = None,
) -> GovernanceRuntime:
    """Validate configuration and construct a fail-closed runtime context."""

    try:
        configuration = ConfigurationLoader(governance_root).load()
    except GovernanceConfigurationError as exc:
        raise GovernanceStartupError(
            "Governance startup validation failed."
        ) from exc

    _validate_startup_constraints(configuration)

    return GovernanceRuntime(
        configuration=configuration,
        policy_enforcer=PolicyEnforcer(configuration),
    )


def _validate_startup_constraints(
    configuration: GovernanceConfiguration,
) -> None:
    registry = configuration.agent_registry
    matrix = configuration.permission_matrix
    approvals = configuration.human_approval_rules
    model_record = configuration.model_use_record

    if registry["default_execution_mode"] != "DETERMINISTIC_ONLY":
        raise GovernanceStartupError(
            "Startup requires deterministic-only execution."
        )

    for component in registry["components"]:
        if (
            component["enabled"] is True
            and component["execution_mode"] != "DETERMINISTIC_ONLY"
        ):
            raise GovernanceStartupError(
                f"Enabled component is not deterministic-only: "
                f"{component['component_id']}"
            )

    if matrix["default_decision"] != "DENY":
        raise GovernanceStartupError(
            "Startup requires default-deny permission behavior."
        )

    if matrix["deny_precedence"] is not True:
        raise GovernanceStartupError(
            "Startup requires deny precedence."
        )

    if matrix["unregistered_component_decision"] != "DENY":
        raise GovernanceStartupError(
            "Startup requires denial of unregistered components."
        )

    if approvals["default_decision"] != "REQUIRE_HUMAN_APPROVAL":
        raise GovernanceStartupError(
            "Startup requires human approval by default."
        )

    if approvals["self_approval_prohibited"] is not True:
        raise GovernanceStartupError(
            "Startup requires self-approval prohibition."
        )

    if approvals["approval_bypass_prohibited"] is not True:
        raise GovernanceStartupError(
            "Startup requires approval-bypass prohibition."
        )

    for rule in approvals["rules"]:
        if rule["approval_required"] is not True:
            raise GovernanceStartupError(
                f"Approval is not mandatory for rule: "
                f"{rule['rule_id']}"
            )

        if rule["automated_approval_allowed"] is not False:
            raise GovernanceStartupError(
                f"Automated approval is prohibited for rule: "
                f"{rule['rule_id']}"
            )

    if model_record["execution_mode"] != "DETERMINISTIC_ONLY":
        raise GovernanceStartupError(
            "Model-use record is not deterministic-only."
        )

    if model_record["model_use_status"] != "NOT_IN_USE":
        raise GovernanceStartupError(
            "Model use must remain NOT_IN_USE."
        )

    if model_record["external_model_calls_allowed"] is not False:
        raise GovernanceStartupError(
            "External model calls must remain disabled."
        )

    if model_record["generative_model_calls_allowed"] is not False:
        raise GovernanceStartupError(
            "Generative model calls must remain disabled."
        )
