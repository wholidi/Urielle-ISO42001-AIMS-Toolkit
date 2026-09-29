"""ISO/IEC 42001 Clause 05 deterministic assessment layer (Release 0.2 P04)."""

from .adapter import (
    build_evidence_mappings,
    evaluate_clause05_question,
    source_evidence_id,
)
from .aggregation import Clause05RequirementResult, aggregate_requirement
from .config import load_evidence_map, load_question_bank
from .validation import Clause05ConfigError, validate_clause05_configuration

__all__ = [
    "Clause05ConfigError",
    "Clause05RequirementResult",
    "aggregate_requirement",
    "build_evidence_mappings",
    "evaluate_clause05_question",
    "load_evidence_map",
    "load_question_bank",
    "source_evidence_id",
    "validate_clause05_configuration",
]
