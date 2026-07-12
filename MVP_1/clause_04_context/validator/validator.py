import re


NEGATION_PATTERNS = [
    r"\bnot documented\b",
    r"\bnot defined\b",
    r"\bnot available\b",
    r"\bnot identified\b",
    r"\bnot established\b",
    r"\bnot implemented\b",
    r"\bmissing\b",
    r"\bincomplete\b",
    r"\bno evidence\b",
    r"\bno response\b",
    r"\bnot yet\b",
    r"\bto be defined\b",
    r"\btbd\b"
]


EVIDENCE_PATTERNS = [
    r"\bevidence is stored in\b",
    r"\bevidence is available in\b",
    r"\bdocumented in\b",
    r"\bregister\b",
    r"\bpolicy\b",
    r"\bstatement\b",
    r"\bprocess map\b",
    r"\bprocedure\b",
    r"\brecord\b"
]


OWNER_PATTERNS = [
    r"\bowner:\s*[a-z0-9 ,._/-]+",
    r"\bresponsible:\s*[a-z0-9 ,._/-]+",
    r"\bowned by\b",
    r"\baccountable\b"
]


DATE_PATTERNS = [
    r"\bdate:\s*\d{4}-\d{2}-\d{2}\b",
    r"\b\d{4}-\d{2}-\d{2}\b"
]


CLAUSE_KEYWORDS = {
    "4.1": [
        r"\bcontext\b",
        r"\binternal\b",
        r"\bexternal\b",
        r"\bissues?\b",
        r"\borganization\b"
    ],
    "4.2": [
        r"\binterested parties\b",
        r"\bstakeholders?\b",
        r"\bregulators?\b",
        r"\bcustomers?\b",
        r"\brequirements?\b"
    ],
    "4.3": [
        r"\bscope\b",
        r"\bboundar(y|ies)\b",
        r"\bincluded\b",
        r"\bexcluded\b",
        r"\bai system\b"
    ],
    "4.4": [
        r"\baims\b",
        r"\bai management system\b",
        r"\bprocess(es)?\b",
        r"\binteractions?\b",
        r"\bcontinual improvement\b"
    ]
}


def contains_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def count_clause_matches(text: str, clause: str) -> int:
    patterns = CLAUSE_KEYWORDS.get(clause, [])
    return sum(1 for pattern in patterns if re.search(pattern, text))


def has_negation_or_gap_language(text: str) -> bool:
    return contains_pattern(text, NEGATION_PATTERNS)


def score_response(response_text: str, clause: str = "") -> float:
    text = response_text.strip().lower()

    if not text:
        return 0.0

    if has_negation_or_gap_language(text):
        return 0.4

    score = 0.0

    # Basic substance: response must be more than a vague sentence
    if len(text.split()) >= 20:
        score += 0.2

    # Evidence reference
    if contains_pattern(text, EVIDENCE_PATTERNS):
        score += 0.25

    # Owner/accountability reference
    if contains_pattern(text, OWNER_PATTERNS):
        score += 0.2

    # Date or review timestamp
    if contains_pattern(text, DATE_PATTERNS):
        score += 0.15

    # Clause-specific relevance
    clause_match_count = count_clause_matches(text, clause)

    if clause_match_count >= 2:
        score += 0.2
    elif clause_match_count == 1:
        score += 0.1

    return min(round(score, 2), 1.0)


def requires_auditor_review(score: float) -> bool:
    return score < 0.75