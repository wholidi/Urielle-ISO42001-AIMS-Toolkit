import pytest

from clause_04_context.validator.validator import (
    requires_auditor_review,
    score_response,
)


def test_empty_response_scores_zero():
    assert score_response("", "4.1") == 0.0


def test_whitespace_response_scores_zero():
    assert score_response("     \n\t   ", "4.1") == 0.0


def test_negated_response_is_capped_low():
    response = (
        "The context register is not documented yet. "
        "Evidence is stored in Clause4_Context_Register.xlsx. "
        "Owner: AI Governance Lead. Date: 2026-07-04."
    )

    assert score_response(response, "4.1") == 0.4


def test_missing_evidence_language_is_capped_low():
    response = (
        "The stakeholder register is missing. "
        "Owner: AI Governance Lead. Date: 2026-07-04."
    )

    assert score_response(response, "4.2") == 0.4


def test_short_vague_response_does_not_score_high():
    response = "We have a register."

    assert score_response(response, "4.1") < 0.75


def test_irrelevant_response_does_not_score_high():
    response = (
        "This response is long enough to contain many words, but it talks about "
        "lunch, office chairs, weather, and general administration without giving "
        "proper AI governance evidence."
    )

    assert score_response(response, "4.1") < 0.75


def test_valid_clause_41_response_scores_high():
    response = (
        "The organization has identified internal and external AI governance issues "
        "in the Context Register. Evidence is stored in Clause4_Context_Register.xlsx. "
        "Owner: AI Governance Lead. Date: 2026-07-04."
    )

    assert score_response(response, "4.1") >= 0.75


def test_valid_clause_42_response_scores_high():
    response = (
        "Interested parties have been identified in the Stakeholder Register. "
        "The register includes internal management, AI system owner, users, auditors, "
        "customers, regulators, legal/compliance, IT/security, and affected stakeholders. "
        "Relevant AI-related requirements include transparency, accountability, "
        "risk management, human oversight, data protection, auditability, incident handling, "
        "and regulatory compliance. Evidence is stored in Clause4_Stakeholder_Register.xlsx. "
        "Owner: AI Governance Lead. Date: 2026-07-04."
    )

    assert score_response(response, "4.2") >= 0.75


def test_valid_clause_43_response_scores_high():
    response = (
        "The AIMS scope has been defined in the AIMS Scope Statement. "
        "The scope includes the Urielle AI audit assistant, Clause 4 evidence collection, "
        "human review workflow, and audit report generation. Exclusions include production "
        "deployment, automated certification decisions, and third-party model training. "
        "The AI system boundary and organizational boundary are documented. "
        "Owner: AI Governance Lead. Date: 2026-07-04."
    )

    assert score_response(response, "4.3") >= 0.75


def test_valid_clause_44_response_scores_high():
    response = (
        "The organization has established an initial AI Management System process map. "
        "The AIMS process includes context review, stakeholder requirement review, "
        "scope definition, AI risk identification, evidence collection, human review, "
        "gap detection, reporting, and continual improvement. Process interactions are "
        "documented through the Clause 4 evidence workflow and readiness report generation. "
        "Evidence is stored in Clause4_AIMS_Process_Map.xlsx. "
        "Owner: AI Governance Lead. Date: 2026-07-04."
    )

    assert score_response(response, "4.4") >= 0.75


def test_response_with_markdown_and_line_breaks_scores_correctly():
    response = """
    ## Evidence Summary

    The organization has identified internal and external AI governance issues
    in the Context Register.

    Evidence is stored in Clause4_Context_Register.xlsx.
    Owner: AI Governance Lead.
    Date: 2026-07-04.
    """

    assert score_response(response, "4.1") >= 0.75


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, True),
        (0.74, True),
        (0.75, False),
        (1.0, False),
    ],
)
def test_auditor_review_threshold(score, expected):
    assert requires_auditor_review(score) is expected