"""Fail-closed structural and relationship validation for Clause 05 configuration."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Mapping

QUESTION_ID = re.compile(r"^Q-C05-(5\.[123])-\d{3}$")
MAPPING_ID = re.compile(r"^C05MAP-(5\.[123])-\d{3}-[A-Z]$")
ARTIFACT_ID = re.compile(r"^S5-\d{2}$")
APPROVED_ARTIFACT_IDS = frozenset(f"S5-{index:02d}" for index in range(1, 16))
ALLOWED_CLAUSES = {"5.1", "5.2", "5.3"}
ALLOWED_ROLES = {"PRIMARY", "CORROBORATING", "CONDITIONAL"}
ALLOWED_RULES = {"ALL_OF", "ANY_OF", "CONDITIONAL"}
ALLOWED_APPLICABILITY = {"APPLICABLE", "CONDITIONAL"}


class Clause05ConfigError(RuntimeError):
    pass


def _require_object(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise Clause05ConfigError(f"{name} must be an object.")
    return value


def validate_clause05_configuration(
    question_bank: Any,
    evidence_map: Any,
) -> None:
    qb = _require_object(question_bank, "question bank")
    em = _require_object(evidence_map, "evidence map")
    if qb.get("schema_version") != "1.0.0" or em.get("schema_version") != "1.0.0":
        raise Clause05ConfigError("Unsupported Clause 05 configuration version.")
    if qb.get("clause") != "5" or em.get("clause") != "5":
        raise Clause05ConfigError("Configuration must be scoped to Clause 05.")

    questions = qb.get("questions")
    mappings = em.get("mappings")
    catalog = em.get("artifact_catalog")
    if not isinstance(questions, list) or not questions:
        raise Clause05ConfigError("Question bank must contain questions.")
    if not isinstance(mappings, list) or not mappings:
        raise Clause05ConfigError("Evidence map must contain mappings.")
    if not isinstance(catalog, list) or not catalog:
        raise Clause05ConfigError("Evidence map must contain an artifact catalog.")

    question_ids = [q.get("question_id") for q in questions if isinstance(q, Mapping)]
    duplicates = [qid for qid, count in Counter(question_ids).items() if count > 1]
    if duplicates:
        raise Clause05ConfigError(f"Duplicate question_id is prohibited: {duplicates[0]}")

    index: dict[str, Mapping[str, Any]] = {}
    for question in questions:
        q = _require_object(question, "question")
        qid = q.get("question_id")
        clause = q.get("clause_ref")
        if not isinstance(qid, str) or QUESTION_ID.fullmatch(qid) is None:
            raise Clause05ConfigError("Invalid Clause 05 question_id.")
        if clause not in ALLOWED_CLAUSES or q.get("requirement_ref") != clause:
            raise Clause05ConfigError("Question requirement_ref must match Clause 05 subclause.")
        if f"Q-C05-{clause}-" not in qid:
            raise Clause05ConfigError("Question identity does not match its clause.")
        if not isinstance(q.get("question_text"), str) or not q["question_text"].strip():
            raise Clause05ConfigError("Question text is required.")
        if q.get("mandatory") is not True:
            raise Clause05ConfigError("Release 0.2 Clause 05 questions must be mandatory.")
        if q.get("human_acceptance_required") is not True:
            raise Clause05ConfigError("Human acceptance cannot be disabled.")
        if q.get("applicability") not in ALLOWED_APPLICABILITY:
            raise Clause05ConfigError("Invalid applicability mode.")
        index[qid] = q

    if len(index) != 21:
        raise Clause05ConfigError("Release 0.2 question bank must contain 21 atomic questions.")
    clause_counts = Counter(q["clause_ref"] for q in questions)
    if clause_counts != Counter({"5.1": 6, "5.2": 8, "5.3": 7}):
        raise Clause05ConfigError("Question-bank clause distribution is invalid.")

    if len(catalog) != len(set(catalog)):
        raise Clause05ConfigError("Duplicate artifact catalog entry is prohibited.")
    catalog_set = set(catalog)
    if any(not isinstance(e, str) or ARTIFACT_ID.fullmatch(e) is None for e in catalog):
        raise Clause05ConfigError("Invalid Clause 05 artifact identity.")
    if catalog_set != APPROVED_ARTIFACT_IDS:
        raise Clause05ConfigError(
            "Artifact catalog must exactly match the approved S5-01 through S5-15 inventory."
        )

    mapping_ids: set[str] = set()
    mapping_pairs: set[tuple[str, str]] = set()
    mapped_questions: set[str] = set()
    rules_by_question: dict[str, set[str]] = {}
    for mapping in mappings:
        m = _require_object(mapping, "mapping")
        mid = m.get("mapping_id")
        qid = m.get("question_id")
        evidence_id = m.get("evidence_id")
        if not isinstance(mid, str) or MAPPING_ID.fullmatch(mid) is None:
            raise Clause05ConfigError("Invalid Clause 05 mapping_id.")
        if mid in mapping_ids:
            raise Clause05ConfigError(f"Duplicate mapping_id is prohibited: {mid}")
        mapping_ids.add(mid)
        if qid not in index:
            raise Clause05ConfigError("Mapping references an unknown question.")
        question = index[qid]
        expected_mapping_prefix = f"C05MAP-{question['clause_ref']}-{qid.rsplit('-', 1)[-1]}-"
        if not mid.startswith(expected_mapping_prefix):
            raise Clause05ConfigError(
                "Mapping identity does not match its question identity."
            )
        if m.get("clause_ref") != question["clause_ref"]:
            raise Clause05ConfigError("Mapping clause does not match its question.")
        if evidence_id not in catalog_set:
            raise Clause05ConfigError("Mapping references an unknown source artifact.")
        pair = (qid, evidence_id)
        if pair in mapping_pairs:
            raise Clause05ConfigError("Duplicate question/evidence mapping is prohibited.")
        mapping_pairs.add(pair)
        if m.get("evidence_role") not in ALLOWED_ROLES:
            raise Clause05ConfigError("Invalid evidence role.")
        rule = m.get("combination_rule")
        if rule not in ALLOWED_RULES:
            raise Clause05ConfigError("Invalid combination rule.")
        rules_by_question.setdefault(qid, set()).add(rule)
        if m.get("human_acceptance_required") is not True:
            raise Clause05ConfigError("Evidence mapping cannot bypass human acceptance.")
        if not isinstance(m.get("claim_supported"), str) or not m["claim_supported"].strip():
            raise Clause05ConfigError("Mapping claim_supported is required.")
        if rule == "CONDITIONAL" and not m.get("applicability_condition"):
            raise Clause05ConfigError("Conditional mapping requires an applicability condition.")
        mapped_questions.add(qid)

    missing = sorted(set(index) - mapped_questions)
    if missing:
        raise Clause05ConfigError(f"Question has no evidence mapping: {missing[0]}")

    for qid, rules in rules_by_question.items():
        if len(rules) != 1:
            raise Clause05ConfigError(
                "All evidence mappings for one atomic question must use one combination rule."
            )
        rule = next(iter(rules))
        applicability = index[qid]["applicability"]
        if rule == "CONDITIONAL" and applicability != "CONDITIONAL":
            raise Clause05ConfigError(
                "CONDITIONAL evidence rules require a conditional question."
            )
        if applicability == "CONDITIONAL" and rule != "CONDITIONAL":
            raise Clause05ConfigError(
                "Conditional questions must use the CONDITIONAL evidence rule."
            )

    commitment_sources = {
        m["evidence_id"] for m in mappings if m["question_id"].startswith("Q-C05-5.1-")
    }
    if commitment_sources == {"S5-01"}:
        raise Clause05ConfigError("S5-01 alone cannot support Clause 5.1.")

    approval = [m for m in mappings if m["question_id"] == "Q-C05-5.2-003"]
    if {m["evidence_id"] for m in approval} != {"S5-01", "S5-06"}:
        raise Clause05ConfigError("Policy approval must map S5-01 and S5-06.")

    resource_decision = [
        m for m in mappings if m["question_id"] == "Q-C05-5.1-004"
    ]
    if {m["evidence_id"] for m in resource_decision} != {"S5-05", "S5-15"}:
        raise Clause05ConfigError(
            "Resource decisions require explicit S5-05 and S5-15 mappings."
        )
    resource_by_source = {
        mapping["evidence_id"]: mapping for mapping in resource_decision
    }
    corroborating_resource = resource_by_source["S5-05"]
    authoritative_resource = resource_by_source["S5-15"]
    if (
        corroborating_resource["evidence_role"] != "CORROBORATING"
        or authoritative_resource["evidence_role"] != "PRIMARY"
        or any(
            mapping["combination_rule"] != "ALL_OF"
            or mapping["human_acceptance_required"] is not True
            for mapping in resource_decision
        )
    ):
        raise Clause05ConfigError(
            "S5-05 corroboration and primary S5-15 decision evidence must both be "
            "question-specifically human accepted under ALL_OF."
        )
    if (
        "cannot establish" not in corroborating_resource["claim_supported"].lower()
        or "authoritative s5-15" not in corroborating_resource["claim_supported"].lower()
    ):
        raise Clause05ConfigError(
            "S5-05 must remain corroborating and unable to establish resource support alone."
        )
    if (
        "authoritative leadership resource-allocation decision"
        not in authoritative_resource["claim_supported"].lower()
        or "template presence" not in authoritative_resource["claim_supported"].lower()
        or "explicitly accepted for this question"
        not in authoritative_resource["claim_supported"].lower()
    ):
        raise Clause05ConfigError(
            "S5-15 must require completed, claim-specific human-accepted decision content."
        )

    reporting_question = index["Q-C05-5.3-006"]
    if reporting_question["question_text"] != (
        "Is an actual AIMS performance reporting occurrence established?"
    ):
        raise Clause05ConfigError(
            "The reporting question must remain atomic and occurrence-specific."
        )
    reporting = [m for m in mappings if m["question_id"] == "Q-C05-5.3-006"]
    if {m["evidence_id"] for m in reporting} != {"S5-05", "S5-11", "S5-14"}:
        raise Clause05ConfigError(
            "Actual reporting occurrence requires explicit S5-05, S5-11, and S5-14 mappings."
        )
    if any(
        m["evidence_role"] != "PRIMARY"
        or m["combination_rule"] != "ALL_OF"
        or m["human_acceptance_required"] is not True
        for m in reporting
    ):
        raise Clause05ConfigError(
            "Every reporting-occurrence source must be primary, required, and human accepted."
        )
    occurrence = next(m for m in reporting if m["evidence_id"] == "S5-05")
    if (
        "actual reporting occurrence" not in occurrence["claim_supported"].lower()
        or "explicitly accepted for this question" not in occurrence["claim_supported"].lower()
        or "template presence alone" not in occurrence["claim_supported"].lower()
    ):
        raise Clause05ConfigError(
            "S5-05 must be claim-specific occurrence content, not template presence."
        )
    schedule = next(m for m in reporting if m["evidence_id"] == "S5-14")
    if (
        "route/cadence planning" not in schedule["claim_supported"].lower()
        or "does not prove" not in schedule["claim_supported"].lower()
    ):
        raise Clause05ConfigError("Reporting schedule must not imply reporting occurrence.")
    role = next(m for m in reporting if m["evidence_id"] == "S5-11")
    if (
        "assigned reporting role" not in role["claim_supported"].lower()
        or "alone does not prove" not in role["claim_supported"].lower()
    ):
        raise Clause05ConfigError("Reporting role alone must not imply reporting occurrence.")
