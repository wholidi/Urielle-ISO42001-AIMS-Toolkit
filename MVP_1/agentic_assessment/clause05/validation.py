"""Fail-closed structural and relationship validation for Clause 05 configuration."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Mapping

QUESTION_ID = re.compile(r"^Q-C05-(5\.[123])-\d{3}$")
MAPPING_ID = re.compile(r"^C05MAP-(5\.[123])-\d{3}-[A-Z]$")
ARTIFACT_ID = re.compile(r"^S5-\d{2}$")
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

    reporting = [m for m in mappings if m["question_id"] == "Q-C05-5.3-006"]
    if any("actual reporting occurrence" not in m["claim_supported"].lower() for m in reporting):
        raise Clause05ConfigError("Reporting schedule must not imply reporting occurrence.")
