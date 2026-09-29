"""Read-only loading of Clause 05 deterministic configuration."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent

def _load(name: str) -> dict[str, Any]:
    path = _ROOT / name
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object.")
    return value

def load_question_bank() -> dict[str, Any]:
    return deepcopy(_load("questions.json"))

def load_evidence_map() -> dict[str, Any]:
    return deepcopy(_load("evidence_map.json"))
